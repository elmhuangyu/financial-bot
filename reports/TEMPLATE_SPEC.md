# <Report Title> Specification

This specification defines the objective, user-provided inputs, calculation and processing methodologies, and deliverable output templates for generating the `<Report Name>` within `financial-bot`.

---

## 1. Objective & Scope

- **Business Purpose**: [Clear explanation of the financial analysis or planning question this report addresses]
- **Target Audience & Use Case**: [e.g., Strategic portfolio rebalancing, annual tax optimization, retirement readiness assessment]
- **Target Deliverables**:
  - Markdown Report: `data/output/<report_name>_report.md`
  - Structured Data Deliverable: `data/output/<report_name>_data.csv`

---

## 2. Required Input

Defines what the **user** must provide to the system prior to report generation.

### 2.1 Source Statements & Data Files (in `data/input/`)
- **Statement Types**: [e.g., Brokerage monthly statements, CSV position exports, 401(k) / RRSP benefit summaries, bank cash summaries, crypto exchange exports]
- **Required Coverage**: [e.g., All active taxable and registered accounts, uninvested cash / settlement balances, security quantities, cost basis, and valuation dates]
- **Institutions**: [e.g., Interactive Brokers, Questrade, Manulife, Fidelity, Schwab, etc.]
- *Note: Statement formats and column headers naturally vary across institutions; parsers in Process handle standardization.*

### 2.2 User Parameters & Assumptions (if applicable)
- **Financial Profile / Goals**: [e.g., Target retirement age, annual retirement spending goal, country / tax residency, risk tolerance profile]
- **Custom Asset Mapping / Overrides**: [e.g., Descriptions of unlisted employer retirement funds, private equity holdings, or custom benchmark proxies]

---

## 3. Process

Defines the complete end-to-end technical, mathematical, and enrichment workflow executed by the system.

### 3.1 Multi-Source Ingestion & Data Standardization
- Parse diverse raw statement formats from `data/input/`.
- Extract raw positions, settlement cash balances, and link account identifiers to canonical tax categories (`Taxable`, `Tax-Free`, `Tax-Deferred`) and account owners.

### 3.2 Dynamic Market Data Enrichment
- **Public Securities**: Query external market APIs (e.g., `yfinance`) dynamically to resolve legal security names, asset classes, GICS sectors, industries, and quote types without static ticker lists.
- **Fund Constituent Look-Through**: Retrieve dynamic sector weightings and top constituent holdings for ETFs and mutual funds.
- **FX Normalization**: Fetch current or statement-date exchange rates (e.g., USD/CAD) to convert all values into standard base currencies.
- **Unlisted / Private Assets**: Map unlisted institutional funds to representative benchmark proxies based on user configuration.

### 3.3 Mathematical Models & Calculation Logic
- Explicit deterministic formulas for all metrics and aggregations:
  - Multi-dimensional roll-ups (by Asset Class, Sector, Tax Regime, Account Owner).
  - Look-through sector decomposition and consolidated single-stock concentration algorithms.
  - Return calculations (TWRR, MWRR/IRR, return on cost).
  - Projections / simulations (cash flow forecasting, withdrawal sustainability, Monte Carlo simulations).

### 3.4 Reconciliation & Quality Control
- **Account NAV Cross-Check**: Ensure the sum of normalized holdings matches raw statement Net Asset Values (NAVs) within tolerance (e.g., $\pm \$1.00$).
- **Data Integrity Audit**: Flag unresolved tickers or unclassified asset lines.

### 3.5 Standard Operating Procedure (SOP)
1. **Ad-hoc Processing**: Write and execute processing scripts in `data/tmp/<script_name>.py` via `uv run`.
2. **Verification**: Verify terminal execution logs and reconciliation checks.
3. **Artifact Generation**: Export final Markdown report and structured datasets to `data/output/`.
4. **Promotion (Optional)**: If parsing or calculation logic is generic and reusable, promote to `src/core/` with comprehensive unit tests under `tests/`.

---

## 4. Output Template

Defines the publication-grade deliverables generated in `data/output/`.

### 4.1 Report Deliverable (`data/output/<report_name>_report.md`)

```markdown
# <Report Title> (<YYYY-MM-DD>)

**Statement Date / Period**: <Date_or_Period>  
**Generated At**: <Timestamp_UTC>  
**FX Rate Assumed**: 1 CAD = <CAD_TO_USD_Rate> USD (1 USD = <USD_TO_CAD_Rate> CAD)  
**Deliverable Artifacts**: [`<output_data>.csv`](<output_data>.csv)  

---

## 1. Executive Summary
- High-level portfolio metrics (Net Worth, Asset Class splits, Key progress metrics)
- Core quantitative findings and high-level takeaway

---

## 2. Detailed Breakdown & Visualizations
- Multi-dimensional summary tables (Asset Class, Sector Look-Through, Tax Treatment, Ownership)
- Visual charts (Mermaid diagrams, scenario projections)

---

## 3. Key Observations & Actionable Recommendations
- Objective observations derived strictly from verified execution results
- Rebalancing, optimization, or risk mitigation recommendations

---

## 4. Assumptions & Disclaimers
- Explicit list of all modeled financial parameters and assumptions
- Standard financial advice disclaimer
```

### 4.2 Data Deliverables
- Output CSV / JSON paths (e.g., `data/output/<report_name>_summary.csv`) and schemas.
