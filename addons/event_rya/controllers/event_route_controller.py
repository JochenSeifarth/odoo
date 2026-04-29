from odoo import http
from odoo.http import request
import logging
from ..services.o2_router_service import O2RouterService

_logger = logging.getLogger(__name__)


class EventRouteController(http.Controller):

    @http.route(
        "/event/<int:event_id>/routejson",
        type="http",
        auth="public",
        csrf=False,
        methods=["GET"],
    )
    def event_route(self, event_id):

        try:
            event = request.env["event.event"].sudo().browse(event_id)
            event_route = event.get_route()
            response = request.make_json_response(event_route)
            return response

        except Exception as e:
            _logger.exception("Full route display failed")

            return {
                "event_id": event_id,
                "error": str(e),
                "legs": [],
                "route": [],
            }

    @http.route(
        "/event/<int:event_id>/route",
        type="http",
        auth="public",
        website=True,
        csrf=False,
        methods=["GET"],
    )
    def event_route_page(self, event_id, **kw):

        event = request.env["event.event"].sudo().browse(event_id)

        return request.render(
            "event_rya.sailing_route_template",
            {
                "event": event,
            },
        )
