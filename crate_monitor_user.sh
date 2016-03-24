#!/bin/bash 
# RUN ON postgres host
user=$1
password=$2

sudo -u postgres psql << EOF

CREATE USER $user PASSWORD '$password';
ALTER USER $user SET SEARCH_PATH TO $user,pg_catalog;

CREATE SCHEMA $user AUTHORIZATION $user;

CREATE FUNCTION $user.f_select_pg_stat_activity()
RETURNS setof pg_catalog.pg_stat_activity
LANGUAGE sql
SECURITY DEFINER
AS \$\$
  SELECT * from pg_catalog.pg_stat_activity;
\$\$;

CREATE FUNCTION $user.f_select_pg_stat_replication()
RETURNS setof pg_catalog.pg_stat_replication
LANGUAGE sql
SECURITY DEFINER
AS \$\$
  SELECT * from pg_catalog.pg_stat_replication;
\$\$;

CREATE VIEW $user.pg_stat_replication
AS
  SELECT * FROM $user.f_select_pg_stat_replication();

CREATE VIEW $user.pg_stat_activity
AS
  SELECT * FROM $user.f_select_pg_stat_activity();

GRANT SELECT ON $user.pg_stat_replication TO $user;
GRANT SELECT ON $user.pg_stat_activity TO $user;

EOF
