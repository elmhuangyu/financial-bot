# Markowitz Efficient Frontier & Mean-Variance Optimization Report Specification

This specification defines the objective and scope, user-provided inputs, mathematical modeling methodologies, standard operating procedure (SOP), and deliverable output templates for generating the Markowitz Efficient Frontier & Portfolio Optimization Report within `financial-bot`.

---

## 1. Objective & Scope

- **Business Purpose**: Provide rigorous Modern Portfolio Theory (MPT) mean-variance optimization analysis to identify mathematically optimal risk-return trade-offs, pinpoint the Global Minimum Variance (GMV) and Maximum Sharpe Ratio (Tangency) portfolios, trace the continuous Efficient Frontier curve, and quantify the "efficiency gap" of the investor's current asset allocation.
- **Target Audience & Use Case**: Strategic asset allocation, portfolio rebalancing, capital allocation line (CAL) risk budgeting, diversification benefit evaluation, and benchmarking current holdings against theoretical risk-adjusted efficiency limits.
- **Target Deliverables**:
  - Markdown Report: `data/output/efficient_frontier_report.md`
  - Structured Data Deliverables:
    - `data/output/efficient_frontier_summary.csv`
    - `data/output/efficient_frontier_points.csv`
    - `data/output/efficient_frontier_allocations.csv`
    - `data/output/efficient_frontier_cal.csv`
  - Interactive Web Dashboard: `data/output/ui_manifest.json` (A2UI schema, on-demand)

---

## 2. Required Input

Defines what the **user** must provide to the system prior to optimization execution.

### 2.1 Source Statement / Portfolio Description (in `data/input/`)
- **Portfolio Configuration or Statement**: CSV, JSON, or text format (e.g., `data/input/portfolio.txt` or normalized holdings from `data/output/normalized_holdings.csv`).
- **Required Fields**:
  - Asset identifiers / tickers (e.g. `SPY`, `QQQ`, `BND`, `GLD`, `BTC-USD`).
  - Current portfolio weights or dollar market values across assets.
  - Optional asset-level weight constraints (e.g., maximum allocation limits $w_i \le 0.30$, long-only $w_i \ge 0$).

### 2.2 User Parameters & Assumptions
- **Expected Return & Risk Inputs**:
  - Historical returns dataframe calibrated from market data, OR
  - Custom annualized expected returns ($\boldsymbol{\mu}$), annualized volatilities ($\boldsymbol{\sigma}$), and empirical correlation matrix ($\mathbf{R}$).
- **Macroeconomic & Risk Assumptions**:
  - Annualized Risk-Free Rate $r_f$ (e.g., 3.5% or 4.0%, representing short-term Treasury yields / cash equivalent returns).
  - Frontier sampling resolution (default: 50 discrete points along the upper curve).
  - Trading / rebalancing periods per year ($dt = 1/252$).

---

## 3. Process

Defines the complete end-to-end technical, mathematical, and optimization workflow executed by the system.

### 3.1 Parameter Calibration & Covariance Matrix Formulation
1. Standardize asset identifiers and compute or ingest annualized statistical vectors:
   - **Expected Return Vector**: $\boldsymbol{\mu} = [\mu_1, \mu_2, \dots, \mu_N]^T \in \mathbb{R}^N$
   - **Volatility Vector**: $\boldsymbol{\sigma} = [\sigma_1, \sigma_2, \dots, \sigma_N]^T \in \mathbb{R}^N$
   - **Empirical Correlation Matrix**: $\mathbf{R} \in \mathbb{R}^{N \times N}$ where $R_{ii} = 1$ and $-1 \le R_{ij} \le 1$
2. Formulate the symmetric positive semi-definite **Annualized Covariance Matrix ($\boldsymbol{\Sigma}$)**:
   $$\boldsymbol{\Sigma} = \operatorname{diag}(\boldsymbol{\sigma}) \mathbf{R} \operatorname{diag}(\boldsymbol{\sigma}), \quad \Sigma_{ij} = \sigma_i \sigma_j R_{ij}$$
3. For any portfolio weight vector $\mathbf{w} = [w_1, \dots, w_N]^T$ satisfying $\sum_{i=1}^N w_i = 1$:
   - **Portfolio Expected Return**: $\mu_p(\mathbf{w}) = \mathbf{w}^T \boldsymbol{\mu} = \sum_{i=1}^N w_i \mu_i$
   - **Portfolio Volatility**: $\sigma_p(\mathbf{w}) = \sqrt{\mathbf{w}^T \boldsymbol{\Sigma} \mathbf{w}} = \sqrt{\sum_{i=1}^N \sum_{j=1}^N w_i w_j \Sigma_{ij}}$
   - **Portfolio Sharpe Ratio**: $\text{SR}(\mathbf{w}) = \frac{\mu_p(\mathbf{w}) - r_f}{\sigma_p(\mathbf{w})}$

### 3.2 Constrained Convex Optimization
Using Sequential Least Squares Programming (`SLSQP`) with multi-start initialization:

1. **Global Minimum Variance (GMV) Portfolio**:
   $$\min_{\mathbf{w}} \mathbf{w}^T \boldsymbol{\Sigma} \mathbf{w} \quad \text{subject to} \quad \sum_{i=1}^N w_i = 1, \quad l_i \le w_i \le u_i \; \forall i$$
2. **Maximum Sharpe Ratio (Tangency / Optimal Risky) Portfolio**:
   $$\max_{\mathbf{w}} \frac{\mathbf{w}^T \boldsymbol{\mu} - r_f}{\sqrt{\mathbf{w}^T \boldsymbol{\Sigma} \mathbf{w}}} \quad \text{subject to} \quad \sum_{i=1}^N w_i = 1, \quad l_i \le w_i \le u_i \; \forall i$$
3. **Efficient Frontier Curve Generation**:
   Discretize target return grid $r_{\text{target}} \in [\mu_{\text{GMV}}, \max(\boldsymbol{\mu})]$ into $M$ points. For each $r_{\text{target}}$:
   $$\min_{\mathbf{w}} \mathbf{w}^T \boldsymbol{\Sigma} \mathbf{w} \quad \text{subject to} \quad \mathbf{w}^T \boldsymbol{\mu} = r_{\text{target}}, \quad \sum_{i=1}^N w_i = 1, \quad l_i \le w_i \le u_i$$
4. **Capital Allocation Line (CAL)**:
   Linear combination connecting the risk-free asset $(0, r_f)$ and the Tangency Portfolio $(\sigma_{\text{Tangency}}, \mu_{\text{Tangency}})$:
   $$\mathbb{E}[R_C] = r_f + \left(\frac{\mu_{\text{Tangency}} - r_f}{\sigma_{\text{Tangency}}}\right) \sigma_C = r_f + \text{SR}_{\max} \cdot \sigma_C$$

### 3.3 Efficiency Gap & Rebalancing Analytics
Evaluate the investor's current portfolio allocation $\mathbf{w}_{\text{current}}$:
1. **Return Enhancement Gap ($\Delta \mu$)**:
   $$\Delta \mu = \mu_p^*(\sigma_{\text{current}}) - \mu_{\text{current}}$$
   where $\mu_p^*(\sigma_{\text{current}})$ is the optimal return on the Efficient Frontier at the current level of volatility.
2. **Volatility Reduction Potential ($\Delta \sigma$)**:
   $$\Delta \sigma = \sigma_{\text{current}} - \sigma_p^*(\mu_{\text{current}})$$
   where $\sigma_p^*(\mu_{\text{current}})$ is the minimum achievable volatility on the Efficient Frontier for the current expected return.
3. **Sharpe Ratio Expansion ($\Delta \text{SR}$)**:
   $$\Delta \text{SR} = \text{SR}_{\max} - \text{SR}_{\text{current}}$$

### 3.4 Standard Operating Procedure (SOP)
1. **Model Execution**: Ingest portfolio weights and asset covariance parameters via `src.core.efficient_frontier.EfficientFrontierEngine`.
2. **Output CSV Generation**: Export summary statistics, frontier points, optimal weight tables, and CAL trajectories to `data/output/`.
3. **Markdown Report Generation**: Render publication-grade Markdown report to `data/output/efficient_frontier_report.md`.
4. **Interactive UI Manifest**: Generate `data/output/ui_manifest.json` on-demand for visualization.

---

## 4. Output Template

Defines the publication-grade deliverables generated in `data/output/`.

### 4.1 Report Deliverable (`data/output/efficient_frontier_report.md`)

```markdown
# Markowitz Efficient Frontier & Portfolio Optimization Report (<YYYY-MM-DD>)

**Analysis Date**: <YYYY-MM-DD>  
**Risk-Free Rate Assumed ($r_f$)**: <RF_PERCENT>%  
**Optimized Asset Universe**: <ASSET_LIST>  
**Deliverable Artifacts**:
- [`efficient_frontier_summary.csv`](efficient_frontier_summary.csv)
- [`efficient_frontier_points.csv`](efficient_frontier_points.csv)
- [`efficient_frontier_allocations.csv`](efficient_frontier_allocations.csv)
- [`efficient_frontier_cal.csv`](efficient_frontier_cal.csv)

---

## 1. Executive Summary

| Portfolio Milestone | Expected Return (Ann.) | Volatility (Ann.) | Sharpe Ratio ($r_f = <RF_PERCENT>%$) | Primary Asset Weights |
| :--- | :--- | :--- | :--- | :--- |
| **Current Portfolio** | `<CURRENT_RET>%` | `<CURRENT_VOL>%` | `<CURRENT_SR>` | `<CURRENT_TOP_WEIGHTS>` |
| **Global Min Variance (GMV)** | `<GMV_RET>%` | `<GMV_VOL>%` | `<GMV_SR>` | `<GMV_TOP_WEIGHTS>` |
| **Maximum Sharpe (Tangency)** | `<MAX_SR_RET>%` | `<MAX_SR_VOL>%` | `<MAX_SR_SR>` | `<MAX_SR_TOP_WEIGHTS>` |

### Key Efficiency Takeaways
- **Return Gap at Current Risk**: At the current volatility of `<CURRENT_VOL>%`, an optimal frontier allocation can achieve `<OPT_RET_AT_VOL>%` expected return (an annual improvement of **+<RETURN_GAP>%**).
- **Risk Reduction Potential**: At the current expected return of `<CURRENT_RET>%`, optimizing the portfolio reduces annual volatility from `<CURRENT_VOL>%` to `<OPT_VOL_AT_RET>%` (a **<VOL_REDUCTION>%** reduction in standard deviation).
- **Sharpe Ratio Expansion**: Rebalancing to the Tangency portfolio increases risk-adjusted efficiency from `<CURRENT_SR>` to `<MAX_SR_SR>`.

---

## 2. Optimal Portfolio Allocations Comparison

| Asset / Ticker | Current Weight | Global Min Variance (GMV) | Max Sharpe (Tangency) | Equal Weight Benchmark |
| :--- | :--- | :--- | :--- | :--- |
| `<ASSET_1>` | `<W_CURR_1>%` | `<W_GMV_1>%` | `<W_MAXSR_1>%` | `<W_EQ_1>%` |
| `<ASSET_2>` | `<W_CURR_2>%` | `<W_GMV_2>%` | `<W_MAXSR_2>%` | `<W_EQ_2>%` |
| ... | ... | ... | ... | ... |
| **Total** | **100.0%** | **100.0%** | **100.0%** | **100.0%** |

---

## 3. Efficient Frontier & Capital Allocation Line (CAL)

```mermaid
xychart-beta
    title "Markowitz Efficient Frontier & Capital Allocation Line"
    x-axis "Annualized Volatility (Risk)" [0%, 5%, 10%, 15%, 20%, 25%, 30%]
    y-axis "Expected Annual Return" 0% --> 25%
    line [3.5%, 7.0%, 10.5%, 14.0%, 17.5%, 21.0%, 24.5%]
```

### Frontier Characteristic Points
| Frontier Point | Target Return | Optimal Volatility | Sharpe Ratio | Dominant Assets |
| :--- | :--- | :--- | :--- | :--- |
| **P1 (GMV)** | `<R1>%` | `<V1>%` | `<SR1>` | `<DOMINANT_1>` |
| **P2 (Balanced)** | `<R2>%` | `<V2>%` | `<SR2>` | `<DOMINANT_2>` |
| **P3 (Tangency / Max SR)** | `<R3>%` | `<V3>%` | `<SR3>` | `<DOMINANT_3>` |
| **P4 (Growth)** | `<R4>%` | `<V4>%` | `<SR4>` | `<DOMINANT_4>` |
| **P5 (Max Return)** | `<R5>%` | `<V5>%` | `<SR5>` | `<DOMINANT_5>` |

---

## 4. Key Observations & Actionable Rebalancing Guidance

1. **Diversification Benefits & Asset Complementarity**: Analysis of the cross-asset correlation matrix and the weights of low-correlation assets.
2. **Rebalancing Strategy**: Concrete transitions from the current allocation towards the Tangency or GMV portfolios.
3. **Risk Budgeting & Leverage (CAL)**: How varying the allocation between cash/Treasuries ($r_f$) and the Tangency portfolio delivers superior risk-adjusted returns across the risk spectrum.

---

## 5. Assumptions & Disclaimers

- **Optimization Model**: Classical Markowitz Mean-Variance Optimization (MVO) subject to long-only constraints ($w_i \ge 0, \sum w_i = 1$).
- **Parameter Estimation**: Historical returns and volatilities are calibrated from past performance and adjusted for macroeconomic cycles. Historical performance does not guarantee future results.
- **Frictions & Taxes**: Optimization does not account for transaction costs, bid-ask spreads, or capital gains tax implications of rebalancing.
- **Disclaimer**: This report is generated by an automated algorithmic system for informational and educational purposes only and does not constitute personalized investment, legal, or tax advice.
```

### 4.2 Structured Data Deliverables

1. **`data/output/efficient_frontier_summary.csv`**:
   - `portfolio_name`: Name of milestone (`Current`, `GMV`, `Max_Sharpe`).
   - `expected_return`: Annualized return.
   - `volatility`: Annualized standard deviation.
   - `sharpe_ratio`: Sharpe ratio ($r_f$).
   - `weight_<ticker>`: Weight for each asset.

2. **`data/output/efficient_frontier_points.csv`**:
   - `point_index`: Sequential integer index.
   - `expected_return`: Target expected return.
   - `volatility`: Minimum achievable volatility.
   - `sharpe_ratio`: Sharpe ratio.
   - `weight_<ticker>`: Optimal asset weights.

3. **`data/output/efficient_frontier_cal.csv`**:
   - `volatility`: Point volatility along the CAL.
   - `expected_return`: Expected return on the Capital Allocation Line.
