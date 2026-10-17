#!/bin/sh
# Nur offizieller PostgreSQL-Entrypoint auf LEEREM eigenen PG-Volume.
# Nie manuell gegen die normale Bienenlogger-Datenbank ausführen!
set -eu
if [ "${POSTGRES_DB:-}" != "bienenlogger_test" ]; then
    echo "ABBRUCH: Nicht die dedizierte Testdatenbank" >&2
    exit 1
fi
if [ "$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atqc "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'bienen')")" != "f" ]; then
    echo "ABBRUCH: Das Schema bienen existiert bereits" >&2
    exit 1
fi
for sql in /bl_init/00_schema.sql /bl_init/01_stockkarte.sql /bl_init/02_benutzer.sql; do
    echo "Init eigene Testdatenbank: $(basename "$sql")"
    psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$sql" > /dev/null
done
