#!/bin/sh
# Every invocation owns its project; cleanup never targets the dev environment.
set -eu
cd "$(dirname "$0")/.."
project="wishlists-bdd-$(date +%s)-$$"
cleanup() {
    docker compose -p "$project" -f compose.bdd.yaml down --volumes
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
docker compose -p "$project" -f compose.bdd.yaml up --build --abort-on-container-exit --exit-code-from bdd
