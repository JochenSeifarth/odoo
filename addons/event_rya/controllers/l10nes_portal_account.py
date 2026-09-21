
from odoo.addons.l10n_es.controllers.portal import L10nESPortalAccount


class RyaL10nESPortalAccount(L10nESPortalAccount):

    def _get_mandatory_billing_address_fields(self, country_sudo):
        field_names = super()._get_mandatory_billing_address_fields(country_sudo)

        # We never want any VAT / NIF or similar as this is never required for our customers
        field_names.discard('vat')

        return field_names
