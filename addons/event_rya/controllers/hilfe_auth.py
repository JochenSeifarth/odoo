from odoo import http
from odoo.http import request


class HilfeAuthController(http.Controller):

    @http.route(
        "/hilfe/auth",
        type="http",
        auth="none",
        methods=["GET"],
        csrf=False,
        save_session=False,
    )
    def hilfe_auth(self):
        if not request.session.uid:
            return request.make_response("", status=401)

        return request.make_response("", status=204)
