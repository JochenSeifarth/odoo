from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):

    def _get_shop_payment_values(self, order, **kwargs):
        values = super()._get_shop_payment_values(order, **kwargs)

        if order._has_prepayment():
            values.update(
                self._get_payment_values(
                    order,
                    is_down_payment=True,
                    website_id=order.website_id.id,
                ),
            )

        return values
