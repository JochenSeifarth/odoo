{
    "name": "Website A4 Sedcard Snippet",
    "summary": "A print-faithful A4 sedcard snippet for the website builder",
    "version": "1.0",
    "category": "Website",
    "depends": ["website"],
    "data": [
        "views/sedcard_snippet.xml",
        "views/snippets.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "odoo_sedcard_snapping/static/src/css/sedcard.css",
            "odoo_sedcard_snapping/static/src/js/sedcard_print.js",
        ],
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
