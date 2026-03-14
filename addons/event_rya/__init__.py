# event_rya/__init__.py
from . import controllers
from . import models
from . import hooks

def post_load_hook(cr, registry):
    """
    Hook, der nach dem Laden des Moduls aufgerufen wird.
    Lädt Übersetzungen auch bei Updates.
    """
    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})
    module = env['ir.module.module'].search([('name', '=', 'event_rya')], limit=1)
    if module and module.state == 'installed':
        hooks.load_translations(cr, registry)