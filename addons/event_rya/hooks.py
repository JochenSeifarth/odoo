# event_rya/hooks.py

from odoo.api import Environment, SUPERUSER_ID

def load_translations(cr, registry):
    """
    Lädt alle Übersetzungen für das Modul event_rya.
    Wird bei Installation und Update ausgeführt.
    """
    env = Environment(cr, SUPERUSER_ID, {})
    module_name = 'event_rya'
    
    # Alle Übersetzungen des Moduls laden
    module = env['ir.module.module'].search([('name', '=', module_name)], limit=1)
    if module:
        env['ir.translation']._load_module_terms(module_name)
        env.cr.commit()  # sicherstellen, dass alles gespeichert wird
        print(f"✅ Übersetzungen für Modul '{module_name}' wurden geladen!")
