# IBKR PortfolioAnalyst (Attribution & Risk Analysis) Specification

This specification defines the objective, required inputs, mathematical calculation methodologies (Brinson-Fachler attribution and Fama / CAPM risk decomposition), and deliverable output templates for generating the `IBKR PortfolioAnalyst Attribution & Risk Report` within `financial-bot`.

---

## 1. Objective & Scope

- **Business Purpose**: Provide rigorous, multi-period attribution analysis and modern portfolio theory (MPT) risk decomposition to explain the drivers of excess return (Active Return) and risk exposure relative to major market benchmarks.
- **Target Audience & Use Case**: 
  - Identifying whether portfolio outperformance/underperformance is driven by macro asset/sector allocation (Allocation Effect) vs. individual security selection (Selection Effect).
  - Quantifying systematic risk exposure (Beta), active managerial alpha (Jensen's Alpha), and risk-adjusted return efficiency (Sharpe, Sortino, Calmar, Information Ratio).
- **Scope & Institution Applicability**:
  - **Exclusively Tailored for IBKR PortfolioAnalyst**: This specification is specifically designed to parse and synthesize Interactive Brokers (IBKR) **PortfolioAnalyst multi-section CSV exports**, which uniquely contain native pre-computed Frongello-smoothed Brinson-Fachler attribution tables, MPT benchmark risk metrics, and time-series performance data.
  - **Other Brokerages / Raw Transaction Reports**: Statements from other financial institutions (e.g., Questrade, Schwab, Fidelity, Manulife) or raw transaction histories do **NOT** contain pre-computed Brinson or Fama metrics; analyzing non-IBKR reports requires separate custom calculation engines that reconstruct historical daily/monthly NAV series, cash flows, and benchmark lookups from scratch.
- **Target Deliverables**:
  - Markdown Report: `data/output/performance_attribution_report.md`
  - Structured Attribution CSV: `data/output/performance_attribution_brinson.csv`
  - Structured Risk Measures CSV: `data/output/risk_measures_fama.csv`
  - Symbol Contribution CSV: `data/output/symbol_performance_contribution.csv`

---

## 2. Required Input

### 2.1 Source Statements & Data Files (in `data/input/`)
- **Statement Types**: **Interactive Brokers PortfolioAnalyst CSV Export** (e.g., `PortfolioAnalyst.csv`).
- **Required Sections within the IBKR Export**:
  - `Key Statistics` (Period NAVs, cumulative return, MTM gains, net deposits)
  - `Performance Attribution vs. <Benchmark>` (Sector contribution and Brinson-Fachler allocation/selection effects)
  - `Risk Measures Benchmark Comparison` (Absolute and relative MPT metrics vs. SPXTR, VT, EFA)
  - `Historical Performance Benchmark Comparison` / `Time Period Benchmark Comparison` (Monthly/quarterly/annual returns)
  - `Performance by Symbol` (Holding weights, return, unrealized/realized P&L, and contribution to return)
- *Note: Non-IBKR statements lacking these specialized sections require a separate calculation pipeline.*

### 2.2 User Parameters & Assumptions (if applicable)
- **Primary Benchmark**: Default to S&P 500 Total Return (SPXTR) or designated primary benchmark.
- **Risk-Free Rate**: US 3-Month Treasury Bill yield corresponding to the analysis period.

---

## 3. Process

### 3.1 Data Parsing & Multi-Section Ingestion
- Ingest raw PortfolioAnalyst CSV tables across relevant sections:
  - `Key Statistics`
  - `Performance Attribution vs. <Benchmark>`
  - `Risk Measures Benchmark Comparison`
  - `Time Period Benchmark Comparison` / `Historical Performance Benchmark Comparison`
  - `Performance by Symbol` / `Open Position Summary`

### 3.2 Brinson-Fachler Performance Attribution Model
Decompose total active return $R_{\text{active}} = R_p - R_b$ into:
1. **Allocation Effect ($R_{\text{alloc}}$)**:
   $$R_{\text{alloc}} = \sum_{i} (w_i - W_i) \times (R_{Bi} - R_B)$$
   Where $w_i$ is portfolio weight in sector $i$, $W_i$ is benchmark weight, $R_{Bi}$ is sector benchmark return, and $R_B$ is total benchmark return.
2. **Selection Effect ($R_{\text{select}}$)**:
   $$R_{\text{select}} = \sum_{i} W_i \times (R_{pi} - R_{Bi}) + \text{Interaction Effect}$$
3. **Multi-Period Linking (Frongello Smoothing)**:
   Apply geometric multi-period compounding links (Andrew S. B. Frongello algorithm) to ensure multi-period active return reconciliation without compounding residual distortion.

### 3.3 Fama & CAPM Risk Decomposition
1. **Capital Asset Pricing Model (CAPM) Regression**:
   $$R_p - R_f = \alpha + \beta (R_m - R_f) + \epsilon$$
2. **Fama Return Decomposition**:
   - Total Excess Return = Return from Systematic Risk ($\beta \times [R_m - R_f]$) + Selectivity ($\alpha$).
   - Net Selectivity = $\alpha - \text{Diversification Premium}$.
3. **Risk-Adjusted Efficiency Metrics**:
   - Sharpe Ratio = $\frac{R_p - R_f}{\sigma_p}$
   - Sortino Ratio = $\frac{R_p - R_f}{\sigma_{\text{down}}}$
   - Information Ratio = $\frac{R_p - R_b}{\text{Tracking Error}}$
   - Calmar Ratio = $\frac{\text{Annualized Return}}{\text{Max Drawdown}}$

### 3.4 Standard Operating Procedure (SOP)
1. **Ad-hoc Processing**: Write extraction and calculation scripts in `data/tmp/<script_name>.py` and execute via `uv run`.
2. **Reconciliation**: Validate that total attribution sum equals portfolio cumulative return minus benchmark return within numerical precision tolerance.
3. **Report Generation**: Export finalized Markdown report and structured datasets into `data/output/`.

---

## 4. Output Template

### 4.1 Report Deliverable (`data/output/performance_attribution_report.md`)
- **Executive Summary**: Core active return, total allocation vs. selection split, and key risk profile summary.
- **Brinson-Fachler Attribution Breakdown**: Sector-level allocation vs. selection effects table with Frongello multi-period smoothing.
- **Fama / CAPM Risk & Factor Analysis**: Absolute and relative risk measures (Beta, Jensen's Alpha, Sharpe, Sortino, Downside Deviation, Drawdown recovery).
- **Symbol Contribution Ranking**: Top contributors and detractors by percentage contribution and dollar P&L.
- **Actionable Strategic Insights**: Portfolio balance, core-satellite optimization, and risk mitigation takeaways.
- **Assumptions & Disclaimers**: Risk-free rate convention and standard regulatory disclosures.

### 4.2 Data Deliverables
- `data/output/performance_attribution_brinson.csv`: Complete sector allocation and selection effects.
- `data/output/risk_measures_fama.csv`: Multi-benchmark comparative risk and CAPM statistics.
- `data/output/symbol_performance_contribution.csv`: Per-symbol return, weight, and profit contribution data.
