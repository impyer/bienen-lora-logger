#!/bin/sh
# NUR die gesonderte bienenlogger_test Datenbank; keine Produktivdaten.
set -eu
cd "$(dirname "$0")"
[ -f .env ] || { echo '.env fehlt' >&2; exit 1; }
mkdir -p backups && chmod 700 backups
umask 077
name="backups/stockkarte-test-$(date -u +%Y%m%dT%H%M%SZ).dump"
docker compose --env-file .env -f compose.yaml exec -T db \
  pg_dump -U bienenlogger -d bienenlogger_test -Fc --no-owner --no-privileges > "$name"
if [ ! -s "$name" ]; then rm -f "$name"; echo 'Backup fehlgeschlagen' >&2; exit 1; fi
docker compose --env-file .env -f compose.yaml exec -T db pg_restore --list < "$name" > /dev/null
printf 'Geprüftes Test-Backup: %s\n' "$name"
