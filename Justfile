# List all available recipes
default:
    @just --list

# Format code with ruff
fmt:
    uvx ruff format

# Lint with ruff and verify no hardcoded absolute paths
lint:
    uvx ruff check
    @echo "Checking for hardcoded absolute paths or file:// links..."
    @if git grep --untracked -nE 'file:///|/home/[a-zA-Z0-9_.-]+|/Users/[a-zA-Z0-9_.-]+' -- ':!Justfile' >/dev/null 2>&1; then \
        echo "ERROR: Hardcoded absolute paths or file:// URIs detected:"; \
        git grep --untracked -nE 'file:///|/home/[a-zA-Z0-9_.-]+|/Users/[a-zA-Z0-9_.-]+' -- ':!Justfile'; \
        exit 1; \
    fi

# Build
build:
    uv build

# Test
test:
    uv run python -m pytest

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
