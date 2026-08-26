---
name: html-dashboard
description: Generates declarative ui_manifest.json in data/output/ for the visual dashboard on-demand. Activate this skill whenever the user requests a dashboard, web view, or visual report.
---

# UI Manifest Generation Skill

This skill guides the AI Agent in producing `data/output/ui_manifest.json` on-demand to feed the web dashboard.

---

## 1. Operating Principles

1. **On-Demand Only**: Only generate `ui_manifest.json` when the user explicitly asks for a dashboard, web view, or visual report.
2. **Zero HTML/Web Code**: The frontend web app is fully decoupled and automatically renders whatever is defined in `ui_manifest.json`. The agent only produces the JSON manifest.
3. **Dynamic & Data-Driven**: Adapt the KPIs, Tabs, Charts, and Tables dynamically to match the active deliverables in `data/output/`.
4. **Zero Absolute Paths**: Use relative filenames for all data sources (e.g. `"normalized_holdings.csv"`).

---

## 2. Manifest Schema (`data/output/ui_manifest.json`)

```json
{
  "schemaVersion": "1.0",
  "title": "Portfolio & Financial Dashboard",
  "asOfDate": "2026-08-25",
  "subtitle": "Multi-Account Asset Allocation & Risk Analysis",
  "kpis": [
    {
      "id": "net-worth",
      "label": "Total Net Worth",
      "value": 881462.02,
      "format": "currency",
      "change": "+49.89%",
      "changeType": "positive",
      "subtext": "unrealized gain",
      "icon": "wallet",
      "color": "emerald"
    }
  ],
  "tabs": [
    {
      "id": "overview",
      "label": "Overview",
      "icon": "layers",
      "layout": "grid-2",
      "widgets": [
        {
          "id": "chart-asset-classes",
          "type": "chart",
          "chartType": "donut",
          "title": "Asset Class Allocation",
          "labels": ["Equities", "Fixed Income", "Cash"],
          "datasets": [
            {
              "data": [750000, 100000, 31462],
              "backgroundColor": ["#22c55e", "#0ea5e9", "#f59e0b"]
            }
          ]
        },
        {
          "id": "tax-buckets",
          "type": "key-val-list",
          "title": "Tax Structure Distribution",
          "items": [
            { "label": "Tax-Free", "value": 250000, "format": "currency", "progressPct": 30, "color": "emerald" }
          ]
        }
      ]
    },
    {
      "id": "holdings",
      "label": "Holdings",
      "icon": "table",
      "layout": "stacked",
      "widgets": [
        {
          "id": "table-holdings",
          "type": "holdings-table",
          "title": "Positions",
          "sourceCsv": "normalized_holdings.csv",
          "columns": [
            { "key": "symbol", "label": "Symbol", "align": "left", "format": "text", "sortable": true },
            { "key": "asset_name", "label": "Asset Name", "align": "left", "format": "text" },
            { "key": "market_value_usd", "label": "Market Value (USD)", "align": "right", "format": "currency", "sortable": true },
            { "key": "pct_of_portfolio", "label": "% Portfolio", "align": "right", "format": "percent", "sortable": true }
          ],
          "features": {
            "search": true,
            "sort": true,
            "aggregateBy": "symbol",
            "exportCsv": true
          }
        }
      ]
    },
    {
      "id": "report",
      "label": "Report",
      "icon": "file-text",
      "layout": "stacked",
      "widgets": [
        {
          "id": "doc-report",
          "type": "markdown",
          "title": "Analysis Report",
          "sourceMd": "asset_allocation_report.md"
        }
      ]
    }
  ]
}
```

### Supported Widget Types & Properties

- **`chart`**:
  - `chartType`: `"donut"` | `"pie"` | `"bar"` | `"horizontal-bar"` | `"line"`
  - `labels`: array of string categories/dates
  - `datasets`: array of `{ label?: string, data: number[], backgroundColor?: string[] | string }`
- **`holdings-table`**: Specialized table supporting position aggregation (`aggregateBy: 'symbol'`), account tag lists, and tax badges.
- **`data-table`**: Generic tabular widget with `sourceCsv`, `columns` (`key`, `label`, `align`, `format`, `sortable`), `features` (`search`, `sort`, `filters`, `exportCsv`).
- **`key-val-list`**: Progress bar items list (`items`: `[{ label, value, format, progressPct, color }]`).
- **`markdown`**: Markdown file viewer (`sourceMd`: filename in `data/output/` or inline `content`). Automatically renders Mermaid diagrams and KaTeX LaTeX formulas.

### Field Enums
- **`format`**: `"currency"` | `"percent"` | `"number"` | `"string"` | `"text"` | `"badge"`
- **`changeType`**: `"positive"` | `"negative"` | `"neutral"`
- **`color`**: `"emerald"` | `"sky"` | `"amber"` | `"rose"` | `"purple"` | `"primary"`
- **`icon`**: `"wallet"` | `"coins"` | `"layers"` | `"table"` | `"file-text"` | `"activity"` | `"trending-up"` | `"shield-check"` | `"gauge"`

---

## 3. Generation SOP

1. **Inspect Outputs**: Check available files in `data/output/` (`*.csv`, `*.md`).
2. **Write Generator Script**: Create `data/tmp/generate_ui_manifest.py` that reads output data, computes KPIs/chart aggregations, and writes `data/output/ui_manifest.json`.
3. **Execute & Verify**:
   ```bash
   uv run python data/tmp/generate_ui_manifest.py
   ```
   Ensure `data/output/ui_manifest.json` is generated with valid JSON structure.
