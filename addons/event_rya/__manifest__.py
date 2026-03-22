{
    "name": "Event RYA",
    "summary": "Show ticket price on event listing page",  
    "version": "1.0",
    "author": "Jochen Seifarth",
    "license": "Other proprietary",
    "category": "Website",
    "depends": [
        "base","event","website","website_event","mail",
    ],
    "data": [
        'security/ir.model.access.csv',        
        "views/event_list_rya.xml",
        "views/event_templates_page_registration_rya.xml",
        "views/sale_report_views.xml", 
        "views/event_slot_calendar_view.xml",     
        "views/event_slot_rya_views.xml",
        "report/event_report_template_full_page_ticket_rya.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
    'post_init_hook': 'load_translations',
}
