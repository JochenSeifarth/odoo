
from odoo.http import request

from odoo.addons.website_event_sale.controllers.main import WebsiteEventSaleController


class WebsiteEventSaleControllerRya(WebsiteEventSaleController):

    def _prepare_event_register_values(self, event, **post):
        values = super()._prepare_event_register_values(event, **post)

        # Add our event JSON-LD data as 'product_markup_data' so it gets
        # picked up by the template website_sale.website_sale_layout
        values['product_markup_data'] = event.sudo()._to_markup_data(request.website)

        return values
