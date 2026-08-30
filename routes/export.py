import io
import csv
import re
import urllib.parse
from typing import Tuple

from flask import Blueprint, request, flash, redirect, url_for, Response, jsonify, render_template, current_app
from flask_login import login_required
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from decorators import view_permission_required
from models import db, Location, Substance, ExcelSourceSubstance, SVHCSubstance, SDSFile
from utils import handle_exception, is_svhc_substance, convert_utc_to_local, csv_safe


export_bp = Blueprint('export', __name__)


def _build_substance_query(args) -> Tuple[object, bool]:
    """Buduje zapytanie Substance z filtrami z request.args.

    Zwraca tuplę (query, filters_applied). Query jest już zjoinowane z Location
    i posortowane po Location.name, Substance.name — wywołujący dodaje paginate/all/count.
    """
    filter_query = args.get('filter', '').strip()
    physical_location = args.get('physical_location', '').strip()
    user_location = args.get('user_location', '').strip()
    is_cmr = args.get('is_cmr', '').strip()
    is_svhc_param = args.get('is_svhc', '').strip()
    has_sds = args.get('has_sds', '').strip()

    query = db.session.query(Substance).join(Location)
    filters_applied = False

    if filter_query:
        search_term = f"%{filter_query}%"
        filter_query_lower = filter_query.lower()

        text_filter_condition = or_(
            Location.name.ilike(search_term),
            Substance.name.ilike(search_term),
            Substance.cas.ilike(search_term),
            Substance.ec_number.ilike(search_term),
            Substance.classification.ilike(search_term),
            Substance.h_phrases.ilike(search_term),
            Substance.physical_location.ilike(search_term),
            Substance.comment.ilike(search_term),
        )

        svhc_text_condition = None
        if re.search(r'(^|\W)svhc($|\W)', filter_query_lower) or filter_query_lower == 'svhc':
            svhc_text_condition = or_(
                Substance.is_svhc.is_(True),
                Substance.contains_svhc.is_(True),
            )

        cmr_text_condition = None
        if re.search(r'(^|\W)cmr($|\W)', filter_query_lower):
            cmr_text_condition = or_(
                Substance.is_cmr.is_(True),
                Substance.contains_cmr.is_(True),
            )

        combined_conditions = [c for c in (svhc_text_condition, cmr_text_condition) if c is not None]
        if combined_conditions:
            if filter_query_lower.strip() in ('svhc', 'cmr'):
                query = query.filter(or_(*combined_conditions))
            else:
                query = query.filter(or_(text_filter_condition, *combined_conditions))
        else:
            query = query.filter(text_filter_condition)

        filters_applied = True

    if physical_location:
        query = query.filter(Substance.physical_location == physical_location)
        filters_applied = True

    if user_location:
        query = query.filter(Location.name == user_location)
        filters_applied = True

    if is_cmr:
        if is_cmr.lower() == 'true':
            query = query.filter(or_(
                Substance.is_cmr.is_(True),
                Substance.contains_cmr.is_(True),
            ))
        else:
            query = query.filter(
                Substance.is_cmr.is_(False),
                Substance.contains_cmr.is_(False),
            )
        filters_applied = True

    if is_svhc_param:
        if is_svhc_param.lower() == 'true':
            query = query.filter(or_(
                Substance.is_svhc.is_(True),
                Substance.contains_svhc.is_(True),
            ))
        else:
            query = query.filter(
                Substance.is_svhc.is_(False),
                Substance.contains_svhc.is_(False),
            )
        filters_applied = True

    if has_sds:
        if has_sds.lower() == 'true':
            query = query.filter(Substance.sds_filename.isnot(None))
        else:
            query = query.filter(Substance.sds_filename.is_(None))
        filters_applied = True

    query = query.order_by(Location.name, Substance.name)
    return query, filters_applied


@export_bp.route('/search_substances')
@login_required
@view_permission_required
def search_substances_api():
    """API do wyszukiwania substancji w bazach CLP i SVHC."""
    query_param = request.args.get('query', '').strip()
    results = []

    if len(query_param) >= 2:
        current_app.logger.info(f"Zapytanie API (Baza) o substancję: '{query_param}'")
        search_term = f"%{query_param}%"

        try:
            found_substances = ExcelSourceSubstance.query.filter(
                ExcelSourceSubstance.name.isnot(None),
                or_(
                    ExcelSourceSubstance.name.ilike(search_term),
                    ExcelSourceSubstance.cas.ilike(search_term),
                    ExcelSourceSubstance.ec_number.ilike(search_term),
                ),
            ).limit(50).all()

            for sub in found_substances:
                results.append({
                    'name': sub.name,
                    'cas': sub.cas,
                    'ec_number': sub.ec_number,
                    'classification': sub.classification,
                    'h_phrases': sub.h_phrases,
                    'scl_mfactor': sub.scl_mfactor,
                    'source': 'CLP',
                })

            found_svhc = SVHCSubstance.query.filter(
                SVHCSubstance.name.isnot(None),
                or_(
                    SVHCSubstance.name.ilike(search_term),
                    SVHCSubstance.cas.ilike(search_term),
                    SVHCSubstance.ec_number.ilike(search_term),
                ),
            ).limit(50).all()

            seen_keys = {(r['cas'], r['ec_number'], r['name']) for r in results}
            for sub in found_svhc:
                # Skip rows already present (from CLP) and also intra-SVHC duplicates
                key = (sub.cas or '', sub.ec_number or '', sub.name or '')
                if key in seen_keys:
                    continue
                # Skip legacy CAS-only duplicate detection kept for safety
                if sub.cas and any(r['cas'] == sub.cas and r['name'] == sub.name for r in results):
                    continue
                seen_keys.add(key)
                results.append({
                    'name': sub.name,
                    'cas': sub.cas or '',
                    'ec_number': sub.ec_number or '',
                    'classification': '',
                    'h_phrases': '',
                    'scl_mfactor': '',
                    'source': 'SVHC',
                })

            current_app.logger.info(f"Wyszukiwanie zwróciło {len(results)} wyników (CLP + SVHC).")

        except Exception as e:
            current_app.logger.exception(f"Błąd podczas wyszukiwania: {e}")
            return jsonify([])

    return jsonify(results)


@export_bp.route('/export/location/<int:location_id>/csv')
@login_required
@view_permission_required
def export_location_csv(location_id):
    """Eksportuje substancje dla danej lokalizacji do CSV."""
    try:
        location = Location.query.get_or_404(location_id)
        substances = (
            Substance.query
            .filter_by(location_id=location.id)
            .order_by(Substance.physical_location, Substance.name)
            .all()
        )

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Nazwa chemiczna', 'Nr CAS', 'Klasyfikacja', 'Zwroty H', 'SCL/M-factor', 'Lokalizacja', 'Komentarz'])

        for sub in substances:
            cas_val = sub.cas or ''
            excel_cas = f'="{cas_val}"' if cas_val else ''
            # excel_cas jest budowany przez nas (wymuszenie formatu tekstowego),
            # pozostałe pola pochodzą od użytkownika -> csv_safe
            writer.writerow([
                csv_safe(sub.name),
                excel_cas,
                csv_safe(sub.classification),
                csv_safe(sub.h_phrases),
                csv_safe(sub.scl_mfactor),
                csv_safe(sub.physical_location or 'Nieznana'),
                csv_safe(sub.comment),
            ])

        csv_data = output.getvalue()
        safe_name = "".join(c if c.isalnum() else "_" for c in location.name)
        filename = f"ChemMan_lok_{safe_name}_subst.csv"
        filename_header = "attachment; filename*=UTF-8''{}".format(
            urllib.parse.quote(filename, encoding='utf-8')
        )

        return Response(
            csv_data.encode('utf-8-sig'),
            mimetype='text/csv',
            headers={"Content-Disposition": filename_header},
        )

    except Exception as e:
        return handle_exception(
            e,
            "eksportu CSV lokacji",
            url_for('locations.view_location', location_id=location_id),
        )


@export_bp.route('/export/all/csv')
@login_required
@view_permission_required
def export_all_csv():
    """Eksportuje wszystkie (lub filtrowane) substancje do CSV."""
    try:
        query, filters_applied = _build_substance_query(request.args)
        substances_to_export = query.all()

        if not substances_to_export:
            filters_msg = "pasujących do filtrów" if filters_applied else ""
            flash(f'Brak substancji {filters_msg} do eksportu.', 'warning')
            url_with_params = url_for('export.view_all_substances')
            if request.query_string:
                url_with_params += '?' + request.query_string.decode('utf-8')
            return redirect(url_with_params)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Nazwa chemiczna', 'Nr CAS', 'Nr WE',
            'Klasyfikacja', 'Zwroty H', 'SCL/M-factor',
            'CMR', 'SVHC', 'Komentarz', 'Użytkownik', 'Lokalizacja',
        ])

        for sub in substances_to_export:
            cas_val = sub.cas or ''
            ec_val = sub.ec_number or ''
            excel_cas = f'="{cas_val}"' if cas_val else ''
            excel_ec = f'="{ec_val}"' if ec_val else ''
            writer.writerow([
                csv_safe(sub.name),
                excel_cas,
                excel_ec,
                csv_safe(sub.classification),
                csv_safe(sub.h_phrases),
                csv_safe(sub.scl_mfactor),
                'Tak' if sub.is_cmr else 'Nie',
                'Tak' if sub.is_svhc else 'Nie',
                csv_safe(sub.comment),
                csv_safe(sub.location.name),
                csv_safe(sub.physical_location or 'Nieznana'),
            ])

        csv_data = output.getvalue()
        filename = "ChemMan_substancje_filtrowane.csv" if filters_applied else "ChemMan_wszystkie_substancje.csv"
        filename_header = "attachment; filename*=UTF-8''{}".format(
            urllib.parse.quote(filename, encoding='utf-8')
        )

        return Response(
            csv_data.encode('utf-8-sig'),
            mimetype='text/csv',
            headers={"Content-Disposition": filename_header},
        )

    except Exception as e:
        redirect_url = url_for('export.view_all_substances')
        if request.query_string:
            redirect_url += '?' + request.query_string.decode('utf-8')
        return handle_exception(e, "globalnego eksportu CSV", redirect_url)


@export_bp.route('/substances/all')
@login_required
@view_permission_required
def view_all_substances():
    """Wyświetla stronę ze wszystkimi substancjami, z paginacją po stronie serwera."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', current_app.config['ITEMS_PER_PAGE'], type=int)
        if per_page > 100:
            per_page = 100

        query, filters_applied = _build_substance_query(request.args)
        query = query.options(joinedload(Substance.sds_files))
        paginated_substances = query.paginate(page=page, per_page=per_page, error_out=False)

        locations = Location.query.order_by(Location.name).all()

        all_substances_data_for_template = []
        for sub in paginated_substances.items:
            svhc_reason = None
            if sub.is_svhc:
                svhc_reason = is_svhc_substance(cas=sub.cas, ec_number=sub.ec_number, name=sub.name)

            sds_files_list = []
            for sds_file in sub.sds_files:
                sds_files_list.append({
                    'id': sds_file.id,
                    'filename': sds_file.filename,
                    'original_filename': sds_file.original_filename,
                    'manufacturer': sds_file.manufacturer,
                    'upload_timestamp_local': convert_utc_to_local(sds_file.upload_timestamp),
                })

            all_substances_data_for_template.append({
                'id': sub.id,
                'location_id': sub.location_id,
                'location_name': sub.location.name,
                'name': sub.name,
                'cas': sub.cas,
                'ec_number': sub.ec_number,
                'classification': sub.classification,
                'h_phrases': sub.h_phrases,
                'comment': sub.comment,
                'sds_filename': sub.sds_filename,
                'sds_upload_timestamp_local': convert_utc_to_local(sub.sds_upload_timestamp),
                'sds_files': sds_files_list,
                'scl_mfactor': sub.scl_mfactor or '',
                'physical_location': sub.physical_location or 'Nieznana',
                'is_cmr': sub.is_cmr,
                'is_svhc': sub.is_svhc,
                'contains_cmr': sub.contains_cmr,
                'contains_svhc': sub.contains_svhc,
                'svhc_reason': svhc_reason or '',
            })

        total_substances = Substance.query.count()
        total_sds_files = SDSFile.query.count()

        return render_template(
            'all_substances.html',
            all_substances_data=all_substances_data_for_template,
            locations=locations,
            pagination=paginated_substances,
            filter_query=request.args.get('filter', '').strip(),
            physical_location=request.args.get('physical_location', '').strip(),
            user_location=request.args.get('user_location', '').strip(),
            is_cmr=request.args.get('is_cmr', '').strip(),
            is_svhc=request.args.get('is_svhc', '').strip(),
            has_sds=request.args.get('has_sds', '').strip(),
            total_substances=total_substances,
            total_sds_files=total_sds_files,
        )

    except Exception as e:
        redirect_url = url_for('export.view_all_substances')
        if request.query_string:
            redirect_url += '?' + request.query_string.decode('utf-8')
        return handle_exception(e, "pobierania wszystkich substancji", redirect_url)
