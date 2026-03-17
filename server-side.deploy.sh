#!/bin/bash
set -euo pipefail  # Stop on error, undefined variable, or failed pipe

# Optional: print each command as it runs
set -x

echo "Starting Odoo update on $(hostname) at $(date)"

# Go to Odoo directory
cd ~/git/odoo

# Update git branch
git fetch
git reset --hard origin/19.0

# Activate virtual environment
source venv_odoo/bin/activate

# Stop the Odoo service
sudo systemctl stop rya

# Backup database
./odoo-bin db -c ./rya-odoo-PROD.conf dump rya /home/jochen/Odoo-Backups/rya-backup-$(date +\%F-\%H\%M\%S).zip

# Run the module update
./odoo-bin   -c ./rya-odoo-PROD.conf -u event_rya --stop-after-init

# Restart the service
sudo systemctl restart rya

# Tail the log
echo "Update completed, streaming Odoo logs..."
tail -f /var/log/rya/rya-odoo-server.log