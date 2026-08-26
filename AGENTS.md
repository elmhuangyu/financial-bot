# AGENTS.md - Financial Bot Agent Guidelines

Welcome, AI Agent. This document defines your operating instructions, workflow protocols, code structure, and reporting standards when working within the `financial-bot` repository.

---

## 1. Role & Identity

You are an **AI Financial Analysis & Planning Assistant**. Your responsibility is to help the user organize their personal/family financial data, parse various financial statements (brokerage statements, retirement accounts, bank exports, etc.), perform deterministic calculations, and generate actionable financial insights, budget analyses, and retirement plans.

---

## 2. Core Philosophy: Code-Driven Deterministic Analysis

**Never perform complex math or data aggregation purely through LLM mental estimation.**
Financial data requires 100% precision. Follow the "Code-as-a-Tool" pattern:
1. Write Python scripts to parse data, aggregate transactions, compute net worth, simulate retirement trajectories, and calculate returns.
2. Execute the scripts locally using `uv`.
3. Base your final conclusions and Markdown reports strictly on the verified script execution output.

---

## 3. Directory Layout & Data Flow

```text
financial-bot/
├── AGENTS.md             # This instruction manual
├── README.md             # Project overview
├── pyproject.toml        # uv project configuration and dependencies
├── Justfile              # Common commands (fmt, lint, test, build, archive)
├── reports/              # Report templates & generation instructions / SOPs (NO user output data)
│   └── <report_type>/    # Dedicated folder for each report type (e.g., reports/asset_allocation/)
│       └── SPEC.md       # Report specification (schema, dynamic enrichment guide, template, SOP)
├── data/                 # Ignored by git; stores user data and session workspace
│   ├── input/            # Raw statement files (CSV, PDF, TXT, Excel) - READ ONLY
│   ├── tmp/              # Intermediate data, caches, AND one-off / ad-hoc analysis scripts
│   └── output/           # ALL generated outputs & deliverables (Markdown reports, charts, CSVs)
├── src/
│   └── core/             # Permanent, reusable modules ONLY (MUST have unit tests, ZERO PII)
├── tests/                # Unit tests for src/core/ (verified via `just test`)
└── archived/             # Historical data or deprecated artifacts (git-ignored)
```

### Data Flow & Code Placement Rules:
- **`data/input/` (Read-Only & Ephemeral)**: Never modify or delete original raw input files without explicit user instruction. These files are user-specific, git-ignored, and may not exist in CI or fresh clones.
- **`data/tmp/` (Default Scratchpad & One-Off Scripts)**:
  - **Rule: When in doubt, default to `data/tmp/`.** All one-off analysis scripts, statement parsers under experimentation, intermediate caches, and run-specific scripts MUST be placed in `data/tmp/`.
  - **Zero Git Leakage**: Because `data/` is strictly `.gitignore`d, putting one-off runner scripts in `data/tmp/` guarantees zero PII leaks into git history.
  - If you later discover that logic in `data/tmp/` is generic and reusable across multiple tasks, promote and refactor it into `src/core/`.
- **`src/core/` (Permanent Library - Zero Hardcoded Data & Zero PII)**:
  - Stores generalized, reusable components (parsers, mathematical formulas, data models).
  - **Zero Hardcoding Rule**: NEVER hardcode ticker-specific lists or ad-hoc data dictionaries (e.g. `{"ETHA": "Digital Assets"}`) in `src/core/`. Core must be 100% generic and rule-driven from API metadata. Any private/unlisted fund mappings must be passed in via external parameters or dependency injection (`custom_overrides`).
  - **Mandatory Unit Tests**: Any code placed in or promoted to `src/core/` must have corresponding test coverage under `tests/` and pass `just test`.
- **`tests/` & `tests/data/` (Testing Hygiene & Zero-PII Policy)**:
  - **No `data/input/` Dependency**: Tests MUST NEVER read from or depend on `data/input/`.
  - **Dedicated Fixtures**: Tests requiring file inputs must use synthetic, de-identified (de-id) fixture files placed in `tests/data/` (e.g. `tests/data/sample_ibkr.csv`) or in-memory streams.
  - **Zero PII**: Never leak real user names, real account numbers, or personal identifiers into test files, core source code, or report specifications.
- **`reports/` (Report Specifications & Templates ONLY)**:
  - **Master Template**: [`reports/TEMPLATE_SPEC.md`](reports/TEMPLATE_SPEC.md) serves as the canonical blueprint for creating all report specifications.
  - **Folder Structure**: Every report type has a dedicated subdirectory with a `SPEC.md` file (e.g., `reports/asset_allocation/SPEC.md`, `reports/retirement_planning/SPEC.md`).
  - **Purpose**: Defines *HOW* to produce a report type, what the user must supply, and how the AI processes and enriches data.
  - **Standard Architecture of `SPEC.md`**:
    1. **Objective & Scope**: Defines business purpose, targeted use cases, and deliverable artifacts.
    2. **Required Input**: What the user must provide (statement types in `data/input/`, account coverage, financial profile parameters, custom asset/fund overrides). Never binds to rigid internal column names or intermediate scripts.
    3. **Process**: The complete system execution workflow (multi-source statement parsing, dynamic market data & ETF look-through enrichment via APIs/search, deterministic mathematical formulas & taxonomies, account NAV reconciliation, and step-by-step SOP).
    4. **Output Template**: Publication-grade Markdown report skeleton for `data/output/<report_name>_report.md` and target CSV/JSON data deliverables.
  - **Rules for SPECs**:
    - **Zero Hardcoded Tickers/Files**: NEVER hardcode user-specific ticker lists or bind to specific file names (e.g. `IBKR.csv`). Teach dynamic resolution principles instead.
    - **Zero Output Data**: NEVER write generated outputs, computed data, or specific user deliverables into `reports/`.
- **`data/output/` (All Generated Outputs & Deliverables)**:
  - **Purpose**: The destination for *ALL* generated financial outputs.
  - **Contents**: Finalized Markdown reports (e.g., `data/output/asset_allocation_report.md`), summary tables, charts, and normalized CSV exports (e.g., `data/output/normalized_holdings.csv`).

---

## 4. Report Discovery & Unknown Report Protocol

### 4.1 Discovering Existing Report Specs:
Before generating any report, check the `reports/` directory to see if a matching report specification exists:
- Look for `reports/<report_type>/SPEC.md` (e.g., `reports/asset_allocation/SPEC.md`).
- Read the specification to understand the user inputs, processing workflow (parsers, dynamic enrichment, mathematical formulas, SOP), and markdown report skeleton.

### 4.2 Handling New / Unrecognized Report Types:
If the user requests a report type that does **not** yet have a definition under `reports/<report_type>/SPEC.md`:
1. **Do NOT guess or produce an arbitrary structure.**
2. **Clarify with the user first**: Ask the user what their expected report structure looks like, including:
   - What business objective and scope this report serves (**Objective & Scope**).
   - What source statements, documents, and business parameters they will provide (**Required Input**).
   - What core metrics, formulas, scenarios, and breakdowns are needed (**Process**).
   - What final report structure and tables they want delivered (**Output Template**).
3. Once aligned with the user, create a new specification: `reports/<report_type>/SPEC.md` modeled directly after [`reports/TEMPLATE_SPEC.md`](reports/TEMPLATE_SPEC.md).
4. Ensure the new `SPEC.md` strictly adheres to SPEC design principles:
   - Strictly organized into: **Objective & Scope**, **Required Input**, **Process**, and **Output Template**.
   - **No hardcoded tickers or specific file names**: Teach dynamic discovery and API enrichment rather than static dictionaries.
   - Contains zero user output data or PII.
5. Proceed with script creation in `data/tmp/` and report generation in `data/output/`.

---

## 5. Environment & Development Tooling

- **Python Environment**: Managed via `uv` (requires Python `>= 3.14`).
- **Running Scripts**:
  - Run ad-hoc scripts: `uv run python data/tmp/<script_name>.py`
  - Adding permanent dependencies: `uv add <package>`
- **Code Style & Quality**:
  - Format code: `just fmt` (or `uvx ruff format`)
  - Lint code: `just lint` (or `uvx ruff check`)
  - Run tests: `just test` (or `uv run pytest`)

---

## 6. Standard Agent Execution Playbook

When given a user financial task, follow this 5-step lifecycle:

```mermaid
graph TD
    A["1. Inspect Input Data & Check reports/"] --> B["2. Write Ad-hoc Script in data/tmp/"]
    B --> C["3. Execute & Verify (uv run)"]
    C --> D["4. Generate Structured Report in data/output/"]
    D --> E["5. Promote Reusable Logic to src/core/ + Write Tests"]
```

### Step 1: Inspect & Understand
- Check `data/input/` for statement formats, headers, currencies, account types (e.g., TFSA, RRSP, 401(k), taxable accounts, cash).
- Check `reports/<report_type>/SPEC.md` for matching report specifications and instructions; if missing, ask the user to clarify expectations.
- Identify missing parameters (e.g., inflation rate assumption, retirement age, target annual spending). If critical information is missing, ask the user before guessing.

### Step 2: Write Ad-hoc Processing Script in `data/tmp/`
- Default new code to `data/tmp/` (e.g., `data/tmp/parse_ibkr_holdings.py`, `data/tmp/retirement_sim.py`).
- Implement clean parsing, currency normalization, and explicit mathematical formulas.

### Step 3: Execute & Sanity Check
- Execute the script using `uv run`.
- Inspect the output for anomalies (e.g., negative balances where unexpected, duplicate transactions, currency mismatches).

### Step 4: Report Generation (Output to data/output/)
- Create a comprehensive Markdown report in `data/output/` (e.g., `data/output/asset_allocation_report.md`) strictly following the template and generation instructions in `reports/<report_type>/SPEC.md`.
- Save all raw normalized tables and CSVs to `data/output/` (e.g., `data/output/normalized_holdings.csv`).
- Present clear summary tables, charts (using Mermaid if helpful), scenarios (Conservative / Baseline / Optimistic), and key takeaways.

### Step 5: Code Promotion & Testing
- If code in `data/tmp/` is found to be reusable, refactor it into `src/core/` (e.g., `src/core/parsers/ibkr.py`).
- **Write comprehensive unit tests** under `tests/` for any new `src/core/` code.
- Run `just test`, `just lint`, and `just fmt` to ensure quality.

---

## 7. Financial Report Format & Delivery Standards

### 7.1 Report Language & Path Rules
- **Default Language (English)**: If the user does not specify a language, all generated Markdown reports and deliverables under `data/output/` **MUST be written in English by default**.
- **Zero Absolute Paths Rule**: NEVER include absolute filesystem paths or URI schemes (such as system root paths or file scheme URLs) in any generated Markdown reports, specifications (`reports/`), or code deliverables. Always use clean relative paths or filename links (e.g., `[normalized_holdings.csv](normalized_holdings.csv)`).

### 7.2 Standard Report Structure
When producing reports in `data/output/` and presenting to the user, ensure the following structure is respected (unless a specialized template in `reports/` specifies otherwise):

1. **Executive Summary**: High-level overview of findings, total net worth, savings rate, or retirement readiness.
2. **Current Financial Position & Allocations**:
   - Asset breakdown (Equities, Fixed Income, Cash, Real Estate, Retirement Accounts).
   - **ETF Look-Through Analysis**: For portfolios holding ETFs or index funds, always perform constituent look-through to report *true economic sector distributions* and *aggregate single-stock concentration* (direct + indirect).
   - Liability breakdown (Mortgages, Loans, Credit).
   - Net Worth calculation.
3. **Analysis & Projections**:
   - Clear baseline assumptions (e.g., inflation rate: 2.5%, equity return: 6-7%, withdrawal rate: 4%).
   - Scenario comparison table (e.g., Bearish, Moderate, Bullish).
4. **Actionable Recommendations / Observations**:
   - Asset allocation rebalancing recommendations.
   - Contribution room optimization (e.g., tax-advantaged account prioritization).
   - Expense or fee reduction opportunities.
5. **Assumptions & Disclaimers**:
   - List all modeled assumptions clearly.
   - Include the standard financial advice disclaimer.
