#!/bin/bash
set -euo pipefail
set -x
DUMPFILE=$(find /tmp -maxdepth 1 -type f -name 'rya.*.zip' -printf '%T@ %p\n' | sort -nr | head -n 1 | cut -d' ' -f2-)
if [[ -z "$DUMPFILE" || ! -f "$DUMPFILE" ]]; then
    echo "ERROR: No dump file found in /tmp (rya.*.zip)" >&2
    exit 1
fi
cd /home/jochen/git/odoo
. ./venv_odoo/bin/activate
python3 odoo-bin.py db -c ./rya-odoo-DEV.conf load --force --neutralize ryadev $DUMPFILE
# Reset active internal users through the ORM so passwords are hashed.
python3 odoo-bin.py shell -c ./rya-odoo-DEV.conf -d ryadev --no-http <<'PY'
internal_group = env.ref('base.group_user')
users = env['res.users'].sudo().search([
    ('active', '=', True),
    ('share', '=', False),
    ('group_ids', 'in', internal_group.id),
], order='login')
users.write({'password': 'dev'})
env.cr.commit()
print(f"Reset passwords for {len(users)} active internal users:")
for user in users:
    print(f"- {user.login} ({user.name})")
PY
# allow mails to local mailpit
sudo -u postgres psql -d ryadev -c "UPDATE ir_mail_server SET smtp_host = 'localhost', smtp_debug = TRUE WHERE active IS TRUE AND smtp_host = 'invalid' AND smtp_port = 1025;"
sudo -u postgres psql -d ryadev -c "UPDATE ir_cron SET active = TRUE WHERE id = (SELECT res_id FROM ir_model_data WHERE model = 'ir.cron' AND module = 'mail' AND name = 'ir_cron_mail_scheduler_action') RETURNING id, active, nextcall;"