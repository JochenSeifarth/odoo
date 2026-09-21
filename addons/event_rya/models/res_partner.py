import urllib.parse

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    coordinates = fields.Char(string='Coordinates', compute='_compute_coordinates', store=False)
    google_map_url = fields.Char(string='Google Maps URL', compute='_compute_google_map_url', store=False)

    @api.depends('website', 'partner_latitude', 'partner_longitude')
    def _compute_google_map_url(self, zoom=10):
        for partner in self:
            # return direct link to a Google Maps location if we have one
            if partner.website and partner.website.startswith('https://maps.'):
                partner.google_map_url = partner.website
                continue

            # Get base link from parent class
            base_link = super(ResPartner, partner).google_map_link(zoom)

            # enhance Google Maps link with marker on Coordinates
            if partner.partner_latitude and partner.partner_longitude:
                parsed = urllib.parse.urlsplit(base_link)
                query = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))
                q = query.get('q', '')
                q += '@%s,%s' % (partner.partner_latitude, partner.partner_longitude)
                query['q'] = q
                partner.google_map_url = urllib.parse.urlunsplit(parsed._replace(query=urllib.parse.urlencode(query)))
            else:
                partner.google_map_url = base_link

    def google_map_link(self, zoom=10):
        self.ensure_one()
        # call again as we may want a different zoom level
        self._compute_google_map_url(zoom)
        # Delegate to the computed field value for backward compatibility
        return self.google_map_url or super().google_map_link(zoom=zoom)

    @api.depends('partner_latitude', 'partner_longitude')
    def _compute_coordinates(self):
        for partner in self:
            lat = partner.partner_latitude
            lon = partner.partner_longitude
            if lat is None or lon is None:
                partner.coordinates = False
                continue
            lat_dms = self._deg_to_dms(lat, is_lat=True)
            lon_dms = self._deg_to_dms(lon, is_lat=False)
            partner.coordinates = f"{lat_dms} {lon_dms}"

    @staticmethod
    def _deg_to_dms(value, is_lat=True):
        """Convert decimal degrees to DMS string with hemisphere.

        Example: 48.208333 -> 48°12'30"N
        """
        if value is None:
            return ''
        hemi = ''
        if is_lat:
            hemi = 'N' if value >= 0 else 'S'
        else:
            hemi = 'E' if value >= 0 else 'W'
        absval = abs(float(value))
        deg = int(absval)
        m_float = (absval - deg) * 60
        minutes = int(m_float)
        seconds = round((m_float - minutes) * 60)
        deg_fmt = f"{deg:02d}" if is_lat else f"{deg:03d}"
        return f'{deg_fmt}°{minutes:02d}\'{seconds:02d}"{hemi}'
