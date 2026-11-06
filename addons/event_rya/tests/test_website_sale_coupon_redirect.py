from urllib.parse import parse_qs, urlsplit

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestWebsiteSaleCouponRedirect(HttpCase):

    def _coupon_url(self):
        lang = self.env["website"].get_current_website().default_lang_id.url_code
        return f"/{lang}/coupon/TEST?r=."

    def test_coupon_redirect_to_referrer(self):
        response = self.url_open(
            self._coupon_url(),
            allow_redirects=False,
            headers={"Referer": f"{self.base_url()}/previous-page?sort=popular"},
        )

        self.assertEqual(response.status_code, 303)
        location = urlsplit(response.headers["Location"])
        self.assertEqual(location.path, "/previous-page")
        self.assertEqual(parse_qs(location.query)["sort"], ["popular"])

    def test_coupon_redirect_without_referrer_uses_shop(self):
        response = self.url_open(
            self._coupon_url(),
            allow_redirects=False,
            headers={"Referer": ""},
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(urlsplit(response.headers["Location"]).path, "/event")
