# List all available recipes
default:
    @just --list

# Format code with ruff (Python) and oxfmt (JS/TS/Vue)
fmt:
    uvx ruff format
    pnpm --prefix web fmt

# Lint with ruff (Python) and oxlint (JS/TS/Vue) and verify no hardcoded absolute paths
lint:
    uvx ruff check
    pnpm --prefix web lint
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

# Run the fullstack web dashboard in dev mode (Hono API on :3000 + Vite UI on :5173)
dev:
    pnpm --prefix web dev

# Build the Vue web dashboard
build-web:
    pnpm --prefix web build

# Start the production web server (Hono API + SPA UI on :3000)
serve:
    pnpm --prefix web build
    pnpm --prefix web start

# Archive current data directory and recreate a clean data directory
archive name="":
    #!/usr/bin/env bash
    set -euo pipefail
    mkdir -p archived
    if [ -d data ]; then
        TIMESTAMP=$(date +%Y-%m-%d-%H-%M-%S)
        ARCHIVE_NAME="{{name}}"

        # If no name passed via CLI argument and running in an interactive terminal, prompt the user
        if [ -z "$ARCHIVE_NAME" ] && [ -t 0 ]; then
            read -r -p "Enter archive name/label (optional, press Enter to skip): " ARCHIVE_NAME
        fi

        TARGET_DIR="archived/${TIMESTAMP}"
        mv data "$TARGET_DIR"

        if [ -n "$ARCHIVE_NAME" ]; then
            echo "$ARCHIVE_NAME" > "$TARGET_DIR/name.txt"
            echo "Archived data to $TARGET_DIR [Name: $ARCHIVE_NAME]"
        else
            echo "Archived data to $TARGET_DIR"
        fi
    fi
    mkdir -p data/input data/tmp data/output
    echo "Created fresh data/ (input, tmp, output)"
