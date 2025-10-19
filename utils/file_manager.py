import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename

class FileManager:
    @staticmethod
    def save_sds_file(file, old_filename=None):
        """
        Zapisuje plik SDS i zwraca jego unikalną nazwę.
        Usuwa stary plik, jeśli został podany.
        
        Parametry:
        - file: Obiekt FileStorage z request.files
        - old_filename: Opcjonalna nazwa starego pliku do usunięcia
        
        Zwraca:
        - str: Unikalna nazwa zapisanego pliku
        """
        # Usuń stary plik, jeśli istnieje
        if old_filename:
            FileManager.delete_sds_file(old_filename)
            
        # Stwórz bezpieczną nazwę pliku + dodaj unikalny prefiks UUID
        original_filename = secure_filename(file.filename)
        # Generujemy unikalną nazwę, aby uniknąć konfliktów i problemów z cache
        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
        
        # Upewnij się, że folder istnieje
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Zapisz plik
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        current_app.logger.info(f"Zapisano plik SDS: {filepath}")
        return unique_filename
    
    @staticmethod
    def delete_sds_file(filename):
        """
        Usuwa plik SDS o podanej nazwie.
        
        Parametry:
        - filename: Nazwa pliku do usunięcia
        
        Zwraca:
        - bool: True jeśli usunięto, False jeśli nie znaleziono
        """
        if not filename:
            return False
            
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            current_app.logger.info(f"Usunięto plik fizycznie: {filepath}")
            return True
        else:
            current_app.logger.warning(f"OSTRZEŻENIE: Plik {filepath} nie został znaleziony na dysku.")
            return False