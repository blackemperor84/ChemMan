"""
Database Import Service for Chem-Man Application.

Provides functions for validating and importing CLP and SVHC Excel databases
through the web interface.
"""

import os
import io
from typing import Tuple, Dict, List, Optional
from flask import current_app
import pandas as pd

from models import db, ExcelSourceSubstance, SVHCSubstance


# Expected columns for CLP database (substancje_baza.xlsx)
CLP_REQUIRED_COLUMNS = [
    'International Chemical Identification',
    'CAS No',
    'EC No',
]

CLP_OPTIONAL_COLUMNS = [
    'Classification',
    'Labelling',
    'Specific Conc. Limits, M-factors',
    'Notes',
]

# Expected columns for SVHC database (svhc.xlsx) - Polish names
SVHC_COLUMN_KEYWORDS = {
    'name': ['nazwa', 'name', 'substance'],
    'cas': ['cas', 'nr cas'],
    'ec': ['ec', 'we', 'nr we', 'nr ec'],
    'reason': ['powód', 'reason', 'włączenia'],
    'date': ['data', 'date'],
}


def validate_excel_mime_type(file_stream) -> bool:
    """
    Validates that the file is a valid Excel file by checking magic bytes.

    Args:
        file_stream: File object from request.files

    Returns:
        bool: True if valid Excel file, False otherwise
    """
    try:
        # Read first 8 bytes for magic number detection
        file_header = file_stream.read(8)
        file_stream.seek(0)  # Reset stream to beginning

        # XLSX files are ZIP archives, start with PK (0x504B)
        if file_header.startswith(b'PK'):
            return True

        # XLS files (older format) start with D0 CF 11 E0 (Microsoft Compound File)
        if file_header.startswith(b'\xD0\xCF\x11\xE0'):
            return True

        return False

    except Exception as e:
        current_app.logger.error(f"Error validating Excel MIME type: {e}")
        return False


def allowed_excel_file(filename: str) -> bool:
    """
    Check if the filename has an allowed Excel extension.

    Args:
        filename: Name of the uploaded file

    Returns:
        bool: True if extension is allowed
    """
    allowed_extensions = {'xlsx', 'xls'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def validate_clp_excel(file_stream) -> Tuple[bool, str, Optional[pd.DataFrame]]:
    """
    Validates CLP Excel file structure.

    Args:
        file_stream: File object from request.files

    Returns:
        Tuple[bool, str, Optional[DataFrame]]:
            (is_valid, message, dataframe if valid)
    """
    try:
        # Read Excel file
        file_stream.seek(0)
        df = pd.read_excel(file_stream, header=0, skiprows=[1])
        file_stream.seek(0)

        if df.empty:
            return False, "Plik Excel jest pusty.", None

        # Check for required columns
        missing_columns = []
        for col in CLP_REQUIRED_COLUMNS:
            if col not in df.columns:
                missing_columns.append(col)

        if missing_columns:
            return False, f"Brak wymaganych kolumn: {', '.join(missing_columns)}", None

        # Check that we have at least some data
        if len(df) < 1:
            return False, "Plik nie zawiera żadnych rekordów.", None

        return True, f"Walidacja pomyślna. Znaleziono {len(df)} rekordów.", df

    except Exception as e:
        current_app.logger.error(f"Error validating CLP Excel: {e}")
        return False, f"Błąd podczas odczytu pliku Excel: {str(e)}", None


def validate_svhc_excel(file_stream) -> Tuple[bool, str, Optional[pd.DataFrame]]:
    """
    Validates SVHC Excel file structure.

    Args:
        file_stream: File object from request.files

    Returns:
        Tuple[bool, str, Optional[DataFrame]]:
            (is_valid, message, dataframe if valid)
    """
    try:
        # Read Excel file
        file_stream.seek(0)
        df = pd.read_excel(file_stream, header=0)
        file_stream.seek(0)

        if df.empty:
            return False, "Plik Excel jest pusty.", None

        # Try to identify columns by keywords
        found_columns = {'name': False, 'cas': False, 'ec': False}

        for col in df.columns:
            col_lower = str(col).lower().strip()
            for field, keywords in SVHC_COLUMN_KEYWORDS.items():
                if field in found_columns:
                    for keyword in keywords:
                        if keyword in col_lower:
                            found_columns[field] = True
                            break

        # At least name or cas or ec must be present
        if not any([found_columns['name'], found_columns['cas'], found_columns['ec']]):
            return False, "Nie można zidentyfikować podstawowych kolumn (nazwa, CAS lub EC).", None

        # Check that we have at least some data
        if len(df) < 1:
            return False, "Plik nie zawiera żadnych rekordów.", None

        return True, f"Walidacja pomyślna. Znaleziono {len(df)} rekordów.", df

    except Exception as e:
        current_app.logger.error(f"Error validating SVHC Excel: {e}")
        return False, f"Błąd podczas odczytu pliku Excel: {str(e)}", None


_EMPTYISH = {'', 'nan', 'none', 'null', 'na', 'n/a'}


def _is_empty(val) -> bool:
    """True for None, pandas NaN, and 'nan'-ish placeholder strings."""
    if val is None:
        return True
    try:
        # Catches float('nan') and numpy NaN without importing numpy directly
        if val != val:  # NaN is the only value where val != val
            return True
    except Exception:
        pass
    if isinstance(val, str) and val.strip().lower() in _EMPTYISH:
        return True
    return False


def _clean_record(record):
    """Normalise a to_dict record so empty-ish values become real None
    before hitting the DB (avoids storing 'NaN' / 'None' as strings)."""
    for key, val in list(record.items()):
        if _is_empty(val):
            record[key] = None


def _snapshot_existing(model, fields):
    """Snapshot given fields from existing rows, keyed by CAS, EC, and name.

    Returns three dicts (by_cas, by_ec, by_name) each mapping key -> {field: value}
    for fields that hold real (non-empty) values. Used by merge-preserve
    import logic so we don't lose curated data (SCL/M-factors, SVHC
    reason, ...) when the incoming source file has those columns stripped.

    Name is the last-resort key — kept for substances without CAS/EC
    (petroleum fractions, complex mixtures). We only insert into by_name
    if the name isn't already present to avoid ambiguous matches.
    """
    by_cas, by_ec, by_name = {}, {}, {}
    columns = [getattr(model, 'cas'), getattr(model, 'ec_number'), getattr(model, 'name')]
    columns.extend(getattr(model, f) for f in fields)
    ambiguous_names = set()
    for row in db.session.query(*columns).all():
        payload = {f: getattr(row, f) for f in fields if not _is_empty(getattr(row, f))}
        if not payload:
            continue
        if row.cas and not _is_empty(row.cas):
            by_cas.setdefault(row.cas, payload)
        if row.ec_number and not _is_empty(row.ec_number):
            by_ec.setdefault(row.ec_number, payload)
        if row.name and not _is_empty(row.name):
            key = str(row.name).strip()
            if key in by_name:
                # Name collision — mark ambiguous so we skip name-based match
                ambiguous_names.add(key)
            else:
                by_name[key] = payload
    for k in ambiguous_names:
        by_name.pop(k, None)
    return by_cas, by_ec, by_name


def _merge_preserve(record, by_cas, by_ec, by_name, fields):
    """Fill empty fields on incoming record from snapshot. Returns per-field
    count of preserved values (0 or 1). Match priority: CAS > EC > exact name."""
    preserved = {f: 0 for f in fields}
    snapshot = None
    cas, ec, name = record.get('cas'), record.get('ec_number'), record.get('name')
    if cas and cas in by_cas:
        snapshot = by_cas[cas]
    elif ec and ec in by_ec:
        snapshot = by_ec[ec]
    elif name and str(name).strip() in by_name:
        snapshot = by_name[str(name).strip()]
    if not snapshot:
        return preserved
    for f in fields:
        if _is_empty(record.get(f)) and f in snapshot:
            record[f] = snapshot[f]
            preserved[f] = 1
    return preserved


def import_clp_data(file_stream) -> Tuple[bool, str, int]:
    """
    Imports CLP data from Excel file into database with merge-preserve
    semantics: if the incoming file has empty scl_mfactor / h_phrases /
    classification for a substance already in the DB with a non-empty value,
    the existing value is kept. This protects curated data (notably SCL and
    M-factors) when ECHA's newer bulk exports strip those columns.

    Args:
        file_stream: File object from request.files

    Returns:
        Tuple[bool, str, int]: (success, message, records_count)
    """
    try:
        is_valid, message, df = validate_clp_excel(file_stream)
        if not is_valid:
            return False, message, 0

        column_map = {
            'International Chemical Identification': 'name',
            'CAS No': 'cas',
            'EC No': 'ec_number',
            'Classification': 'classification',
            'Unnamed: 5': 'h_phrases',
            'Specific Conc. Limits, M-factors': 'scl_mfactor',
        }
        df.rename(columns=column_map, inplace=True)

        for col in ['name', 'cas', 'ec_number', 'classification', 'h_phrases', 'scl_mfactor']:
            if col not in df.columns:
                df[col] = None

        df = df[['name', 'cas', 'ec_number', 'classification', 'h_phrases', 'scl_mfactor']]
        df = df.where(pd.notna(df), None)

        preserve_fields = ['scl_mfactor', 'h_phrases', 'classification']
        by_cas, by_ec, by_name = _snapshot_existing(ExcelSourceSubstance, preserve_fields)
        current_app.logger.info(
            f"Snapshot przed importem CLP: {len(by_cas)} CAS + {len(by_ec)} EC + {len(by_name)} nazw z danymi do zachowania."
        )

        # Przygotuj komplet danych PRZED dotknięciem bazy - błąd parsowania
        # nie może zostawić transakcji w połowie.
        data_to_insert = df.to_dict(orient='records')
        preserved_totals = {f: 0 for f in preserve_fields}
        for record in data_to_insert:
            _clean_record(record)
            counts = _merge_preserve(record, by_cas, by_ec, by_name, preserve_fields)
            for f, c in counts.items():
                preserved_totals[f] += c

        # Zabezpieczenie: pusty zestaw danych nigdy nie może wyczyścić bazy referencyjnej.
        if not data_to_insert:
            return False, "Plik nie zawiera rekordów do zaimportowania. Baza CLP nie została zmieniona.", 0

        # JEDNA TRANSAKCJA: usunięcie starych rekordów i wstawienie nowych.
        # Bez tego nieudany insert zostawiał pustą tabelę bez możliwości odtworzenia
        # (rollback nie cofał już zatwierdzonego DELETE).
        current_app.logger.info("Podmiana danych CLP (usunięcie + wstawienie w jednej transakcji)...")
        db.session.query(ExcelSourceSubstance).delete()
        db.session.bulk_insert_mappings(ExcelSourceSubstance, data_to_insert)
        db.session.commit()

        records_count = len(data_to_insert)
        preserved_parts = [
            f"{v} × {k}" for k, v in preserved_totals.items() if v
        ]
        preserved_msg = f" Zachowano dane: {', '.join(preserved_parts)}." if preserved_parts else ""
        current_app.logger.info(
            f"Import CLP zakończony. Dodano {records_count} rekordów.{preserved_msg}"
        )

        return (
            True,
            f"Import zakończony pomyślnie. Dodano {records_count} rekordów.{preserved_msg}",
            records_count,
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error importing CLP data: {e}")
        return False, f"Błąd podczas importu CLP: {str(e)}", 0


def import_svhc_data(file_stream) -> Tuple[bool, str, int]:
    """
    Imports SVHC data from Excel file into database.

    Args:
        file_stream: File object from request.files

    Returns:
        Tuple[bool, str, int]: (success, message, records_count)
    """
    try:
        # Validate first
        is_valid, message, df = validate_svhc_excel(file_stream)
        if not is_valid:
            return False, message, 0

        # ECHA's SVHC export has changed column names over time — sometimes
        # with a trailing space, sometimes not, and the date column may be absent.
        # We match by keyword against normalised (stripped, lowercased) headers
        # so both old and new formats work.
        column_map = {}
        mapped_targets = set()

        for col in df.columns:
            col_norm = str(col).lower().strip()
            if 'name' not in mapped_targets and (
                'nazwa' in col_norm or 'name' in col_norm or 'substance' in col_norm
            ):
                column_map[col] = 'name'
                mapped_targets.add('name')
            elif 'cas' not in mapped_targets and 'cas' in col_norm:
                column_map[col] = 'cas'
                mapped_targets.add('cas')
            elif 'ec_number' not in mapped_targets and (
                col_norm in ('nr we', 'nr ec', 'ec no', 'we', 'ec')
                or col_norm.startswith('nr we')
                or col_norm.startswith('nr ec')
                or col_norm.startswith('ec ')
            ):
                column_map[col] = 'ec_number'
                mapped_targets.add('ec_number')
            elif 'reason' not in mapped_targets and (
                'powód' in col_norm or 'powod' in col_norm or 'reason' in col_norm or 'włączenia' in col_norm
            ):
                column_map[col] = 'reason'
                mapped_targets.add('reason')
            elif 'date_inclusion' not in mapped_targets and (
                'data' in col_norm or 'date' in col_norm
            ):
                column_map[col] = 'date_inclusion'
                mapped_targets.add('date_inclusion')

        if 'name' not in mapped_targets:
            return False, "Nie znaleziono kolumny z nazwą substancji w pliku SVHC.", 0

        # Rename columns
        df.rename(columns=column_map, inplace=True)

        # Ensure all required columns exist
        for col in ['name', 'cas', 'ec_number', 'reason', 'date_inclusion']:
            if col not in df.columns:
                df[col] = None

        df = df[['name', 'cas', 'ec_number', 'reason', 'date_inclusion']]
        df = df.where(pd.notna(df), None)

        preserve_fields = ['reason', 'date_inclusion']
        by_cas, by_ec, by_name = _snapshot_existing(SVHCSubstance, preserve_fields)
        current_app.logger.info(
            f"Snapshot przed importem SVHC: {len(by_cas)} CAS + {len(by_ec)} EC + {len(by_name)} nazw z danymi do zachowania."
        )

        # Przygotuj komplet danych PRZED dotknięciem bazy - błąd parsowania
        # nie może zostawić transakcji w połowie.
        data_to_insert = df.to_dict(orient='records')
        preserved_totals = {f: 0 for f in preserve_fields}
        for record in data_to_insert:
            _clean_record(record)
            counts = _merge_preserve(record, by_cas, by_ec, by_name, preserve_fields)
            for f, c in counts.items():
                preserved_totals[f] += c

        # Zabezpieczenie: pusty zestaw danych nigdy nie może wyczyścić bazy referencyjnej.
        if not data_to_insert:
            return False, "Plik nie zawiera rekordów do zaimportowania. Baza SVHC nie została zmieniona.", 0

        # JEDNA TRANSAKCJA: usunięcie starych rekordów i wstawienie nowych.
        # Bez tego nieudany insert zostawiał pustą tabelę bez możliwości odtworzenia
        # (rollback nie cofał już zatwierdzonego DELETE).
        current_app.logger.info("Podmiana danych SVHC (usunięcie + wstawienie w jednej transakcji)...")
        db.session.query(SVHCSubstance).delete()
        db.session.bulk_insert_mappings(SVHCSubstance, data_to_insert)
        db.session.commit()

        records_count = len(data_to_insert)
        preserved_parts = [f"{v} × {k}" for k, v in preserved_totals.items() if v]
        preserved_msg = f" Zachowano dane: {', '.join(preserved_parts)}." if preserved_parts else ""
        current_app.logger.info(
            f"Import SVHC zakończony. Dodano {records_count} rekordów.{preserved_msg}"
        )

        return (
            True,
            f"Import zakończony pomyślnie. Dodano {records_count} rekordów.{preserved_msg}",
            records_count,
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error importing SVHC data: {e}")
        return False, f"Błąd podczas importu SVHC: {str(e)}", 0


def get_database_stats() -> Dict[str, int]:
    """
    Returns current record counts for CLP and SVHC databases.

    Returns:
        Dict with 'clp_count' and 'svhc_count' keys
    """
    try:
        clp_count = db.session.query(ExcelSourceSubstance).count()
        svhc_count = db.session.query(SVHCSubstance).count()

        return {
            'clp_count': clp_count,
            'svhc_count': svhc_count
        }
    except Exception as e:
        current_app.logger.error(f"Error getting database stats: {e}")
        return {
            'clp_count': 0,
            'svhc_count': 0
        }
