from __future__ import annotations

from odoo import models


PRIORITIZED_LANGUAGE_CODES = ("es", "en", "de", "ru")


class ResLang(models.Model):
    _inherit = "res.lang"

    def _get_frontend(self):
        frontend_languages = super()._get_frontend()
        language_priority = {
            code: index for index, code in enumerate(PRIORITIZED_LANGUAGE_CODES)
        }

        sorted_languages = sorted(
            frontend_languages.items(),
            key=lambda item: language_priority.get(
                item[1].code.split("_", 1)[0],
                len(PRIORITIZED_LANGUAGE_CODES),
            ),
        )

        return frontend_languages.__class__(dict(sorted_languages))
