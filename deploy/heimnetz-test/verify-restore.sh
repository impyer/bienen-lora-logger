#!/bin/sh
# Nicht-destruktiver Restore-Test: neue isolierte Neben-Datenbank.
# Bestehende Ziel-Datenbanken werden NICHT überschrieben.
set -eu
cd "$(dirname "$0")"
if [ "$#" -ne 1 ] || [ ! -s "$1" ]; then
    echo 'Nutzung: ./verify-restore.sh backups/stockkarte-test-DATUM.dump' >&2
    exit 1
fi
[ -f .env ] || { echo '.env fehlt' >&2; exit 1; }
backup="$1"
compose() { docker compose --env-file .env -f compose.yaml "$@"; }
# Immer die ausdrücklich eigene Testquelle validieren.
source_db=$(compose exec -T db psql -U bienenlogger -d bienenlogger_test -Atqc 'SELECT current_database()')
[ "$source_db" = 'bienenlogger_test' ] || { echo 'ABBRUCH: Falsche Quell-DB' >&2; exit 1; }
# Ein fester, exklusiver Restore-Zielname. Bereits vorhandene DB wird nie gelöscht.
name='bienenlogger_restore_check'
exists=$(compose exec -T db psql -U bienenlogger -d postgres -Atqc "SELECT EXISTS (SELECT 1 FROM pg_database WHERE datname = '$name')")
[ "$exists" = 'f' ] || { echo "ABBRUCH: $name existiert schon – nie automatisch löschen" >&2; exit 1; }
compose exec -T db createdb -U bienenlogger "$name"
# Absichtlich kein trap mit DROP DATABASE: Ein Fehlerfall muss untersucht werden.
if ! compose exec -T db pg_restore -U bienenlogger -d "$name" --no-owner --no-privileges < "$backup"; then
    echo "RESTORE FEHLGESCHLAGEN; $name bleibt zur Diagnose erhalten." >&2
    exit 1
fi
source_count=$(compose exec -T db psql -U bienenlogger -d bienenlogger_test -Atqc 'SELECT count(*) FROM bienen.sk_kategorie')
restore_count=$(compose exec -T db psql -U bienenlogger -d "$name" -Atqc 'SELECT count(*) FROM bienen.sk_kategorie')
[ "$source_count" = "$restore_count" ] || { echo 'ABBRUCH: Kataloganzahl unterscheidet sich' >&2; exit 1; }
source_colonies=$(compose exec -T db psql -U bienenlogger -d bienenlogger_test -Atqc 'SELECT count(*) FROM bienen.volk')
restore_colonies=$(compose exec -T db psql -U bienenlogger -d "$name" -Atqc 'SELECT count(*) FROM bienen.volk')
[ "$source_colonies" = "$restore_colonies" ] || { echo 'ABBRUCH: Volk-Anzahl unterscheidet sich' >&2; exit 1; }

# Vergleiche auch den tatsächlichen Bestand und inhaltliche Historien:
# Kategorien-/Volk-Anzahlen allein würden einen fehlenden Revisionsdatensatz übersehen.
for table in sk_durchsicht sk_durchsicht_revision sk_checkliste_version sk_checkliste_feld sk_benutzer sk_benutzer_volk; do
    source_rows=$(compose exec -T db psql -U bienenlogger -d bienenlogger_test -Atqc \
        "SELECT count(*) FROM bienen.$table")
    target_rows=$(compose exec -T db psql -U bienenlogger -d "$name" -Atqc \
        "SELECT count(*) FROM bienen.$table")
    [ "$source_rows" = "$target_rows" ] || { echo "ABBRUCH: $table: $source_rows != $target_rows" >&2; exit 1; }
done
sql="SELECT COALESCE(jsonb_agg(jsonb_build_object('id',durchsicht_id,'revision',revision,
   'datum',ereignis_datum,'zeit',ereignis_zeit,'genauigkeit',zeitgenauigkeit,
   'werte',werte,'notiz',notiz,'autor',autor,'geloescht',geloescht)
   ORDER BY durchsicht_id,revision)::text,'[]')
   FROM bienen.sk_durchsicht_revision"
original_history=$(compose exec -T db psql -U bienenlogger -d bienenlogger_test -Atqc "$sql")
restored_history=$(compose exec -T db psql -U bienenlogger -d "$name" -Atqc "$sql")
[ "$original_history" = "$restored_history" ] || {
    echo 'ABBRUCH: Wiederhergestellte Revisionshistorie weicht inhaltlich ab' >&2; exit 1;
}
[ "$original_history" != '[]' ] || {
    echo 'ABBRUCH: Es wurden keine Durchsichtsrevisionen für den Restore-Test erfasst' >&2; exit 1;
}

printf 'Restore erfolgreich in %s: %s Kategorien und %s Völker.\n' "$name" "$restore_count" "$restore_colonies"
cat <<'MSG'
Die wiederhergestellte zweite Datenbank wurde absichtlich NICHT gelöscht.
Nach manueller Prüfung nur bei ausdrücklicher Entscheidung entfernen:
  docker compose exec db dropdb -U bienenlogger bienenlogger_restore_check
Das normale Web-Frontend verwendet weiterhin bienenlogger_test.
MSG
