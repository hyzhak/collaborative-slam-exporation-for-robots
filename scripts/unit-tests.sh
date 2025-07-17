#!/usr/bin/env bash
set -e

podman-compose -f docker-compose.unit.yaml \
  up --build --exit-code-from unit_test unit_test
