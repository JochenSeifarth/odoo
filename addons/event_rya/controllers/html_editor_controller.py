from odoo.addons.html_editor.controllers.main import HTML_Editor


class EventRyaHtmlEditor(HTML_Editor):

    def _attachment_create(self, name='', data=False, url=False, res_id=False, res_model='ir.ui.view'):
        attachment = super()._attachment_create(
            name=name, data=data, url=url, res_id=res_id, res_model=res_model,
        )
        # Event-related uploads (e.g. images attached to event records) should be
        # publicly accessible so they can be displayed on the website.
        # make previously created attachments public:
        # update ir_attachment set public = true  where res_model = 'event.event' and public  is false
        if res_model and res_model == 'event.event' and not attachment.public:
            attachment.sudo().write({'public': True})
        return attachment
