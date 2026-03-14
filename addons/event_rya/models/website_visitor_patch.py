# event_rya/models/website_visitor_patch.py
from odoo import models, api
import logging
from pytz import timezone
from datetime import datetime
from odoo.http import request

_logger = logging.getLogger(__name__)

class WebsiteVisitor(models.Model):
    _inherit = 'website.visitor'

    def _get_visitor_timezone(self):
        """Return the visitor timezone, normalized to the event's offset if available."""
        # Standard Visitor-TZ oder Fallback
        visitor_tz = super()._get_visitor_timezone() or 'Europe/Madrid'

        try:
            website_tz     = 'Europe/Madrid'
            website_tz_obj = timezone(website_tz)
            visitor_tz_obj = timezone(visitor_tz)
                
            # Vergleiche UTC-Offsets zur Normalisierung
            now = datetime.utcnow()
            if visitor_tz_obj.utcoffset(now) == website_tz_obj.utcoffset(now):
                _logger.debug(
                    "Visitor tz %s matches 'Europe/Madrid' offset, using tz '%s'",
                    visitor_tz, website_tz
                )
                visitor_tz = website_tz
        except Exception as e:
            _logger.warning("Error normalizing visitor tz with event tz: %s", e)

        _logger.debug("Final visitor timezone: %s", visitor_tz)
        return visitor_tz