#!/usr/bin/env bash
# One-time setup on honeydew: a read-only Postgres role for bball-analysis.
#
#   sudo bash scripts/setup_db_reader.sh
#
# What it does, and why:
# 1. Creates role `bball_reader` (LOGIN, no password) and grants it the built-in
#    `pg_read_all_data` role: SELECT on every table, including tables bballagg
#    creates later, and nothing else (no INSERT/UPDATE/DELETE/DROP).
# 2. Lets Linux user `alex` log in as `bball_reader` over the local socket.
#    Postgres "peer" auth normally requires the DB role to equal the Linux user name;
#    a user map in pg_ident.conf adds the alex -> bball_reader pairing. A regex line
#    keeps every existing same-name login (postgres, alex) working as before.
# 3. Reloads Postgres (no restart; open connections are not dropped).
#
# Backups of both config files are written next to them first. Safe to re-run.
set -euo pipefail

MAP=bball
ROLE=bball_reader
LINUX_USER=alex

[[ $EUID -eq 0 ]] || { echo "run with sudo"; exit 1; }

psql_pg() { sudo -u postgres psql -v ON_ERROR_STOP=1 -Atq "$@"; }

HBA=$(psql_pg -c 'show hba_file')
IDENT=$(psql_pg -c 'show ident_file')
STAMP=$(date +%Y%m%d-%H%M%S)
echo "hba:   $HBA"
echo "ident: $IDENT"

# 1. role
psql_pg <<SQL
do \$\$ begin
  if not exists (select from pg_roles where rolname = '$ROLE') then
    create role $ROLE login;
  end if;
end \$\$;
grant pg_read_all_data to $ROLE;
SQL
echo "role $ROLE ready (pg_read_all_data)"

# 2. ident map
if ! grep -qE "^\s*$MAP\s" "$IDENT"; then
  cp -p "$IDENT" "$IDENT.bak-$STAMP"
  cat >> "$IDENT" <<EOF

# bball-analysis: same-name logins as before, plus $LINUX_USER -> $ROLE
$MAP    /^(.*)\$    \\1
$MAP    $LINUX_USER    $ROLE
EOF
  echo "added map '$MAP' to $IDENT (backup $IDENT.bak-$STAMP)"
else
  echo "map '$MAP' already in $IDENT"
fi

# 2b. use the map on the generic local peer line
if grep -qE "^local\s+all\s+all\s+peer\s*$" "$HBA"; then
  cp -p "$HBA" "$HBA.bak-$STAMP"
  sed -i -E "s/^(local\s+all\s+all\s+peer)\s*$/\1 map=$MAP/" "$HBA"
  echo "set map=$MAP on 'local all all peer' in $HBA (backup $HBA.bak-$STAMP)"
elif grep -qE "^local\s+all\s+all\s+peer\s+map=$MAP\s*$" "$HBA"; then
  echo "hba already uses map=$MAP"
else
  echo "ERROR: no plain 'local all all peer' line in $HBA; edit by hand. Lines:" >&2
  grep -E '^local' "$HBA" >&2
  exit 1
fi

# 3. reload and test
psql_pg -c 'select pg_reload_conf()' >/dev/null
sleep 1
psql_pg -c "select line_number, error from pg_hba_file_rules where error is not null" | grep . \
  && { echo "ERROR in pg_hba.conf, restore the backup" >&2; exit 1; } || true
sudo -u "$LINUX_USER" psql -d bballagg -U "$ROLE" -Atc \
  "select 'connected as ' || current_user || ', can read: ' || count(*) || ' tables'
   from information_schema.tables where table_schema = 'public'"
sudo -u "$LINUX_USER" psql -d bballagg -Atc "select 'alex still works: ' || current_user"
echo "done"
