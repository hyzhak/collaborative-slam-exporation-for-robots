#!/usr/bin/env bash
set -e

# podman-compose -f docker-compose.yml -f docker-compose.integration.yaml down -v || true
podman-compose -f docker-compose.yml up -d
podman-compose -f docker-compose.yml -f docker-compose.integration.yaml run --rm integration_test
STATUS=$?
exit $STATUS
