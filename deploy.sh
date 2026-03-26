#!/usr/bin/env bash
set -euo pipefail

REMOTE="rya@rya"
APP_DIR="/home/rya/git/odoo"
CONFIG="/home/rya/git/odoo/rya-odoo-PROD.conf"
LOG_FILE="/var/log/rya/rya-odoo-server.log"
SERVICE="rya"
BRANCH="19.0"
BACKUP_DIR="/home/jochen/Odoo-Backups"

# Usage:
# ./deploy.sh [module1 module2 ...]
# Default module: event_rya

MODULES="${*:-event_rya}"
MODULE_CSV=$(echo "$MODULES" | tr ' ' ',')

ssh "$REMOTE" \
  CONFIG="$CONFIG" \
  APP_DIR="$APP_DIR" \
  SERVICE="$SERVICE" \
  LOG_FILE="$LOG_FILE" \
  BRANCH="$BRANCH" \
  BACKUP_DIR="$BACKUP_DIR" \
  MODULE_CSV="$MODULE_CSV" \
  bash -se <<'EOF'
set -euo pipefail

cd "$APP_DIR"

echo "=== Fetch latest code ==="
git fetch
git reset --hard origin/"$BRANCH"

echo "=== Creating database backup ==="
cd $APP_DIR && ./venv_odoo/bin/python ./odoo-bin db -c $CONFIG dump rya $BACKUP_DIR/rya-backup-$(date +%F-%H%M%S).zip

echo "=== Stopping service ==="
sudo systemctl stop "$SERVICE"

echo "=== Updating Odoo modules: $MODULE_CSV ==="
. venv_odoo/bin/activate
./odoo-bin -c "$CONFIG" -u "$MODULE_CSV" --stop-after-init

echo "=== Restarting service ==="
sudo systemctl restart "$SERVICE"

echo "=== Tailing logs ==="
tail -f "$LOG_FILE"
EOF
