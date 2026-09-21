# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    whatsapp_button_enabled = fields.Boolean(
        string="Enable WhatsApp Button",
        related='website_id.whatsapp_button_enabled',
        readonly=False,
    )
    whatsapp_phone_number = fields.Char(
        string="WhatsApp Phone Number",
        related='website_id.whatsapp_phone_number',
        readonly=False,
        help="Phone number with country code (e.g., +1234567890)",
    )
    whatsapp_default_message = fields.Text(
        string="Default Message",
        related='website_id.whatsapp_default_message',
        readonly=False,
        help="Pre-filled message when user clicks the button",
    )
    whatsapp_button_position = fields.Selection(
        string="Button Position",
        related='website_id.whatsapp_button_position',
        readonly=False,
    )
    whatsapp_button_size = fields.Selection(
        string="Button Size",
        related='website_id.whatsapp_button_size',
        readonly=False,
    )
    whatsapp_tooltip_text = fields.Char(
        string="Tooltip Text",
        related='website_id.whatsapp_tooltip_text',
        readonly=False,
    )
