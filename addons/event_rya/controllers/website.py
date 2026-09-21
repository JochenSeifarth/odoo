import json

from odoo import http

from odoo.addons.website.controllers.main import Website


class WebsiteSeoSuggestDisable(Website):

    @http.route(
        ['/website/seo_suggest'],
        type='jsonrpc',
        auth="user",
        website=True,
        readonly=True,
        override=True,
    )
    def seo_suggest(self, keywords=None, lang=None):
        # Completely disable Google SEO suggestions, as they cause hangs and HTTP 502 errors
        return json.dumps([keywords])
