import logging
import os
import requests
from datetime import datetime

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class O2RouterService:

    BASE_URL = os.getenv("ROUTE_BASE_URL", "http://localhost:3000/route")
    API_KEY = os.getenv("ROUTE_API_KEY", "asw")

    def route(self, start, end):
        from_lat, from_lon = start
        to_lat, to_lon = end

        _logger.info(
            "Routing request: (%s, %s) --> (%s, %s)",
            from_lat,
            from_lon,
            to_lat,
            to_lon,
        )

        data = self._fetch_route(from_lat, from_lon, to_lat, to_lon)
        return data

    def _fetch_route(self, from_lat, from_lon, to_lat, to_lon):
        params = {"from": f"{from_lat},{from_lon}", "to": f"{to_lat},{to_lon}"}
        headers = {"X-Api-Key": self.API_KEY}

        try:
            response = requests.get(
                self.BASE_URL, params=params, headers=headers, timeout=10
            )
        except requests.RequestException as e:
            _logger.exception("Upstream request failed")
            raise UserError("Routing service temporarily unavailable")

        if response.status_code != 200:
            _logger.error("Upstream error %s: %s", response.status_code, response.text)
            raise UserError("Routing provider error")

        _logger.info(
            "Routing response: (%s, %s) --> (%s, %s) ::: %s",
            from_lat,
            from_lon,
            to_lat,
            to_lon,
            response.json(),
        )

        return response.json()

    def to_geojson_feature(
        self, data, from_lat, from_lon, to_lat, to_lon, upstream_time, total_time
    ):
        return {
            "type": "Feature",
            "geometry": data.get("geometry"),
            "properties": {
                "distance_nm": data.get("distance_nm"),
                "raw_hops": data.get("raw_hops"),
                "smooth_hops": data.get("smooth_hops"),
                "from": {"lat": from_lat, "lon": from_lon},
                "to": {"lat": to_lat, "lon": to_lon},
                "timing": {
                    "upstream_seconds": round(upstream_time, 6),
                    "total_seconds": round(total_time, 6),
                },
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        }

    @staticmethod
    def _haversine_distance_nm(lat1, lon1, lat2, lon2) -> float:
        """Returns distance in nautical miles between two points"""
        R_km = 6371  # Earth radius in km
        if None in [lat1, lon1, lat2, lon2]:
            return 0.0
        phi1: float = math.radians(lat1)
        phi2: float = math.radians(lat2)
        d_phi: float = math.radians(lat2 - lat1)
        d_lambda: float = math.radians(lon2 - lon1)

        a: float = (
            math.sin(d_phi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
        )
        c: float = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance_km: float = R_km * c
        distance_nm: float = distance_km * 0.539957  # Convert km to nautical miles
        return distance_nm
