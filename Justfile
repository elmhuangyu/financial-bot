# List all available recipes
default:
    @just --list

# Format code with ruff
fmt:
    uvx ruff format

# Lint with ruff
lint:
    uvx ruff check

# Build
build:
    uv build

# Test
test:
    uv run pytest

# Archive current data directory and recreate a clean data directory
archive:
    #!/usr/bin/env bash
    set -euo pipefail
    mkdir -p archived
    if [ -d data ]; then
        TIMESTAMP=$(date +%Y-%m-%d-%H-%M-%S)
        mv data "archived/${TIMESTAMP}"
        echo "Archived data to archived/${TIMESTAMP}"
    fi
    mkdir -p data/input data/tmp data/output
    echo "Created fresh data/ (input, tmp, output)"
