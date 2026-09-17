#!/bin/sh
# On a freshly created network, the embedded DNS resolver at
# 127.0.0.11 is not always answering yet the instant a container starts, even though
# `depends_on: postgres: condition: service_healthy` already held. A datasource's first
# connection attempt can then throw UnknownHostException before the resolver catches up,
# and neither spring-boot's HikariCP pool nor spring-traditional's
# DriverManagerDataSource retries on its own, so the app crashed and stayed unhealthy
# forever. `getent hosts` costs nothing once DNS is up (the normal case, first try) and
# bounds the wait when it is not.
#
# Shared by modules/spring-boot/Dockerfile and modules/spring-traditional/Dockerfile,
# the two apps that resolve `postgres` by hostname over a fresh JDBC connection at boot.
# A prior version of this fix was duplicated verbatim in both CMD lines; kept in one file
# so a future change to the retry count or interval has one place to land, and so the
# retries stay within the margin docker-compose.yml's healthcheck retries budget for it.

set -eu

host="${1:-postgres}"
attempts="${2:-30}"
i=1
while [ "$i" -le "$attempts" ]; do
    if getent hosts "$host" >/dev/null 2>&1; then
        exit 0
    fi
    echo "[wait-for-postgres] name resolution for '$host' not ready yet, retry $i/$attempts"
    i=$((i + 1))
    sleep 1
done

echo "[wait-for-postgres] '$host' never resolved after $attempts attempts; proceeding anyway so the real error surfaces" >&2
exit 0
