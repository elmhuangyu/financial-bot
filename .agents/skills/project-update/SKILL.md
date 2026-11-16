---
name: project-update
description: >-
  Runbook for updating Python (uv) and web (pnpm) dependencies and toolchains
  in the financial-bot repository. Use when the user asks to update project
  dependencies, upgrade Python/Node/pnpm packages, or perform a routine
  dependency audit and bump.
---

# Project Update Runbook

Use this workflow when updating dependencies or runtime toolchains across the
`financial-bot` repository (Python core under `src/` + `pyproject.toml`, and
the web dashboard under `web/`).

Never edit lockfiles (`uv.lock`, `web/pnpm-lock.yaml`) by hand.

## 1. Python Dependencies (`pyproject.toml` & `uv.lock`)

1. **Preview available updates** without modifying files:
   ```bash
   uv lock --upgrade --dry-run
   ```
2. **Update Python dependencies**:
   - Routine updates within `pyproject.toml` constraints:
     ```bash
     uv lock --upgrade && uv sync
     ```
   - Targeted single-package upgrade:
     ```bash
     uv lock --upgrade-package <pkg> && uv sync
     ```
   - If bumping minimum version bounds in `pyproject.toml` (`dependencies` or
     `[dependency-groups].dev`), update `pyproject.toml` and then run:
     ```bash
     uv lock && uv sync
     ```
3. **Check Python toolchain & Ruff target**:
   - Keep `.python-version`, `pyproject.toml` (`project.requires-python`), and
     `[tool.ruff].target-version` aligned.
   - `just fmt` and `just lint` run `uvx ruff`, so verify formatting/linting
     still passes cleanly after Ruff or Python updates.

## 2. Web Dependencies (`web/` with `pnpm`)

Always use `pnpm` (never `npm` or `yarn`).

1. **Check outdated packages**:
   ```bash
   pnpm --prefix web outdated
   ```
2. **Update dependencies**:
   - Compatible updates within `web/package.json` ranges:
     ```bash
     pnpm --prefix web update
     ```
   - Major/latest updates (review breaking changes first for `vue`, `vite`,
     `hono`, `@hono/node-server`, `typescript`, `tailwindcss`, `daisyui`,
     `chart.js`, `vue-chartjs`, `mermaid`, `katex`, `oxlint`, `oxfmt`, etc.):
     ```bash
     pnpm --prefix web update --latest <pkg>
     ```
3. **Audit dependencies**:
   ```bash
   pnpm --prefix web audit --prod --audit-level=high
   ```
   (Run `pnpm --prefix web audit --audit-level=high` to include devDependencies.)

## 3. Verification

Run the full local suite after all updates:

```bash
just fmt
just lint
just build
just build-web
just test
```

Also smoke-check `web/` TypeScript types if TypeScript, Vue, or `@types/*`
packages were updated:

```bash
pnpm --prefix web exec vue-tsc --noEmit
```

Check `git status` and `git diff` to verify only expected files changed
(`pyproject.toml`, `uv.lock`, `web/package.json`, `web/pnpm-lock.yaml`, etc.),
and commit using conventional commits (e.g., `build(deps): ...`).
