# Canadian Retirement, Pension & Tax Jurisdiction Rules

This specification document provides the official data retrieval protocols, statutory formulas, projection rules, and tax mechanisms applicable to Canadian tax residents (specifically Ontario) during accumulation and decumulation.

> **Zero Hardcoding Policy**: Statutory numbers (CPP/OAS maximums, tax brackets, BPA, clawback thresholds) change annually. Agents must **never** hardcode these values into `src/core/`. Instead, follow the Data Lookup Guide below to retrieve current-year rates or accept user overrides, then apply the mathematical projection rules in ad-hoc analysis scripts under `data/tmp/`.

---

## 1. Statutory Data Lookup Guide (CRA & Official Sources)

When running a Canadian retirement analysis, the agent must determine the active base tax year (e.g. 2026) and retrieve current official CRA benchmark parameters.

### 1.1 Key Parameters to Identify for Base Year $T_0$
1. **Canada Pension Plan (CPP / CPP2)**:
   - Year's Maximum Pensionable Earnings (YMPE / MPE)
   - Year's Additional Maximum Pensionable Earnings (YAMPE) (CPP2 tier introduced in 2024)
   - Maximum Annual Base CPP at age 65
   - Maximum Annual Enhanced CPP (CPP1 + CPP2) at age 65
2. **Old Age Security (OAS)**:
   - Maximum Annual OAS benefit at age 65
   - OAS Recovery Tax (Clawback) minimum threshold (Line 23600 Net Income)
3. **Federal & Ontario Income Tax**:
   - Federal Basic Personal Amount (BPA) & Ontario Basic Personal Amount
   - Federal and Ontario tax brackets and marginal rates
4. **Registered Accounts**:
   - TFSA annual contribution room (e.g. $7,000 in recent years, indexed in $500 increments)
   - RRSP annual dollar limit (or 18% of earned income up to cap)
   - CRA RRIF Minimum Withdrawal percentage schedule

### 1.2 Recommended Verification & Search Queries
If the user has not provided explicit current-year tax parameters, the agent can verify current-year parameters using targeted search queries:
- `"CRA maximum CPP benefit at age 65 <YEAR>"`
- `"CRA maximum monthly OAS pension <YEAR>"`
- `"CRA OAS pension recovery tax income threshold <YEAR>"`
- `"Federal and Ontario tax brackets basic personal amount <YEAR>"`
- `"CRA RRIF minimum withdrawal factors"`

---

## 2. Statutory Government Pension Mechanics & Formulas

### 2.1 Canada Pension Plan (CPP & Enhanced CPP2)
- **Contributory Framework**: Standard contributory period spans age 18 to age 65 (up to 47 years). The CRA general drop-out provision excludes 17% of the lowest-earning months (~8 years), establishing a **39-year baseline contributory denominator**.
- **Base CPP Formula**:
  $$\text{Base CPP}_{65} = \text{Base Max}_{T_0} \times \min\left(1.0, \frac{\text{Contributed Years}}{39.0}\right)$$
- **Enhanced CPP Formula (CPP1 & CPP2)**:
  - Funded enhancement tier initiated in 2019 phasing toward 40 contributory years:
  $$\text{Enhanced CPP}_{65} = \text{Enhanced Max}_{T_0} \times \min\left(1.0, \frac{\max(0, \text{Retire Year} - 2019 + 1)}{40.0}\right)$$
- **Actuarial Adjustments for Claim Age**:
  - **Age 65**: $100\%$ baseline entitlement ($\text{Base CPP}_{65} + \text{Enhanced CPP}_{65}$).
  - **Early Claim (Age 60 to 64)**: Reduced by **$0.60\%$ per month** ($7.2\%$ per year) prior to age 65 (maximum reduction of **$-36\%$** at age 60):
    $$\text{Factor}_{\text{early}} = 1.0 - (65 - \text{Claim Age}) \times 12 \times 0.006$$
  - **Delayed Claim (Age 65 to 70)**: Increased by **$0.70\%$ per month** ($8.4\%$ per year) after age 65 (maximum enhancement of **$+42\%$** at age 70):
    $$\text{Factor}_{\text{delayed}} = 1.0 + (\min(70, \text{Claim Age}) - 65) \times 12 \times 0.007$$

### 2.2 Old Age Security (OAS)
- **Residency Proration**: Full OAS requires 40 years of Canadian residence after age 18. For individuals with $10 \le N < 40$ years of residence:
  $$\text{OAS}_{65} = \text{Full OAS Max}_{T_0} \times \min\left(1.0, \frac{N}{40.0}\right)$$
- **Delayed Claim Incentive**: Deferral from age 65 up to age 70 increases the benefit by **$0.60\%$ per month** ($7.2\%$ per year, max **$+36\%$** at age 70):
  $$\text{Factor}_{\text{delayed OAS}} = 1.0 + (\min(70, \text{Claim Age}) - 65) \times 12 \times 0.006$$
- **Age 75 Enhancement**: Automatic **$10\%$ statutory increase** in baseline OAS entitlement starting at age 75:
  $$\text{OAS}_{\text{age} \ge 75} = \text{OAS}_{\text{adjusted}} \times 1.10$$
- **OAS Recovery Tax (Clawback)**:
  - If Line 23600 Net Income exceeds the inflation-indexed clawback threshold ($\text{Threshold}_t$), OAS is subject to a $15\%$ recovery tax:
  $$\text{Clawback}_t = \min\left(\text{OAS}_t, \max\left(0, (\text{Net Income}_t - \text{Threshold}_t) \times 0.15\right)\right)$$

### 2.3 Guaranteed Income Supplement (GIS)
- Income-tested non-taxable benefit for low-income seniors.
- Subject to a steep **$50\%$ clawback** on non-OAS net income.

---

## 3. Dynamic Future Projection & Indexation Rules

All long-term multi-decade decumulation models must project statutory thresholds and benefits in either **nominal dollars** (indexed by inflation) or **constant base-year dollars**:

### 3.1 Cumulative Inflation Indexing
Let $i_k$ be the annual CPI inflation rate for year $k$. The cumulative inflation index from base year $T_0$ to year $t$ is:
$$I_t = \prod_{k=T_0+1}^{t} (1 + i_k)$$

### 3.2 Statutory Escalation Rules
1. **Tax Brackets & Basic Personal Amounts**:
   $$\text{BPA}_t = \text{BPA}_{T_0} \times I_t, \quad \text{Bracket}_{m, t} = \text{Bracket}_{m, T_0} \times I_t$$
2. **OAS Recovery Threshold**:
   $$\text{Threshold}_t = \text{Threshold}_{T_0} \times I_t$$
3. **CPP & OAS Annual Benefits**:
   - In constant-dollar simulations: pensions retain real purchasing power and scale with statutory age adjustment multipliers.
   - In nominal simulations: base entitlements compound annually by $I_t$.
4. **TFSA Annual Contribution Limit**:
   - Statutory rule: The annual room escalates with inflation and rounds to the nearest $\$500$:
   $$\text{TFSA Limit}_t = \text{round}\left(\frac{\text{TFSA Limit}_{T_0} \times I_t}{500}\right) \times 500$$

---

## 4. Income Tax Engine & Account Decumulation Mechanics

### 4.1 Combined Federal & Ontario Marginal Tax Rate Structure
For any projected tax year $t$, calculate combined income tax on taxable income $Y_t$:
- Apply indexed Basic Personal Amount (BPA) zero-tax threshold.
- Apply progressive marginal rate tiers across indexed federal and Ontario bracket boundaries:
  - Tier 1 (approx 20.05% effective combined rate up to Bracket 1)
  - Tier 2 (approx 29.65% – 31.48% combined rate between Bracket 1 and Bracket 2)
  - Tier 3 (approx 37.91% – 43.41% combined rate between Bracket 2 and Bracket 3)
  - Tier 4 (approx 48% – 53.53% top combined rate above Bracket 3 / top threshold)

### 4.2 Registered Retirement Income Fund (RRIF) Minimum Schedule
Accounts must convert to a RRIF by age 71. Mandatory minimum percentage withdrawals:
- **Prior to age 71** (if voluntarily converted):
  $$\text{Rate}(\text{Age}) = \frac{1}{90 - \text{Age}}$$
- **Age 71 and older** (Statutory CRA Schedule):
  - Age 71: $5.28\%$
  - Age 72: $5.40\%$
  - Age 73: $5.53\%$
  - Age 74: $5.67\%$
  - Age 75: $5.82\%$
  - Age 80: $6.82\%$
  - Age 85: $8.51\%$
  - Age 90: $11.92\%$
  - Age 95+: $20.00\%$

### 4.3 Strategic Tax Optimization Protocols
1. **RRSP / RRIF Meltdown Strategy**: Systematic early withdrawals (prior to age 65/71) to absorb lower tax brackets ($20.05\%$ – $29.65\%$), preventing aggressive forced RRIF minimums and severe OAS clawbacks later in life.
2. **TFSA Reinvestment Transfer**: Route surplus funds from the RRSP meltdown directly into annual inflation-indexed TFSA room to permanently shelter capital gains and dividend income.
3. **Spousal Pension Income Splitting (Form T1036)**: Post-age 65, split up to $50\%$ of eligible RRIF and corporate pension distributions to the lower-earning spouse to balance marginal tax brackets and mitigate OAS clawback.
4. **Carrying Charges / Investment Loan Interest Deduction**: Deduct investment loan interest on Line 22100 against ordinary income.
