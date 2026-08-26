# Portfolio Monte Carlo Simulation Report Specification

This specification defines the objective and scope, user-provided inputs, mathematical modeling methodologies, standard operating procedure (SOP), and deliverable output templates for generating the Monte Carlo Simulation Report within `financial-bot`.

---

## 1. Objective & Scope

- **Business Purpose**: Provide stochastic forward-looking projections for multi-asset portfolios using empirical real-market return and covariance distributions calibrated from historical market data.
- **Target Audience & Use Case**: Long-term asset allocation assessment, multi-horizon stress testing, sequence-of-returns risk, interim peak-to-trough drawdown evaluation, and probabilistic loss assessment for portfolios containing equities, index funds, and digital assets.
- **Target Deliverables**:
  - Markdown Report: `data/output/monte_carlo_report.md`
  - Structured Data Deliverables:
    - `data/output/monte_carlo_summary.csv`
    - `data/output/monte_carlo_horizon_risks.csv`
    - `data/output/monte_carlo_percentile_trajectories.csv`
    - `data/output/monte_carlo_asset_stats.csv`
    - `data/output/monte_carlo_asset_correlations.csv`
  - Interactive Web Dashboard: `data/output/ui_manifest.json` (A2UI schema)

---

## 2. Required Input

Defines what the **user** must provide to the system prior to simulation execution.

### 2.1 Source Statement / Portfolio Description (in `data/input/`)
- **Portfolio Configuration File**: Text or CSV format (e.g. `data/input/portfolio.txt` or `data/output/normalized_holdings.csv`).
- **Required Fields**:
  - Total portfolio baseline or dollar capital (e.g. `$900,000 USD`).
  - Target asset allocation weights (e.g. `30% GOOG, 40% SP500, 25% NASDAQ100, 5% BTC`).

### 2.2 User Parameters & Assumptions
- **Historical Calibration Window**: Start date for market data calibration (e.g. `2021-01-01` to align with modern institutional crypto trading regimes).
- **Simulation Parameters**:
  - Number of simulation paths $N$ (e.g. $N = 1,000$).
  - Time horizon $T$ in years (e.g. $T = 30$).
  - Rebalancing frequency (e.g. annual rebalancing).
  - Trading steps per year $dt = 1/252$.

---

## 3. Process

Defines the complete end-to-end technical, mathematical, and simulation workflow executed by the system.

### 3.1 Data Ingestion & Hybrid Asset Parameter Calibration
1. Parse portfolio configuration and normalize ticker representations (e.g., `GOOG`, `SP500 -> SPY`, `NASDAQ100 -> QQQ`, `BTC -> BTC-USD`).
2. **Hybrid Historical Ingestion Strategy**:
   - **Broad-Market Anchors (SP500, Nasdaq 100)**: Query longest available historical return series (`period='max'`, ~30+ years) to incorporate full macroeconomic cycles (including the 2000 Dot-com crash, 2008 GFC, and 2020 COVID shock).
   - **High-Beta Equities & Digital Assets (GOOG, BTC-USD)**: Query modern institutional era data (`start='2021-01-01'`) and apply an explicit conservative discount/haircut (e.g. **-8.0%**) to eliminate short-term bull-run drift bias.
   - **Cross-Asset Correlation Matrix ($\mathbf{R}$)**: Calibrate empirical correlations using overlapping modern daily returns (post-2021) to capture real-world co-movements between crypto, mega-cap tech, and index funds.
3. Compute daily discrete return series:
   $$R_{i, t} = \frac{P_{i, t} - P_{i, t-1}}{P_{i, t-1}}$$
4. Calculate individual asset statistical parameters:
   - **Annualized Expected Return ($\mu_i$)**:
     $$\mu_i = 252 \times \mathbb{E}[R_{i, t}] - \text{Haircut}_i$$
   - **Annualized Volatility ($\sigma_i$)**:
     $$\sigma_i = \sqrt{252} \times \operatorname{Std}(R_{i, t})$$
   - **Annualized Covariance Matrix ($\boldsymbol{\Sigma}$)**:
     $$\boldsymbol{\Sigma}_{ij} = \sigma_i \sigma_j R_{ij}$$
   - **Empirical Correlation Matrix ($\mathbf{R}$)**:
     $$R_{ij} = \frac{\operatorname{Cov}(\mathbf{R}_{i, t}, \mathbf{R}_{j, t})}{\operatorname{Std}(\mathbf{R}_{i, t})\operatorname{Std}(\mathbf{R}_{j, t})}$$
   - **Portfolio Aggregate Expected Return and Volatility**:
     $$\mu_{\text{port}} = \mathbf{w}^T \boldsymbol{\mu}, \quad \sigma_{\text{port}} = \sqrt{\mathbf{w}^T \boldsymbol{\Sigma} \mathbf{w}}$$

### 3.2 Correlated Multivariate Geometric Brownian Motion (Cholesky + GBM)
1. Perform Cholesky factorization on the empirical correlation matrix $\mathbf{R}$:
   $$\mathbf{R} = \mathbf{L} \mathbf{L}^T$$
   where $\mathbf{L}$ is the lower triangular matrix.
2. For each simulation path $k \in \{1, \dots, N\}$ and each discrete trading day step $\Delta t = 1/252$:
   - Generate independent standard normal random shock vector $\mathbf{Z}_{\text{uncorr}} \sim \mathcal{N}(\mathbf{0}, \mathbf{I})$.
   - Induce cross-asset empirical correlation:
     $$\mathbf{Z}_{\text{corr}} = \mathbf{L} \mathbf{Z}_{\text{uncorr}}$$
   - Update individual asset values using the exact SDE solution under Ito's Lemma:
     $$S_{i, t+\Delta t} = S_{i, t} \exp\left( \left(\mu_i - \frac{1}{2}\sigma_i^2\right)\Delta t + \sigma_i \sqrt{\Delta t} Z_{\text{corr}, i} \right)$$
3. Apply periodic rebalancing to restore target allocation weights $\mathbf{w}$ at designated step intervals (e.g. annual rebalancing at $\text{step} \pmod{252} = 0$).

### 3.3 Risk, Loss Probabilities & Downside Analytics
1. **Multi-Horizon Loss Probability Matrix**:
   For investment horizons $h \in \{1, 2, 3, 5, 7, 10, 15, 20, 25, 30\}$ years:
   $$\mathbb{P}(\text{Loss}_h) = \frac{1}{N} \sum_{k=1}^N \mathbb{I}\left( V_k(h) < V_0 \right)$$
   Compute downside percentiles ($P_5$, $P_{10}$) and cumulative downside returns.
2. **Worst-Case & Extreme Downside Tail Tracking**:
   - At each milestone year and at terminal horizon $T$, record both the **5th percentile downside tail ($P_5$)** and the **simulated minimum path ($\text{Min}$)**:
     $$\text{Min}(t) = \min_{1 \le k \le N} V_k(t), \quad P_5(t) = \text{Percentile}(V(t), 5)$$
3. **Maximum Drawdown (MDD) Tracking**:
   For each trajectory $k$, track running peak $M_k(t) = \max_{0 \le \tau \le t} V_k(\tau)$ and peak-to-trough drop:
   $$\text{MDD}_k = \max_{0 \le t \le T} \left( \frac{M_k(t) - V_k(t)}{M_k(t)} \right)$$
   Compute median MDD, mean MDD, and worst-case MDD across all $N$ paths.
4. **Compound Annual Growth Rate (CAGR) Percentiles**:
   $$\text{CAGR}_k = \left(\frac{V_k(T)}{V_0}\right)^{1/T} - 1$$

### 3.4 Standard Operating Procedure (SOP)
1. **Model Execution**: Run `src.core.monte_carlo.MonteCarloEngine` via ad-hoc runner or permanent pipeline.
2. **Output CSV Generation**: Export summary statistics, horizon risk matrices, and trajectory tables (including `min_usd`, `p5_usd`, `p10_usd`, `p25_usd`, `p50_median_usd`, `p75_usd`, `p90_usd`, `mean_usd`) to `data/output/`.
3. **Markdown Report Generation**: Render `data/output/monte_carlo_report.md` following Section 4.
4. **Interactive Dashboard Manifest (`data/output/ui_manifest.json`)**:
   - **Zero Hardcoding Rule**: All KPI values, badges, and card subtexts MUST be dynamically derived from the generated output CSVs. Never hardcode mock/static numbers.
   - **Full Spectrum Trajectory Chart**: The 30-year Growth Cone line chart must include the full distribution from **Optimistic (P90)** down to **Conservative (P10)**, **Downside Tail (P5)**, and **Simulated Worst Path (Min)**.

---

## 4. Output Template

Defines the publication-grade deliverables generated in `data/output/`.

### 4.1 Report Deliverable (`data/output/monte_carlo_report.md`)

```markdown
# Portfolio Monte Carlo Simulation Report (<N> Paths, <T>-Year Horizon)

**Portfolio Baseline**: $<Initial_Value_USD> USD  
**Historical Calibration Window**: <Start_Date> to <End_Date>  
**Simulation Scale**: <N> Iterations $\times$ <T> Years with Correlated GBM (Cholesky) & Annual Rebalancing  
**Deliverable CSVs**:
- [`monte_carlo_summary.csv`](monte_carlo_summary.csv)
- [`monte_carlo_horizon_risks.csv`](monte_carlo_horizon_risks.csv)
- [`monte_carlo_percentile_trajectories.csv`](monte_carlo_percentile_trajectories.csv)
- [`monte_carlo_asset_stats.csv`](monte_carlo_asset_stats.csv)
- [`monte_carlo_asset_correlations.csv`](monte_carlo_asset_correlations.csv)

---

## 1. Executive Summary
- **Initial Portfolio Net Worth**: $<Initial_Value_USD> USD
- **Expected Annual Return & Volatility**: <Ann_Return>% / <Ann_Vol>%
- **Short-Term Downside Risk (1-Year Loss Probability)**: <1Y_Loss_Prob>% (5th percentile: $<1Y_P5_USD>, <1Y_P5_Return>%)
- **Maximum Drawdown Exposure (Median / Worst Crash)**: <Median_MDD>% / <Worst_MDD>%
- **Terminal Outcomes (Median P50 / Conservative P10)**: $<Median_Final_USD> (<Median_CAGR>%) / $<P10_Final_USD> (<P10_CAGR>%)

---

## 2. Multi-Horizon Loss Probability & Downside Analysis
| Investment Horizon | Loss Probability (< $V_0) | 5th Percentile (Downside Value) | Downside Cum. Return | Median Value (USD) | Median CAGR |
| :--- | :---: | :---: | :---: | :---: | :---: |
<!-- Dynamically render horizon matrix -->

---

## 3. Growth Milestones (Trajectory Percentiles)
| Milestone | Simulated Worst (Min) | Downside Tail (P5) | Conservative (P10) | Median (P50) | Optimistic (P90) | Mean |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
<!-- Dynamically render milestones including Min and P5 worst cases -->

---

## 4. Asset Allocation & Empirical Covariance Matrix (Post-2021)
### 4.1 Asset Parameters (Post-2021 Calibration)
| Symbol | Asset Name | Target Weight | Starting Capital (USD) | Annualized Expected Return ($\mu_i$) | Annualized Volatility ($\sigma_i$) | Calibration Rationale |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
<!-- Dynamically iterate assets -->
| **<Symbol>** | <Asset_Name> | <Weight>% | $<Starting_USD> | **<Expected_Return>%** | **<Volatility>%** | <Rationale> |
| **Total** | **Portfolio Weighted** | **100.0%** | **$<Total_USD>** | **<Portfolio_Return>%** | **<Portfolio_Vol>%** | Composite Calibration |

### 4.2 Empirical Asset Correlation Matrix ($\mathbf{R}$)
| Asset | <Symbol_1> | <Symbol_2> | ... |
| :--- | :---: | :---: | :---: |
<!-- Dynamically render correlation matrix -->

```mermaid
pie title Initial Target Portfolio Allocation
    "<Asset_1>" : <Weight_1>
    "<Asset_2>" : <Weight_2>
```

---

## 5. Critical Risk & Downside Takeaways
- Discussion on short-term loss probabilities vs long-term compounding.
- Inevitability of interim peak-to-trough drawdowns during long-term holding.
- Downside tail analysis (P5 and Min paths) and emotional resilience requirements.
- Rebalancing volatility harvesting benefits.

---

## 6. Model Assumptions & Disclaimers
- Correlated Multivariate Geometric Brownian Motion formulation ($dS_i = \mu_i S_i dt + \sigma_i S_i dW_i$ via $\mathbf{Z}_{\text{corr}} = \mathbf{L} \mathbf{Z}_{\text{uncorr}}$).
- Standard financial simulation disclaimer.
```

### 4.2 Data Deliverables
- `data/output/monte_carlo_summary.csv`
- `data/output/monte_carlo_horizon_risks.csv`
- `data/output/monte_carlo_percentile_trajectories.csv`
- `data/output/monte_carlo_asset_stats.csv`
- `data/output/monte_carlo_asset_correlations.csv`
- `data/output/ui_manifest.json` (A2UI interactive dashboard manifest with dynamic KPIs and Growth Fan datasets)
