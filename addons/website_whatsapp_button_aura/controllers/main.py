# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class WhatsAppButtonController(http.Controller):

    @http.route('/website/whatsapp/config', type='json', auth='public', website=True)
    def get_whatsapp_config(self):
        """Return WhatsApp button configuration for the current website."""
        website = request.website
        return {
            'enabled': website.whatsapp_button_enabled,
            'phone': website.whatsapp_phone_number or '',
            'message': website.whatsapp_default_message or '',
            'position': website.whatsapp_button_position or 'right',
            'size': website.whatsapp_button_size or 'medium',
            'tooltip': website.whatsapp_tooltip_text or 'Chat with us on WhatsApp',
        }
