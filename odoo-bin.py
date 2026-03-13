#!/usr/bin/env python3
import odoo.netsvc
from odoo.netsvc import ColoredFormatter

# Monkeypatch für init_logger: immer Farben aktivieren und nur Uhrzeit
_original_init_logger = odoo.netsvc.init_logger

def patched_init_logger(*args, **kwargs):
    # Original init_logger aufrufen
    _original_init_logger(*args, **kwargs)

    # Alle StreamHandler suchen und den Formatter ersetzen
    for handler in odoo.netsvc.logging.getLogger().handlers:
        if isinstance(handler, odoo.netsvc.logging.StreamHandler):
            handler.setFormatter(ColoredFormatter(handler.formatter._fmt, "%H:%M:%S"))

# Patchen
odoo.netsvc.init_logger = patched_init_logger

from odoo.tools import config

import odoo.cli
if __name__ == "__main__":
    odoo.cli.main()