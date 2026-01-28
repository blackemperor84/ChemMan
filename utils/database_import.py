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


def import_clp_data(file_stream) -> Tuple[bool, str, int]:
    """
    Imports CLP data from Excel file into database.

    Args:
        file_stream: File object from request.files

    Returns:
        Tuple[bool, str, int]: (success, message, records_count)
    """
    try:
        # Validate first
        is_valid, message, df = validate_clp_excel(file_stream)
        if not is_valid:
            return False, message, 0

        # Column mapping
        column_map = {
            'International Chemical Identification': 'name',
            'CAS No': 'cas',
            'EC No': 'ec_number',
            'Classification': 'classification',
            'Unnamed: 5': 'h_phrases',  # H-phrases column
            'Specific Conc. Limits, M-factors': 'scl_mfactor'
        }

        # Rename columns
        df.rename(columns=column_map, inplace=True)

        # Keep only mapped columns that exist
        columns_to_keep = [v for v in column_map.values() if v in df.columns]

        # Add missing columns as None
        for col in ['name', 'cas', 'ec_number', 'classification', 'h_phrases', 'scl_mfactor']:
            if col not in df.columns:
                df[col] = None
            else:
                columns_to_keep.append(col) if col not in columns_to_keep else None

        df = df[['name', 'cas', 'ec_number', 'classification', 'h_phrases', 'scl_mfactor']]

        # Replace NaN values with None to avoid storing "nan" strings
        df = df.where(pd.notna(df), None)

        # Clear existing data
        current_app.logger.info("Czyszczenie tabeli excel_source_substances...")
        db.session.query(ExcelSourceSubstance).delete()
        db.session.commit()

        # Convert DataFrame to list of dicts and insert
        current_app.logger.info("Importowanie danych CLP do bazy...")
        data_to_insert = df.to_dict(orient='records')

        # Batch insert for better performance
        db.session.bulk_insert_mappings(ExcelSourceSubstance, data_to_insert)
        db.session.commit()

        records_count = len(data_to_insert)
        current_app.logger.info(f"Import CLP zakończony. Dodano {records_count} rekordów.")

        return True, f"Import zakończony pomyślnie. Dodano {records_count} rekordów.", records_count

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error importing CLP data: {e}")
        import traceback
        traceback.print_exc()
        return False, f"Błąd podczas importu: {str(e)}", 0


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

        # Try to map columns intelligently
        column_map = {}

        # First try exact matches (with trailing spaces as in original file)
        exact_mappings = {
            'Nazwa substancji ': 'name',
            'Nr WE': 'ec_number',
            'Nr CAS': 'cas',
            'Powód włączenia ': 'reason',
            'Data włączenia ': 'date_inclusion'
        }

        for original_col, mapped_col in exact_mappings.items():
            if original_col in df.columns:
                column_map[original_col] = mapped_col

        # If exact matches failed, try keyword matching
        if not column_map:
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if 'nazwa' in col_lower or 'name' in col_lower or 'substance' in col_lower:
                    column_map[col] = 'name'
                elif 'cas' in col_lower:
                    column_map[col] = 'cas'
                elif 'ec' in col_lower or 'we' in col_lower:
                    column_map[col] = 'ec_number'
                elif 'powód' in col_lower or 'reason' in col_lower:
                    column_map[col] = 'reason'
                elif 'data' in col_lower or 'date' in col_lower:
                    column_map[col] = 'date_inclusion'

        # Rename columns
        df.rename(columns=column_map, inplace=True)

        # Ensure all required columns exist
        for col in ['name', 'cas', 'ec_number', 'reason', 'date_inclusion']:
            if col not in df.columns:
                df[col] = None

        df = df[['name', 'cas', 'ec_number', 'reason', 'date_inclusion']]

        # Replace NaN values with None to avoid storing "nan" strings
        df = df.where(pd.notna(df), None)

        # Clear existing data
        current_app.logger.info("Czyszczenie tabeli svhc_substances...")
        db.session.query(SVHCSubstance).delete()
        db.session.commit()

        # Convert DataFrame to list of dicts and insert
        current_app.logger.info("Importowanie danych SVHC do bazy...")
        data_to_insert = df.to_dict(orient='records')

        # Batch insert for better performance
        db.session.bulk_insert_mappings(SVHCSubstance, data_to_insert)
        db.session.commit()

        records_count = len(data_to_insert)
        current_app.logger.info(f"Import SVHC zakończony. Dodano {records_count} rekordów.")

        return True, f"Import zakończony pomyślnie. Dodano {records_count} rekordów.", records_count

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error importing SVHC data: {e}")
        import traceback
        traceback.print_exc()
        return False, f"Błąd podczas importu: {str(e)}", 0


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
