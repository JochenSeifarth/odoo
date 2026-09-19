from odoo import models
from odoo.http import request


class WebsiteSeoMetadata(models.AbstractModel):
    _inherit = 'website.seo.metadata'

    def _default_website_meta(self):
        self.ensure_one()

        metadata = super()._default_website_meta()

        page = self.page_ids[:1] if 'page_ids' in self._fields else None
        if page and page.menu_ids:
            title = '%s | %s' % (
                page.menu_ids[0].name,
                request.website.name,
            )
            metadata['default_opengraph']['og:title'] = title
            metadata['default_twitter']['twitter:title'] = title

        return metadata
