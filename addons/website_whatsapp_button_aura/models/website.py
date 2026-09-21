# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Website(models.Model):
    _inherit = 'website'

    whatsapp_button_enabled = fields.Boolean(
        string="Enable WhatsApp Button",
        default=False,
    )
    whatsapp_phone_number = fields.Char(
        string="WhatsApp Phone Number",
        default="",
        help="Phone number with country code (e.g., +1234567890)",
    )
    whatsapp_default_message = fields.Text(
        string="Default Message",
        default="Hello! I have a question about your products.",
        help="Pre-filled message when user clicks the button",
    )
    whatsapp_button_position = fields.Selection([
        ('right', 'Right'),
        ('left', 'Left'),
    ], string="Button Position", default='right')
    whatsapp_button_size = fields.Selection([
        ('small', 'Small (50px)'),
        ('medium', 'Medium (60px)'),
        ('large', 'Large (70px)'),
    ], string="Button Size", default='medium')
    whatsapp_tooltip_text = fields.Char(
        string="Tooltip Text",
        default="Chat with us on WhatsApp",
    )
