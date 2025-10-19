def register_blueprints(app):
    """
    Rejestruje wszystkie blueprinty aplikacji.
    
    Ta funkcja importuje i rejestruje wszystkie moduły z trasami (routes) 
    w aplikacji Flask.
    """
    from routes.auth import auth_bp
    from routes.locations import locations_bp
    from routes.substances import substances_bp
    from routes.files import files_bp
    from routes.admin import admin_bp
    from routes.export import export_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(locations_bp)
    app.register_blueprint(substances_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(export_bp)