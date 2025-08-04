#!/usr/bin/env bash
set -e

echo "Running unit tests..."
bash scripts/unit-tests.sh

echo "Running integration tests..."
bash scripts/integration-tests.sh

echo "Running Ruff lint (check only)..."
podman-compose -f docker-compose.unit.yaml run --rm lint

echo "Validation complete."
