#!/bin/bash
set -euo pipefail
set -x
DUMPFILE=$(mktemp /tmp/rya.XXXXXX.zip)
# odoo is particularly picky about position of options
ssh rya@rya "cd ~rya/git/odoo && ./venv_odoo/bin/python ./odoo-bin db -c ./rya-odoo-PROD.conf dump rya" 2> >(cat >&2) | pv -ptrab > $DUMPFILE
# odoo is particularly picky about position of options
cd /home/jochen/git/odoo
. ./venv_odoo/bin/activate 
python3 odoo-bin.py db -c ./rya-odoo-DEV.conf load --force --neutralize ryadev $DUMPFILE
# allow mails to local mailpit
sudo -u postgres psql -d ryadev -c "UPDATE ir_mail_server SET smtp_host = 'localhost', smtp_debug = TRUE WHERE active IS TRUE AND smtp_host = 'invalid' AND smtp_port = 1025;"
sudo -u postgres psql -d ryadev -c "UPDATE ir_cron SET active = TRUE WHERE id = (SELECT res_id FROM ir_model_data WHERE model = 'ir.cron' AND module = 'mail' AND name = 'ir_cron_mail_scheduler_action') RETURNING id, active, nextcall;"