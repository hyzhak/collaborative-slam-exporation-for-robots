#!/usr/bin/env bash
set -e

podman-compose -f docker-compose.yml -f docker-compose.integration.yaml down -v || true
podman-compose -f docker-compose.yml -f docker-compose.integration.yaml \
  up --build --exit-code-from integration_test integration_test
