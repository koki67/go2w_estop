#!/bin/bash
export DOCKER_API_VERSION=1.43

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec docker compose -f "$SCRIPT_DIR/docker-compose.yml" "$@"
