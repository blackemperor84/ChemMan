"""Tests for batch 4/5 of the security-audit remediation.

Covers:
- CMR detection reading the `classification` field (not just H-phrases)
- SVHC lookup distinguishing "not found" from "could not verify"
- copy route propagating contains_cmr / contains_svhc
- ?next= open-redirect validation
- CSV formula-injection escaping
"""
import csv
import io

import pytest

from utils import (
    SVHC_FOUND,
    SVHC_NOT_FOUND,
    SVHC_UNKNOWN,
    check_svhc_substance,
    csv_safe,
    is_cmr_substance,
    is_safe_redirect_url,
)


class TestCMRClassificationField:
    """A row can carry `Carc. 1B` with empty h_phrases; it must still be CMR."""

    def test_classification_only_carc_1b(self):
        assert is_cmr_substance(None, 'Carc. 1B') is True

    def test_classification_only_muta_1a(self):
        assert is_cmr_substance('', 'Muta. 1A') is True

    def test_classification_only_repr_1b(self):
        assert is_cmr_substance(None, 'Repr. 1B') is True

    def test_classification_without_space(self):
        assert is_cmr_substance(None, 'Carc.1B') is True

    def test_classification_within_longer_string(self):
        assert is_cmr_substance(None, 'Flam. Liq. 2, Carc. 1B, Aquatic Chronic 2') is True

    @pytest.mark.parametrize('classification', [
        'Carc. 2',      # category 2 -> H351, outside the Polish 1A/1B register
        'Muta. 2',
        'Repr. 2',
        'Skin Irrit. 2',
        'Aquatic Chronic 1',
        'Flam. Liq. 1B',  # "1B" but not a CMR hazard class
        'Eye Dam. 1',
    ])
    def test_non_cmr_classifications(self, classification):
        assert is_cmr_substance(None, classification) is False

    def test_h_phrase_still_wins_without_classification(self):
        assert is_cmr_substance('H350', None) is True

    def test_both_empty(self):
        assert is_cmr_substance(None, None) is False

    def test_category_2_h_phrases_unchanged(self):
        """Polish register is 1A/1B only - category 2 stays out. Deliberate."""
        assert is_cmr_substance('H341', None) is False
        assert is_cmr_substance('H351', None) is False
        assert is_cmr_substance('H361', None) is False


class TestSVHCVerificationStatus:
    def test_not_found_is_reported_as_not_found(self, db_session):
        result = check_svhc_substance(cas='0000-00-0')
        assert result.status == SVHC_NOT_FOUND
        assert result.is_svhc is False
        assert result.verified is True

    def test_no_input_is_not_found_not_unknown(self, db_session):
        result = check_svhc_substance()
        assert result.status == SVHC_NOT_FOUND
        assert result.verified is True

    def test_lookup_failure_is_distinguishable(self, db_session, monkeypatch):
        """A DB error must NOT look like 'not on the SVHC list'."""
        import utils

        class Boom:
            @property
            def query(self):
                raise RuntimeError('database is down')

        monkeypatch.setattr(utils, 'SVHCSubstance', Boom())

        result = check_svhc_substance(cas='7439-92-1')

        assert result.status == SVHC_UNKNOWN
        assert result.verified is False
        # Crucially: is_svhc is False, but `verified` tells callers not to trust it.
        assert result.is_svhc is False

    def test_found_carries_reason(self, db_session):
        from models import SVHCSubstance

        db_session.add(SVHCSubstance(
            name='Testowa substancja',
            cas='1234-56-7',
            ec_number='200-000-1',
            reason='Carcinogenic',
        ))
        db_session.commit()

        result = check_svhc_substance(cas='1234-56-7')
        assert result.status == SVHC_FOUND
        assert result.is_svhc is True
        assert result.verified is True
        assert 'Carcinogenic' in result.reason

    def test_legacy_wrapper_still_returns_reason(self, db_session):
        from models import SVHCSubstance
        from utils import is_svhc_substance

        db_session.add(SVHCSubstance(
            name='Legacy', cas='9999-99-9', ec_number='200-999-9',
            reason='Toxic for reproduction',
        ))
        db_session.commit()

        assert is_svhc_substance(cas='9999-99-9') == 'Toxic for reproduction'
        assert is_svhc_substance(cas='0000-00-0') is None


class TestCsvSafe:
    @pytest.mark.parametrize('payload', [
        '=cmd|\' /C calc\'!A0',
        '+1+1',
        '-2+3',
        '@SUM(1:1)',
    ])
    def test_formula_prefixes_are_neutralised(self, payload):
        result = csv_safe(payload)
        assert result.startswith("'")
        assert result[1:] == payload

    def test_tab_and_cr_are_neutralised(self):
        assert csv_safe(chr(9) + '=1').startswith("'")
        assert csv_safe(chr(13) + '=1').startswith("'")

    def test_ordinary_values_untouched(self):
        assert csv_safe('Aceton') == 'Aceton'
        assert csv_safe('H350, H360') == 'H350, H360'
        assert csv_safe(None) == ''
        assert csv_safe(42) == '42'

    def test_escaped_cell_is_inert_when_parsed_back(self):
        output = io.StringIO()
        csv.writer(output).writerow([csv_safe('=1+1')])
        cell = next(csv.reader(io.StringIO(output.getvalue())))[0]
        assert not cell.startswith('=')


class TestSafeRedirect:
    @pytest.mark.parametrize('target', [
        'http://evil.com',
        'https://evil.com/path',
        '//evil.com',
        chr(92) + chr(92) + 'evil.com',
        'javascript:alert(1)',
        '',
        None,
    ])
    def test_external_and_empty_targets_rejected(self, app, target):
        with app.test_request_context('/login'):
            assert is_safe_redirect_url(target) is False

    @pytest.mark.parametrize('target', [
        '/locations',
        '/substance/1',
        '/export/all/csv?foo=bar',
    ])
    def test_relative_targets_allowed(self, app, target):
        with app.test_request_context('/login'):
            assert is_safe_redirect_url(target) is True

    def test_same_host_absolute_allowed(self, app):
        with app.test_request_context('/login', base_url='http://localhost'):
            assert is_safe_redirect_url('http://localhost/locations') is True


class TestCopyPropagatesContainsFlags:
    """The copy route used to drop contains_cmr / contains_svhc silently.

    Those flags mark a *mixture* that contains a CMR/SVHC component; losing them
    on copy understates the hazard of the copied record.
    """

    def test_contains_flags_are_copied(self, client, admin_user, test_location, db_session, app):
        from models import Location, Substance

        source_sub = Substance(
            name='Mieszanina z CMR',
            cas='444-44-4',
            location_id=test_location.id,
            is_cmr=False,
            is_svhc=False,
            contains_cmr=True,
            contains_svhc=True,
        )
        db_session.add(source_sub)
        db_session.commit()

        target = Location(name='Target contains-flags')
        db_session.add(target)
        db_session.commit()

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123',
        })

        response = client.post(
            '/substances/copy',
            json={
                'substance_ids': [source_sub.id],
                'target_location_id': target.id,
            },
        )
        assert response.status_code == 200

        copied = Substance.query.filter_by(
            name='Mieszanina z CMR', location_id=target.id
        ).first()
        assert copied is not None
        assert copied.contains_cmr is True
        assert copied.contains_svhc is True
