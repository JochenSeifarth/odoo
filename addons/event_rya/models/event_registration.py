from odoo import fields, models


class EventRegistration(models.Model):
    _inherit = 'event.registration'

# we badly need this to be a stored field so that it can be properly sorted by on kanban and list views etc,
# properties should be merged by Odoo - so we do not lose any of the compute logic
    event_begin_date = fields.Datetime(store=True, index=True)
