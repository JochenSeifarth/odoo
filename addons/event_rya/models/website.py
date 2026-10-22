from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    rya_google_review_url = fields.Char(
        string="Google Review URL",
        help="Direct Google URL where reviews for this website can be entered.\n"
             "It is inserted in the after the event mail of the event_rya addon, "
             "for the events published on this website.",
    )
