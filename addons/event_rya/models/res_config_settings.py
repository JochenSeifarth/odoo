from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    rya_google_review_url = fields.Char(
        related='website_id.rya_google_review_url',
        string='Google Review URL',
        readonly=False)
