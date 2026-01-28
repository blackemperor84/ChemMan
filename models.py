from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# Inicjalizacja obiektów
db = SQLAlchemy()
bcrypt = Bcrypt()

class Location(db.Model):
    """Model komórki organizacyjnej (działu/jednostki organizacyjnej)."""
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacja: Jedna komórka organizacyjna -> wiele substancji
    # cascade="all, delete-orphan" zapewnia usunięcie substancji przy usuwaniu komórki
    substances = db.relationship('Substance', backref='location', lazy=True, cascade="all, delete-orphan")

    # Relacja: Jedna komórka organizacyjna -> wielu użytkowników
    users = db.relationship('User', backref='organizational_unit', lazy=True)

    def update_modification_time(self) -> 'Location':
        """
        Aktualizuje pole last_modified na aktualny czas.

        Returns:
            Location: Zwraca samego siebie dla łańcuchowania metod
        """
        self.last_modified = datetime.utcnow()
        return self

    def __repr__(self) -> str:
        return f'<Location {self.name}>'

class Substance(db.Model):
    """Model substancji chemicznej."""
    __tablename__ = 'substances'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)  # TEXT dla bardzo długich nazw (do 2048 chars)
    cas = db.Column(db.Text, nullable=True)  # TEXT dla list numerów CAS (do 484 chars)
    ec_number = db.Column(db.Text, nullable=True)  # TEXT dla list numerów EC (do 441 chars)
    classification = db.Column(db.Text, nullable=True)
    h_phrases = db.Column(db.Text, nullable=True)
    scl_mfactor = db.Column(db.Text, nullable=True)
    comment = db.Column(db.Text, nullable=True)
    is_cmr = db.Column(db.Boolean, default=False)  # Flaga CMR dla czystej substancji
    is_svhc = db.Column(db.Boolean, default=False)  # Flaga SVHC dla czystej substancji
    contains_cmr = db.Column(db.Boolean, default=False)  # Flaga CMR dla mieszanin (zawiera CMR)
    contains_svhc = db.Column(db.Boolean, default=False)  # Flaga SVHC dla mieszanin (zawiera SVHC)
    sds_filename = db.Column(db.String(255), nullable=True)  # Zachowane dla kompatybilności wstecznej
    sds_upload_timestamp = db.Column(db.DateTime, nullable=True)  # Zachowane dla kompatybilności wstecznej
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    physical_location = db.Column(db.String(50), nullable=True)

    # Relacja: Jedna substancja -> wiele plików SDS
    sds_files = db.relationship('SDSFile', backref='substance', lazy=True, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f'<Substance {self.name} (CAS: {self.cas}) in Loc {self.location_id}>'

class SDSFile(db.Model):
    """Model pliku SDS (Safety Data Sheet)."""
    __tablename__ = 'sds_files'

    id = db.Column(db.Integer, primary_key=True)
    substance_id = db.Column(db.Integer, db.ForeignKey('substances.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)  # Nazwa pliku na dysku (z UUID)
    original_filename = db.Column(db.String(255), nullable=True)  # Oryginalna nazwa pliku
    manufacturer = db.Column(db.String(255), nullable=True)  # Producent/dostawca
    upload_timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f'<SDSFile {self.original_filename} for Substance ID {self.substance_id}>'

class User(db.Model, UserMixin):
    """Model użytkownika systemu z obsługą uwierzytelniania."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)  # Przechowuje hash hasła
    is_admin = db.Column(db.Boolean, default=False)  # Dodane pole dla uprawnień administratora
    organizational_unit_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)  # Przypisanie do komórki organizacyjnej

    # Metoda ustawiająca (hashująca) hasło
    def set_password(self, password: str) -> None:
        """
        Ustawia hasło użytkownika (hashuje i zapisuje).

        Args:
            password: Hasło w formie jawnej (plaintext)
        """
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    # Metoda sprawdzająca hasło
    def check_password(self, password: str) -> bool:
        """
        Sprawdza, czy podane hasło jest poprawne.

        Args:
            password: Hasło w formie jawnej do sprawdzenia

        Returns:
            bool: True jeśli hasło poprawne, False w przeciwnym razie
        """
        return bcrypt.check_password_hash(self.password_hash, password)
    
    # Pola uprawnień
    can_view = db.Column(db.Boolean, default=True)  # Może przeglądać substancje
    can_add = db.Column(db.Boolean, default=False)  # Może dodawać substancje
    can_edit = db.Column(db.Boolean, default=False)  # Może edytować substancje (np. komentarze)
    can_delete = db.Column(db.Boolean, default=False)  # Może usuwać substancje
    can_move = db.Column(db.Boolean, default=False)  # Może przenosić substancje
    can_copy = db.Column(db.Boolean, default=False)  # Może kopiować substancje
    can_upload_sds = db.Column(db.Boolean, default=False)  # Może dodawać/usuwać pliki SDS
    can_add_location = db.Column(db.Boolean, default=False)  # Może dodawać lokalizacje
    can_delete_location = db.Column(db.Boolean, default=False)  # Może usuwać lokalizacje
    can_update_databases = db.Column(db.Boolean, default=False)  # Może aktualizować bazy substancji (CLP, SVHC)

    def has_access_to_organizational_unit(self, location_id: int) -> bool:
        """
        Sprawdza, czy użytkownik ma dostęp do PRZEGLĄDANIA danej komórki organizacyjnej.
        Administratorzy mają dostęp do wszystkich komórek.
        Zwykli użytkownicy mogą przeglądać wszystkie komórki (tylko odczyt).

        Args:
            location_id: ID komórki organizacyjnej do sprawdzenia

        Returns:
            bool: True jeśli użytkownik może przeglądać, False w przeciwnym razie
        """
        # Admin ma dostęp do wszystkiego
        if self.is_admin:
            return True

        # Użytkownicy z przypisaną komórką mogą przeglądać wszystkie komórki
        # (ale modyfikować tylko swoją - sprawdza can_modify_organizational_unit)
        if self.organizational_unit_id is not None:
            return True

        # Użytkownicy bez przypisanej komórki nie mają dostępu
        return False

    def can_modify_organizational_unit(self, location_id: int) -> bool:
        """
        Sprawdza, czy użytkownik może MODYFIKOWAĆ daną komórkę organizacyjną.
        Administratorzy mogą modyfikować wszystkie komórki.
        Zwykli użytkownicy mogą modyfikować tylko przypisaną im komórkę.

        Args:
            location_id: ID komórki organizacyjnej do sprawdzenia

        Returns:
            bool: True jeśli użytkownik może modyfikować, False w przeciwnym razie
        """
        # Admin może modyfikować wszystko
        if self.is_admin:
            return True

        # Użytkownik może modyfikować tylko swoją przypisaną komórkę
        if self.organizational_unit_id is None:
            return False

        return self.organizational_unit_id == location_id

    def __repr__(self) -> str:
        return f'<User {self.username}>'

class AuditLog(db.Model):
    """Model dziennika zmian (Audit Log)."""
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # Czas zdarzenia
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Kto? (może być None dla akcji systemowych)
    username = db.Column(db.String(80), nullable=True)  # Przechowujemy też nazwę, na wypadek usunięcia użytkownika
    action = db.Column(db.String(100), nullable=False)  # Co? Np. CREATE_LOCATION, DELETE_SUBSTANCE
    target_type = db.Column(db.String(50), nullable=True)  # Jaki typ obiektu? Np. Location, Substance
    target_id = db.Column(db.Integer, nullable=True)  # ID obiektu, którego dotyczy akcja
    details = db.Column(db.Text, nullable=True)  # Dodatkowe informacje, np. zmienione wartości

    # Relacja do użytkownika (opcjonalna)
    user = db.relationship('User', backref='audit_logs', lazy=True)

    def __repr__(self) -> str:
        return f'<AuditLog {self.timestamp} - {self.username} - {self.action}>'
    

class ExcelSourceSubstance(db.Model):
    """Model przechowujący dane zaimportowane z pliku Excel."""
    __tablename__ = 'excel_source_substances' # Nazwa nowej tabeli

    id = db.Column(db.Integer, primary_key=True)
    # Kolumny odpowiadające tym w Excelu, które chcesz przeszukiwać/wyświetlać
    name = db.Column(db.Text)  # TEXT dla bardzo długich nazw (do 2048 chars)
    cas = db.Column(db.Text)  # TEXT dla list numerów CAS (do 484 chars)
    ec_number = db.Column(db.Text)  # TEXT dla list numerów EC (do 441 chars)
    classification = db.Column(db.Text, nullable=True)
    h_phrases = db.Column(db.Text, nullable=True)
    scl_mfactor = db.Column(db.Text, nullable=True)

    def __repr__(self) -> str:
        return f'<ExcelSourceSubstance {self.name} (CAS: {self.cas})>'

class SVHCSubstance(db.Model):
    """Model przechowujący dane z listy SVHC."""
    __tablename__ = 'svhc_substances'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)  # TEXT dla bardzo długich nazw
    cas = db.Column(db.Text)  # TEXT dla list numerów CAS
    ec_number = db.Column(db.Text)  # TEXT dla list numerów EC
    reason = db.Column(db.Text, nullable=True)
    date_inclusion = db.Column(db.String(50), nullable=True)

    def __repr__(self) -> str:
        return f'<SVHCSubstance {self.name} (CAS: {self.cas})>'