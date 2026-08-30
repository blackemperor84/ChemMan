"""
ChemMan Demo - Standalone Application Entry Point
This file is used as the entry point for PyInstaller
"""

import os
import sys
import webbrowser
import threading
import time

# Determine if running as frozen executable or script
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    application_path = sys._MEIPASS
    # Add parent directory to path for imports
    parent_path = os.path.dirname(application_path)
    if parent_path not in sys.path:
        sys.path.insert(0, parent_path)
    if application_path not in sys.path:
        sys.path.insert(0, application_path)
else:
    # Running as script
    application_path = os.path.dirname(os.path.abspath(__file__))
    parent_path = os.path.join(application_path, '..')
    if parent_path not in sys.path:
        sys.path.insert(0, parent_path)

# Set up environment
os.environ['FLASK_ENV'] = 'demo'
os.environ['DATABASE_URL'] = 'sqlite:///' + os.path.join(application_path, 'demo_chemman.db')

# Import after path setup
try:
    from config_demo import DemoConfig
    from app_demo_wrapper import create_app
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Application path: {application_path}")
    print(f"sys.path: {sys.path}")
    raise

def open_browser(port=5000, delay=2):
    """Open browser after short delay"""
    def _open():
        time.sleep(delay)
        webbrowser.open(f'http://127.0.0.1:{port}')

    thread = threading.Thread(target=_open)
    thread.daemon = True
    thread.start()

def main():
    """Main entry point for demo application"""

    print("=" * 60)
    print("  ChemMan v2.4.1 - Demo Version")
    print("=" * 60)
    print()
    print("System Zarzadzania Substancjami Chemicznymi")
    print()
    print("Logowanie:")
    print("   Username: admin")
    print("   Password: Demo1234")
    print()
    print("URL: http://127.0.0.1:5000")
    print()
    print("Aby zatrzymac aplikacje, nacisnij Ctrl+C")
    print("=" * 60)
    print()

    # Create Flask app
    app = create_app(DemoConfig)

    # Open browser automatically
    open_browser(port=5000, delay=3)

    # Run Flask server
    try:
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=False,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n")
        print("=" * 60)
        print("  Aplikacja zamknięta. Dziękujemy!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Błąd: {e}")
        print("\nSprawdź plik demo_chemman.log dla szczegółów")
        input("\nNaciśnij Enter aby zamknąć...")

if __name__ == '__main__':
    main()
