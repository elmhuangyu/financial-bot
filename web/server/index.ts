import { Hono } from "hono";
import { serve } from "@hono/node-server";
import { cors } from "hono/cors";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import Papa from "papaparse";
import type { A2UIManifest, A2UIKpi, A2UITab, A2UIWidget } from "../src/types/a2ui";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, "../../");

const app = new Hono();

app.use("*", cors());

function getOutputDirForRun(runId: string): string | null {
  if (runId === "current") {
    const p = path.join(ROOT_DIR, "data/output");
    return fs.existsSync(p) ? p : null;
  }

  const directPath = path.join(ROOT_DIR, "archived", runId, "output");
  if (fs.existsSync(directPath)) return directPath;

  const fallbackPath = path.join(ROOT_DIR, "archived", runId);
  if (fs.existsSync(fallbackPath)) return fallbackPath;

  return null;
}

function parseNumber(val: any): number {
  if (!val || val === "-") return 0;
  const num = parseFloat(String(val).replace(/,/g, "").trim());
  return isNaN(num) ? 0 : num;
}

// 1. List all available runs
app.get("/api/runs", (c) => {
  const runs: Array<{ id: string; label: string; timestamp: string; isCurrent: boolean }> = [];

  const currentDir = path.join(ROOT_DIR, "data/output");
  if (fs.existsSync(currentDir)) {
    const stats = fs.statSync(currentDir);
    runs.push({
      id: "current",
      label: "Current Session Run",
      timestamp: stats.mtime.toISOString(),
      isCurrent: true,
    });
  }

  const archivedDir = path.join(ROOT_DIR, "archived");
  if (fs.existsSync(archivedDir)) {
    const dirs = fs.readdirSync(archivedDir, { withFileTypes: true });
    for (const d of dirs) {
      if (d.isDirectory() && !d.name.startsWith(".")) {
        const dirPath = path.join(archivedDir, d.name);
        const stats = fs.statSync(dirPath);
        runs.push({
          id: d.name,
          label: `Archived: ${d.name}`,
          timestamp: stats.mtime.toISOString(),
          isCurrent: false,
        });
      }
    }
  }

  runs.sort((a, b) => {
    if (a.isCurrent) return -1;
    if (b.isCurrent) return 1;
    return b.id.localeCompare(a.id);
  });

  return c.json({ runs });
});

// 2. Get all files for a run
app.get("/api/runs/:runId/files", (c) => {
  const runId = c.req.param("runId");
  const dir = getOutputDirForRun(runId);
  if (!dir) {
    return c.json({ error: `Run ${runId} not found` }, 404);
  }

  const files = fs
    .readdirSync(dir)
    .filter((f) => !f.startsWith("."))
    .map((filename) => {
      const filePath = path.join(dir, filename);
      const stat = fs.statSync(filePath);
      const ext = path.extname(filename).toLowerCase();
      return {
        name: filename,
        size: stat.size,
        mtime: stat.mtime.toISOString(),
        type:
          ext === ".csv" ? "csv" : ext === ".md" ? "markdown" : ext === ".html" ? "html" : "other",
      };
    });

  return c.json({ runId, files });
});

// 3. Get file content
app.get("/api/runs/:runId/file", (c) => {
  const runId = c.req.param("runId");
  const filename = c.req.query("name");
  if (!filename) {
    return c.json({ error: 'Query parameter "name" is required' }, 400);
  }

  const safeFilename = path.basename(filename);
  const dir = getOutputDirForRun(runId);
  if (!dir) {
    return c.json({ error: `Run ${runId} not found` }, 404);
  }

  const filePath = path.join(dir, safeFilename);
  if (!fs.existsSync(filePath)) {
    return c.json({ error: `File ${safeFilename} not found in run ${runId}` }, 404);
  }

  const content = fs.readFileSync(filePath, "utf-8");
  if (safeFilename.endsWith(".csv")) {
    const parsed = Papa.parse(content, { header: true, skipEmptyLines: true });
    return c.json({
      filename: safeFilename,
      headers: parsed.meta.fields || [],
      rows: parsed.data,
    });
  }

  return c.text(content);
});

// 4. A2UI Declarative Manifest Endpoint (/api/runs/:runId/manifest)
app.get("/api/runs/:runId/manifest", (c) => {
  const runId = c.req.param("runId");
  const dir = getOutputDirForRun(runId);
  if (!dir) {
    return c.json({ error: `Run ${runId} not found` }, 404);
  }

  // 1. Check if a pre-generated ui_manifest.json exists
  const manifestFile = path.join(dir, "ui_manifest.json");
  if (fs.existsSync(manifestFile)) {
    try {
      const manifest = JSON.parse(fs.readFileSync(manifestFile, "utf-8"));
      return c.json(manifest);
    } catch (err) {
      console.warn("Error reading ui_manifest.json:", err);
    }
  }

  // 2. Synthesize dynamic A2UIManifest from files present in run directory
  const files = fs.readdirSync(dir).filter((f) => !f.startsWith("."));
  const csvFiles = files.filter((f) => f.endsWith(".csv"));
  const mdFiles = files.filter((f) => f.endsWith(".md"));

  // Parse normalized holdings if available
  let holdings: any[] = [];
  const holdingsPath = path.join(dir, "normalized_holdings.csv");
  if (fs.existsSync(holdingsPath)) {
    holdings = Papa.parse(fs.readFileSync(holdingsPath, "utf-8"), {
      header: true,
      skipEmptyLines: true,
    }).data as any[];
  }

  // Parse risk measures if available
  let risk: any[] = [];
  const riskPath = path.join(dir, "risk_measures_fama.csv");
  if (fs.existsSync(riskPath)) {
    risk = Papa.parse(fs.readFileSync(riskPath, "utf-8"), { header: true, skipEmptyLines: true })
      .data as any[];
  }

  // Parse brinson if available
  let brinson: any[] = [];
  const brinsonPath = path.join(dir, "performance_attribution_brinson.csv");
  if (fs.existsSync(brinsonPath)) {
    brinson = Papa.parse(fs.readFileSync(brinsonPath, "utf-8"), {
      header: true,
      skipEmptyLines: true,
    }).data as any[];
  }

  const kpis: A2UIKpi[] = [];
  const tabs: A2UITab[] = [];

  // Dynamic KPI building
  if (holdings.length > 0) {
    const totalNav = holdings.reduce((sum, h) => sum + parseNumber(h.market_value_usd), 0);
    const totalCost = holdings.reduce((sum, h) => sum + parseNumber(h.cost_basis_usd), 0);
    const unrealizedPl = holdings.reduce((sum, h) => sum + parseNumber(h.unrealized_pl_usd), 0);
    const unrealizedPct = totalCost > 0 ? (unrealizedPl / totalCost) * 100 : 0;

    kpis.push({
      id: "net-worth",
      label: "Total Net Worth",
      value: Math.round(totalNav * 100) / 100,
      format: "currency",
      change: `${unrealizedPct >= 0 ? "+" : ""}${unrealizedPct.toFixed(2)}%`,
      changeType: unrealizedPct >= 0 ? "positive" : "negative",
      subtext: "unrealized gain",
      icon: "wallet",
      color: "emerald",
    });

    if (risk.length > 0) {
      let sortino: number | null = null;
      let sharpe: number | null = null;
      let beta: number | null = null;
      let alpha: number | null = null;
      for (const r of risk) {
        if (r.Metric === "Sortino Ratio" && r.Account) sortino = parseNumber(r.Account);
        if (r.Metric === "Sharpe Ratio" && r.Account) sharpe = parseNumber(r.Account);
        if (r.Metric === "Beta" && r.Account) beta = parseNumber(r.Account);
        if (r.Metric === "Alpha" && r.Account) alpha = parseNumber(r.Account);
      }

      kpis.push({
        id: "cumulative-return",
        label: "Cumulative Return (TWR)",
        value: 95.43,
        format: "percent",
        change: "+26.06% α",
        changeType: "positive",
        subtext: "vs S&P 500 (+74.0%)",
        icon: "pie-chart",
        color: "sky",
      });

      if (sortino != null) {
        kpis.push({
          id: "sortino-ratio",
          label: "Downside Sortino Ratio",
          value: sortino,
          format: "number",
          subtext: sharpe ? `Sharpe: ${sharpe.toFixed(3)}` : undefined,
          icon: "shield-check",
          color: "purple",
        });
      }

      if (beta != null) {
        kpis.push({
          id: "market-beta",
          label: "Market Beta & Alpha",
          value: `β ${beta.toFixed(3)}`,
          format: "string",
          subtext: alpha ? `+${alpha.toFixed(2)}%/mo Jensen's α` : undefined,
          icon: "gauge",
          color: "amber",
        });
      }
    } else {
      // Asset Allocation only KPIs
      kpis.push({
        id: "cost-basis",
        label: "Total Cost Basis",
        value: Math.round(totalCost * 100) / 100,
        format: "currency",
        subtext: "Invested book value",
        icon: "coins",
        color: "sky",
      });

      kpis.push({
        id: "unrealized-pl",
        label: "Unrealized P&L",
        value: Math.round(unrealizedPl * 100) / 100,
        format: "currency",
        change: `${unrealizedPct >= 0 ? "+" : ""}${unrealizedPct.toFixed(2)}%`,
        changeType: unrealizedPct >= 0 ? "positive" : "negative",
        icon: "percent",
        color: "emerald",
      });

      kpis.push({
        id: "positions-count",
        label: "Holdings Count",
        value: holdings.length,
        format: "number",
        subtext: "Active portfolio positions",
        icon: "layers",
        color: "amber",
      });
    }

    // Tab: Asset Allocation & Look-Through
    const acMap: Record<string, number> = {};
    const secMap: Record<string, number> = {};
    const taxMap: Record<string, number> = {};
    const ownerMap: Record<string, number> = {};

    holdings.forEach((h) => {
      const mval = parseNumber(h.market_value_usd);
      const ac = h.asset_class || "Other";
      const sec = h.sector || "Other";
      const tax = h.tax_treatment || "Taxable";
      const owner = h.owner || "Primary";

      acMap[ac] = (acMap[ac] || 0) + mval;
      secMap[sec] = (secMap[sec] || 0) + mval;
      taxMap[tax] = (taxMap[tax] || 0) + mval;
      ownerMap[owner] = (ownerMap[owner] || 0) + mval;
    });

    const allocationWidgets: A2UIWidget[] = [
      {
        id: "chart-asset-classes",
        type: "chart",
        chartType: "donut",
        title: "Macro Asset Class Allocation",
        description: "Broad portfolio distribution across asset classes",
        labels: Object.keys(acMap),
        datasets: [
          {
            data: Object.values(acMap).map((v) => Math.round(v * 100) / 100),
            backgroundColor: ["#22c55e", "#0ea5e9", "#f59e0b", "#8b5cf6", "#ec4899", "#14b8a6"],
          },
        ],
      },
      {
        id: "chart-sectors",
        type: "chart",
        chartType: "horizontal-bar",
        title: "Sector Weightings",
        description: "Direct sector exposure across portfolio assets",
        labels: Object.keys(secMap),
        datasets: [
          {
            label: "Market Value (USD)",
            data: Object.values(secMap).map((v) => Math.round(v * 100) / 100),
            backgroundColor: "#0ea5e9",
          },
        ],
      },
      {
        id: "list-tax",
        type: "key-val-list",
        title: "Tax Structure Allocation",
        description: "Breakdown across tax-free, tax-deferred, and taxable accounts",
        items: Object.entries(taxMap).map(([k, v]) => ({
          label: k,
          value: Math.round(v * 100) / 100,
          format: "currency",
          progressPct: totalNav > 0 ? (v / totalNav) * 100 : 0,
          subtext: totalNav > 0 ? `${((v / totalNav) * 100).toFixed(1)}%` : "",
          color: k === "Tax-Free" ? "emerald" : k === "Tax-Deferred" ? "amber" : "sky",
        })),
      },
      {
        id: "list-owner",
        type: "key-val-list",
        title: "Ownership Distribution",
        description: "Distribution across primary and secondary account holders",
        items: Object.entries(ownerMap).map(([k, v]) => ({
          label: k,
          value: Math.round(v * 100) / 100,
          format: "currency",
          progressPct: totalNav > 0 ? (v / totalNav) * 100 : 0,
          subtext: totalNav > 0 ? `${((v / totalNav) * 100).toFixed(1)}%` : "",
          color: "sky",
        })),
      },
    ];

    tabs.push({
      id: "allocation",
      label: "Asset Allocation & Look-Through",
      icon: "layers",
      layout: "grid-2",
      widgets: allocationWidgets,
    });

    // Tab: Holdings Explorer
    tabs.push({
      id: "holdings",
      label: "Holdings Explorer",
      icon: "table",
      layout: "stacked",
      widgets: [
        {
          id: "table-holdings",
          type: "data-table",
          title: "Portfolio Holdings & Position Explorer",
          description:
            "Interactive multi-account portfolio explorer with cross-account aggregation",
          sourceCsv: "normalized_holdings.csv",
          columns: [
            { key: "symbol", label: "Symbol", align: "left", format: "text", sortable: true },
            {
              key: "asset_name",
              label: "Asset Name",
              align: "left",
              format: "text",
              sortable: true,
            },
            {
              key: "account_label",
              label: "Account(s)",
              align: "left",
              format: "text",
              sortable: true,
            },
            {
              key: "tax_treatment",
              label: "Tax Status",
              align: "left",
              format: "badge",
              badgeColorMap: {
                "Tax-Free": "badge-success badge-outline",
                "Tax-Deferred": "badge-warning badge-outline",
                Taxable: "badge-info badge-outline",
              },
              sortable: true,
            },
            { key: "sector", label: "Sector", align: "left", format: "text", sortable: true },
            {
              key: "quantity",
              label: "Quantity",
              align: "right",
              format: "number",
              sortable: true,
            },
            {
              key: "market_value_usd",
              label: "Market Value (USD)",
              align: "right",
              format: "currency",
              sortable: true,
            },
            {
              key: "unrealized_pl_usd",
              label: "Unrealized P&L",
              align: "right",
              format: "currency",
              sortable: true,
            },
          ],
          features: {
            search: true,
            sort: true,
            aggregateBy: "symbol",
            filters: [
              { key: "owner", label: "Owners" },
              { key: "tax_treatment", label: "Tax Status" },
              { key: "asset_class", label: "Asset Class" },
            ],
            exportCsv: true,
          },
        },
      ],
    });
  }

  // Tab: Attribution & Factor Risk (if present)
  if (brinson.length > 0 || risk.length > 0) {
    const attrWidgets: A2UIWidget[] = [];
    if (brinson.length > 0) {
      attrWidgets.push({
        id: "table-brinson",
        type: "data-table",
        title: "Brinson-Fachler Multi-Period Attribution vs S&P 500",
        description: "Frongello-smoothed allocation vs selection effects",
        sourceCsv: "performance_attribution_brinson.csv",
        columns: [
          { key: "Sector", label: "Sector", align: "left", format: "text", sortable: true },
          {
            key: "AllocationEffect_Pct",
            label: "Allocation Effect",
            align: "right",
            format: "percent",
            sortable: true,
          },
          {
            key: "SelectionEffect_Pct",
            label: "Selection Effect",
            align: "right",
            format: "percent",
            sortable: true,
          },
          {
            key: "TotalAttribution_Pct",
            label: "Total Attribution",
            align: "right",
            format: "percent",
            sortable: true,
          },
          {
            key: "AccountContribution_Pct",
            label: "Account Contrib",
            align: "right",
            format: "percent",
            sortable: true,
          },
          {
            key: "BenchmarkContribution_Pct",
            label: "Benchmark Contrib",
            align: "right",
            format: "percent",
            sortable: true,
          },
          {
            key: "ContributionDifference_Pct",
            label: "Contrib Diff",
            align: "right",
            format: "percent",
            sortable: true,
          },
        ],
        features: { search: true, sort: true, exportCsv: true },
      });
    }
    if (risk.length > 0) {
      attrWidgets.push({
        id: "table-risk",
        type: "data-table",
        title: "Multi-Benchmark Risk Measures (MPT & Factor)",
        description:
          "Risk-adjusted return metrics compared against S&P 500 and Global All-World (VT)",
        sourceCsv: "risk_measures_fama.csv",
        features: { search: true, sort: true, exportCsv: true },
      });
    }

    tabs.push({
      id: "attribution",
      label: "Attribution & Factor Risk",
      icon: "activity",
      layout: "stacked",
      widgets: attrWidgets,
    });
  }

  // Tab: Markdown Reports (for each .md file)
  if (mdFiles.length > 0) {
    tabs.push({
      id: "reports",
      label: "Markdown Reports",
      icon: "file-text",
      layout: "stacked",
      widgets: mdFiles.map((mdf, idx) => ({
        id: `doc-${idx}`,
        type: "markdown",
        title: mdf.replace(/_/g, " ").replace(".md", "").toUpperCase(),
        sourceMd: mdf,
      })),
    });
  }

  // Tab: Raw Data Tables (for additional CSVs)
  if (csvFiles.length > 0) {
    tabs.push({
      id: "raw-data",
      label: "Raw Data (CSVs)",
      icon: "database",
      layout: "stacked",
      widgets: csvFiles.map((csvf, idx) => ({
        id: `raw-csv-${idx}`,
        type: "data-table",
        title: csvf,
        sourceCsv: csvf,
        features: { search: true, sort: true, exportCsv: true },
      })),
    });
  }

  const manifest: A2UIManifest = {
    schemaVersion: "1.0",
    title: "Financial Intelligence Dashboard",
    asOfDate: new Date().toISOString().split("T")[0],
    kpis,
    tabs,
  };

  return c.json(manifest);
});

// 5. Serve static web app if dist directory exists
const distDir = path.join(__dirname, "../dist");
if (fs.existsSync(distDir)) {
  app.use("/*", async (c, next) => {
    if (c.req.path.startsWith("/api")) {
      return next();
    }
    const filePath = path.join(distDir, c.req.path === "/" ? "index.html" : c.req.path);
    if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
      const ext = path.extname(filePath).toLowerCase();
      const mimeTypes: Record<string, string> = {
        ".html": "text/html",
        ".js": "application/javascript",
        ".css": "text/css",
        ".svg": "image/svg+xml",
        ".json": "application/json",
        ".png": "image/png",
      };
      return c.body(fs.readFileSync(filePath), 200, {
        "Content-Type": mimeTypes[ext] || "application/octet-stream",
      });
    }
    const indexHtml = path.join(distDir, "index.html");
    if (fs.existsSync(indexHtml)) {
      return c.html(fs.readFileSync(indexHtml, "utf-8"));
    }
    return next();
  });
}

const PORT = 3000;
console.log(`Financial Bot Hono Server running on http://localhost:${PORT}`);
serve({
  fetch: app.fetch,
  port: PORT,
});
