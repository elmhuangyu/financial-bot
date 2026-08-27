# SPEC: Comprehensive Retirement & Decumulation Planning

## 1. Objective & Scope
This specification defines the universal methodology, stochastic market simulation standards, multi-scenario trade-off modeling, decumulation sequencing, and reporting templates for retirement and decumulation planning (FIRE and Longevity Analysis).
It assesses:
1. Target accumulation trajectories and Monte Carlo retirement timing distributions (P10, P50, P90).
2. **Multi-Scenario Sensitivity & Real Estate Liquidation Matrix**: Comparing different retirement target thresholds (e.g., $2.8M vs. $3.0M vs. $3.5M USD), consumption levels ($80k vs. $90k vs. $100k vs. $120k CAD/year), real estate options (keep & rent vs. immediate liquidation vs. emergency contingency sale), and post-retirement asset allocation structures (100% S&P 500 vs. 90/10 vs. 80/20 equity/treasury blends).
3. Longevity safety, sequence of returns risk (SRR), and portfolio ruin probabilities through advanced ages (e.g., age 95+).
4. Statutory government pension optimization and claim timing.
5. Multi-account decumulation schedules across tax-deferred, tax-free, and taxable asset buckets.

---

## 2. Required Input
- **Portfolio Baseline**: Current valuations classified across asset classes and tax buckets (Tax-Deferred, Tax-Free, Taxable), historical/expected accumulation and post-retirement returns, volatilities, asset class correlations, and degree of freedom parameters for fat-tailed shocks.
- **Liabilities & Real Estate**: Mortgages, loan terms and interest deductibility, rental cash flows, cost basis (ACB), and inflation-indexed property valuations with alternative liquidation strategies.
- **Demographic Profile**: Birth years, retirement horizon, residency history, and statutory pension contribution histories.
- **Consumption Targets**: Baseline annual lifestyle expenditures in constant base-year currency and inflation expectations across baseline, conservative, and expanded scenarios.
- **Retirement Milestones**: Threshold portfolio targets, delayed-work boundaries, and debt amortization schedules.

---

## 3. Process & Core Mathematical Models

### 3.1 Heavy-Tailed Return Generation
Simulate annual portfolio returns using standardized Student-t innovations to model fat-tailed market shocks:
$$\tilde{R}_t = \mu + \sigma \cdot \left( \frac{t_{\nu}}{\sqrt{\nu / (\nu - 2)}} \right)$$
where $\nu$ represents degrees of freedom (typically $\nu = 5.0$).

### 3.2 Dynamic Cash Buffer & Asset Allocation Blends
1. **Dynamic Cash Buffer Rule**: Maintain a 3-year living expense reserve in high-yield cash or money market instruments upon retirement. In down-market years ($R_t < 0$), living expenses are drawn primarily from the cash buffer to mitigate Sequence of Returns Risk (SRR), while up-market years replenish the reserve.
2. **Post-Retirement Allocation Optimization**:
   - **100% Equity (S&P 500)**: Return 9.50%, Volatility 18.00%.
   - **90/10 Balanced Growth (90% S&P 500 + 10% 10-Yr US Treasuries)**: Return 8.97%, Volatility 16.21%. Mitigates sequence risk and compresses ruin rates.
   - **80/20 Classic Conservative (80% S&P 500 + 20% 10-Yr US Treasuries)**: Return 8.44%, Volatility 14.46%.

### 3.3 Real Estate Liquidation Protocols
Simulate three distinct real estate paradigms:
1. **Perpetual Cash Flow (Keep & Rent)**: The property is held throughout retirement, generating inflation-hedged net rental cash flows while preserving full equity.
2. **Immediate Retirement Liquidation (Sell at Retirement)**: The property is liquidated at retirement. Net proceeds after mortgage payoff, transaction costs (~5%), and capital gains tax are injected into the liquid investment portfolio.
3. **Emergency Liquidation Backstop (Contingency Sale)**: The property is held for rental cash flows under normal market conditions, but automatically liquidated at current market value if liquid assets drop below a critical liquidity threshold (e.g., $400k USD), eliminating tail ruin risk.

### 3.4 Multi-Scenario Comparative Framework
The planning model evaluates and contrasts multiple strategic scenarios to provide decision clarity on trade-offs:
- **Baseline Plan**: Primary target threshold and nominal living expenses with rental held.
- **Fast FIRE Plan**: $2.8M USD target with $80k CAD spending (reaches retirement in 6 years, Bob age 43).
- **Asset Allocation Comparisons**: Evaluating 100% equity vs. 90/10 equity/treasury blends.
- **Real Estate Variations**: Immediate liquidation vs. emergency backstop liquidation.
- **Plan Solidity Scorecard**: Rating each scenario's viability based on 95-year ruin rates ($<3\%$ A+, $<5\%$ A, $<8\%$ A-, $\ge 8\%$ B+).

### 3.5 Jurisdiction-Specific Pension & Tax Integration
- Regional tax systems and statutory pension models are decoupled from this general specification.
- For Canadian jurisdiction rules (CPP, Enhanced CPP2, OAS, OAS Clawback, RRIF mandatory minima, and Ontario progressive tax brackets), refer to [`CANADA.md`](CANADA.md).

### 3.6 Decumulation Priority & Optimization
1. **Deduct Guaranteed Non-Portfolio Inflows**: Account for net rental income (if retained) and index-linked government pensions first.
2. **Tax-Deferred Meltdown**: Systematically withdraw from tax-deferred accounts in early retirement to utilize lower marginal tax brackets and prevent future mandatory minimum spikes.
3. **Tax-Free Reinvestment**: Direct unspent distributions from early meltdowns into newly indexed tax-free contribution room.
4. **Taxable Liquidation**: Draw from taxable accounts for lump-sum debt payoffs or shortfall coverage, applying capital gains preferential tax treatments.
5. **Tax-Free Preservation**: Reserve tax-free accounts as the final liquidity backstop during late-life stages or high tax-bracket events.

---

## 4. Output Deliverables

- `data/output/retirement_planning_report.md`: Publication-grade Markdown report containing executive takeaways, asset allocation impact comparisons, real estate matrix, accumulation percentiles, longevity risk assessments, pension roadmaps, and the full multi-account decumulation schedule.
- `data/output/scenario_comparison_matrix.csv`: Multi-scenario sensitivity dataset comparing target sizes, asset allocations, real estate liquidation strategies, retirement ages, spending levels, and ruin probabilities in normalized USD Base.
- `data/output/yearly_decumulation_schedule.csv`: Detailed year-by-year schedule from retirement to target age, reporting itemized draws by account bucket, tax liabilities, and real purchasing power in normalized USD Base.
- `data/output/ui_manifest.json`: Web dashboard manifest conforming to the html-dashboard skill specification, featuring scenario comparison tables and KPI scorecards.
