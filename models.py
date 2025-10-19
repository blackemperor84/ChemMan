from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# Inicjalizacja obiektów
db = SQLAlchemy()
bcrypt = Bcrypt()

class Location(db.Model):
    """Model lokalizacji substancji chemicznych."""
    __tablename__ = 'locations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacja: Jedna lokalizacja -> wiele substancji
    # cascade="all, delete-orphan" zapewnia usunięcie substancji przy usuwaniu lokalizacji
    substances = db.relationship('Substance', backref='location', lazy=True, cascade="all, delete-orphan")

    def update_modification_time(self):
        """Aktualizuje pole last_modified na aktualny czas."""
        self.last_modified = datetime.utcnow()
        return self
    
    def __repr__(self):
        return f'<Location {self.name}>'

class Substance(db.Model):
    """Model substancji chemicznej."""
    __tablename__ = 'substances'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    cas = db.Column(db.String(20), nullable=True)
    ec_number = db.Column(db.String(20), nullable=True)  # Dodanie numeru WE
    classification = db.Column(db.Text, nullable=True)
    h_phrases = db.Column(db.Text, nullable=True)
    scl_mfactor = db.Column(db.Text, nullable=True)
    comment = db.Column(db.Text, nullable=True)
    is_cmr = db.Column(db.Boolean, default=False)  # Flaga CMR
    is_svhc = db.Column(db.Boolean, default=False)  # Flaga SVHC
    sds_filename = db.Column(db.String(255), nullable=True)
    sds_upload_timestamp = db.Column(db.DateTime, nullable=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    physical_location = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f'<Substance {self.name} (CAS: {self.cas}) in Loc {self.location_id}>'

class User(db.Model, UserMixin):
    """Model użytkownika systemu z obsługą uwierzytelniania."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)  # Przechowuje hash hasła
    is_admin = db.Column(db.Boolean, default=False)  # Dodane pole dla uprawnień administratora

    # Metoda ustawiająca (hashująca) hasło
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    # Metoda sprawdzająca hasło
    def check_password(self, password):
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

    def __repr__(self):
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

    def __repr__(self):
        return f'<AuditLog {self.timestamp} - {self.username} - {self.action}>'
    

class ExcelSourceSubstance(db.Model):
    """Model przechowujący dane zaimportowane z pliku Excel."""
    __tablename__ = 'excel_source_substances' # Nazwa nowej tabeli

    id = db.Column(db.Integer, primary_key=True)
    # Kolumny odpowiadające tym w Excelu, które chcesz przeszukiwać/wyświetlać
    name = db.Column(db.String(255), index=True) # Dodajemy indeks dla szybszego wyszukiwania
    cas = db.Column(db.String(20), index=True)   # Dodajemy indeks
    ec_number = db.Column(db.String(20), index=True) # Dodajemy indeks
    classification = db.Column(db.Text, nullable=True)
    h_phrases = db.Column(db.Text, nullable=True)
    scl_mfactor = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<ExcelSourceSubstance {self.name} (CAS: {self.cas})>'

class SVHCSubstance(db.Model):
    """Model przechowujący dane z listy SVHC."""
    __tablename__ = 'svhc_substances'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=True)
    cas = db.Column(db.String(20), index=True)
    ec_number = db.Column(db.String(20), index=True)
    reason = db.Column(db.Text, nullable=True)
    date_inclusion = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f'<SVHCSubstance {self.name} (CAS: {self.cas})>'