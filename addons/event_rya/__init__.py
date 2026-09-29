# event_rya/__init__.py
from . import controllers
from . import models

# Installed on import, not on _register_hook: the core templates are compiled
# while the module data is loaded, which happens before the models are set up.
from .models.qweb_deprecation_filter import install as _install_qweb_deprecation_filter

_install_qweb_deprecation_filter()
