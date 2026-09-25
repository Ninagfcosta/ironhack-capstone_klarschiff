#!/usr/bin/env bash
# Daily backup of the decision log, alerts and monitor state (cron: 0 2 * * *).
set -euo pipefail
STAMP=$(date +%F)
DEST=${BACKUP_DIR:-$HOME/klarschiff-backups}
mkdir -p "$DEST"
docker run --rm -v deploy_klarschiff-data:/data -v "$DEST":/backup alpine \
  tar czf "/backup/klarschiff-data-$STAMP.tgz" -C /data .
# keep 30 days
find "$DEST" -name 'klarschiff-data-*.tgz' -mtime +30 -delete
echo "Backup written: $DEST/klarschiff-data-$STAMP.tgz"
