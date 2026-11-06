from odoo.http import request, route

from odoo.addons.website_sale_loyalty.controllers.main import WebsiteSale


class WebsiteSaleCouponRedirect(WebsiteSale):

    @route()
    def activate_coupon(self, code, r="/event", **kw):
        if r == ".":
            r = request.httprequest.referrer or "/event"
        return super().activate_coupon(code, r=r, **kw)
