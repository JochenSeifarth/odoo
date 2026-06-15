# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64

from odoo.tests import Form, users

from odoo.addons.mail.tests.common import MailCommon


class TestMailComposeMessageEventRYA(MailCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['ir.config_parameter'].set_param('mail.restrict.template.rendering', True)
        cls.test_record = cls.env['res.partner'].with_context(cls._test_context).create({
            'name': 'Test',
        })
        cls.mail_template = cls.env['mail.template'].create({
            'auto_delete': True,
            'body_html': '<p>Hello</p>',
            'lang': '{{ object.lang }}',
            'model_id': cls.env['ir.model']._get_id('res.partner'),
            'name': 'Test template',
            'use_default_to': True,
            'subject': 'Test subject',
        })

    @users('employee')
    def test_template_change_clears_attachments_when_none(self):
        attachment = self.env['ir.attachment'].create({
            'name': 'Test attachment',
            'datas': base64.b64encode(b'hello').decode(),
            'res_model': 'res.partner',
            'res_id': self.test_record.id,
            'type': 'binary',
        })
        template_with_attachment = self.mail_template.copy()
        template_with_attachment.write({'attachment_ids': [(6, 0, [attachment.id])]})
        template_without_attachment = self.mail_template.copy()

        composer_form = Form(self.env['mail.compose.message'].with_context({
            'default_model': self.test_record._name,
            'default_res_ids': self.test_record.ids,
            'default_template_id': template_with_attachment.id,
        }))

        self.assertEqual(composer_form.attachment_ids.ids, [attachment.id])

        composer_form.template_id = template_without_attachment

        self.assertFalse(composer_form.attachment_ids.ids)
