# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class MailComposeMessage(models.TransientModel):
    _inherit = ['mail.compose.message']

    @api.depends('composition_mode', 'model', 'res_domain', 'res_ids', 'template_id')
    def _compute_attachment_ids(self):
        """Clear stale attachments when switching to a template with none."""
        for composer in self:
            res_ids = composer._evaluate_res_ids() or [0]
            if (composer.template_id.attachment_ids and
                (composer.composition_mode == 'mass_mail' or composer.composition_batch)):
                composer.attachment_ids = composer.template_id.attachment_ids
            elif composer.template_id and composer.composition_mode == 'comment' and len(res_ids) == 1:
                rendered_values = composer._generate_template_for_composer(
                    res_ids,
                    ('attachment_ids', 'attachments'),
                )[res_ids[0]]
                attachment_ids = rendered_values.get('attachment_ids') or []
                if rendered_values.get('attachments'):
                    attachment_ids += composer.env['ir.attachment'].create([
                        {
                            'name': attach_fname,
                            'datas': attach_datas,
                            'res_model': 'mail.compose.message',
                            'res_id': 0,
                            'type': 'binary',
                        } for attach_fname, attach_datas in rendered_values.pop('attachments')
                    ]).ids
                composer.attachment_ids = attachment_ids or False
            elif not composer.template_id:
                composer.attachment_ids = False
