# -*- coding: utf-8 -*-
{
    'name': 'Website Floating WhatsApp Button',
    'version': '19.0.1.0.0',
    'category': 'Website',
    'summary': 'Add a floating WhatsApp chat button to your website',
    'description': """
Website Floating WhatsApp Button
================================
This module adds a floating WhatsApp button to your Odoo website.

Features:
---------
* Floating WhatsApp button on website
* Click to open WhatsApp chat
* Dynamic phone number configuration
* Customizable default message
* Position selection (left/right)
* Enable/Disable from settings
* Super lightweight (CSS + JS only)
    """,
    'author': 'Aura Odoo Tech',
    'website': 'https://auraodoo.tech',
    'license': 'LGPL-3',
    'depends': ['website'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/website_whatsapp_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_whatsapp_button_aura/static/src/css/whatsapp_button.css',
            'website_whatsapp_button_aura/static/src/js/whatsapp_button.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
   
    'support': {
        'email': 'odooaura@gmail.com',
        'youtube': 'https://www.youtube.com/@Auraodoo',
        'linkedin': 'https://www.linkedin.com/in/auraodoo/',
        'teams': 'https://teams.live.com/l/invite/FEAjpqG_VdivNGvDQE?v=g1',
        'website': 'https://www.auraodoo.tech/',
    },
      
}
