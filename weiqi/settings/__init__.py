
import os

from .settings_base import *

try:
    # settings_local.py can override base settings, usually for development.
    from .settings_local import *
except ImportError:
    pass


# Settings can be loaded from an external file with the path given as environment variable.
# This is useful for deployment on servers.
if 'WEIQI_SETTINGS' in os.environ:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'weiqi.settings', os.environ['WEIQI_SETTINGS'])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    globals().update(mod.__dict__)
