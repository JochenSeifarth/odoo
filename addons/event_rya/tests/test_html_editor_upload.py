from unittest.mock import MagicMock

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.event_rya.controllers.html_editor_controller import EventRyaHtmlEditor
from odoo.addons.html_editor.controllers import main as html_editor_main


@tagged("post_install", "-at_install")
class TestEventAttachmentUploadPublic(TransactionCase):

    def _create_via_controller(self, res_model, name="upload.png"):
        controller = EventRyaHtmlEditor()
        mock_request = MagicMock()
        mock_request.env = self.env
        mock_request.httprequest = None
        original_request = html_editor_main.request
        html_editor_main.request = mock_request
        try:
            return controller._attachment_create(
                name=name,
                data=b"\x89PNG\r\n\x1a\n",
                res_model=res_model,
                res_id=1,
            )
        finally:
            html_editor_main.request = original_request

    def test_attachment_create_event_model_sets_public(self):
        attachment = self._create_via_controller("event.event", name="event_upload.png")
        self.assertTrue(attachment.public)

    def test_attachment_create_event_submodel_sets_public(self):
        attachment = self._create_via_controller("event.registration", name="event_reg.png")
        self.assertFalse(attachment.public)

    def test_attachment_create_non_event_model_keeps_default(self):
        attachment = self._create_via_controller("res.partner", name="partner_upload.png")
        self.assertFalse(attachment.public)
