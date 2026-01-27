"""
Demo-specific app wrapper that bypasses unnecessary imports
Creates mock modules for dependencies that aren't needed in demo mode
"""
import sys
import os
from types import ModuleType

# Create mock modules for dependencies not needed in demo
def create_mock_module(name):
    """Create a mock module with common Flask extension patterns"""
    module = ModuleType(name)

    # Mock common Flask extension patterns
    def mock_init(*args, **kwargs):
        return None

    def mock_decorator(func):
        return func

    class MockCSRFProtect:
        """Mock CSRF protection that provides csrf_token"""
        def __init__(self, app=None):
            self.app = None
            if app is not None:
                self.init_app(app)

        def init_app(self, app):
            self.app = app
            # Inject csrf_token function into Jinja2 globals
            @app.context_processor
            def csrf_token():
                return {'csrf_token': lambda: 'demo-csrf-token'}

        def __call__(self, *args, **kwargs):
            return mock_decorator

    class MockMigrate:
        def __init__(self, *args, **kwargs):
            pass
        def __call__(self, *args, **kwargs):
            return mock_decorator
        def init_app(self, *args, **kwargs):
            pass

    # Set common attributes
    module.Migrate = MockMigrate
    module.CSRFProtect = MockCSRFProtect

    return module

# Mock out optional dependencies before importing app
sys.modules['flask_migrate'] = create_mock_module('flask_migrate')
sys.modules['flask_wtf'] = create_mock_module('flask_wtf')
sys.modules['flask_wtf.csrf'] = create_mock_module('flask_wtf.csrf')
sys.modules['wtforms'] = create_mock_module('wtforms')

# Now import the real app
from app import create_app

# Export for use in run_demo
__all__ = ['create_app']
