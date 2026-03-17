ssh rya@rya 
cd git/odoo; git fetch; git reset --hard origin/19.0
. venv_odoo/bin/activate
sudo systemctl stop rya
./odoo-bin -c /home/rya/git/odoo/rya-odoo-PROD.conf -u website_event_sale --stop-after-init
sudo systemctl restart rya; tail -f /var/log/rya/rya-odoo-server.log