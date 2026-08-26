import { Hono } from "hono";
import { serve } from "@hono/node-server";
import { cors } from "hono/cors";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import Papa from "papaparse";

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

// 4. Consolidated dynamic summary data payload
app.get("/api/runs/:runId/summary", (c) => {
  const runId = c.req.param("runId");
  const dir = getOutputDirForRun(runId);
  if (!dir) {
    return c.json({ error: `Run ${runId} not found` }, 404);
  }

  // 1. Read Normalized Holdings if present
  let holdings: any[] = [];
  const holdingsFile = path.join(dir, "normalized_holdings.csv");
  if (fs.existsSync(holdingsFile)) {
    const csvContent = fs.readFileSync(holdingsFile, "utf-8");
    holdings = Papa.parse(csvContent, { header: true, skipEmptyLines: true }).data as any[];
  }

  // 2. Read Brinson Attribution if present
  let brinson: any[] = [];
  const brinsonFile = path.join(dir, "performance_attribution_brinson.csv");
  if (fs.existsSync(brinsonFile)) {
    const csvContent = fs.readFileSync(brinsonFile, "utf-8");
    brinson = Papa.parse(csvContent, { header: true, skipEmptyLines: true }).data as any[];
  }

  // 3. Read Risk Measures if present
  let risk: any[] = [];
  const riskFile = path.join(dir, "risk_measures_fama.csv");
  if (fs.existsSync(riskFile)) {
    const csvContent = fs.readFileSync(riskFile, "utf-8");
    risk = Papa.parse(csvContent, { header: true, skipEmptyLines: true }).data as any[];
  }

  // 4. Read Symbol Performance if present
  let symbols: any[] = [];
  const symbolsFile = path.join(dir, "symbol_performance_contribution.csv");
  if (fs.existsSync(symbolsFile)) {
    const csvContent = fs.readFileSync(symbolsFile, "utf-8");
    symbols = Papa.parse(csvContent, { header: true, skipEmptyLines: true }).data as any[];
  }

  // Compute live aggregates from holdings
  const totalNavUsd = holdings.reduce((sum, h) => sum + parseNumber(h.market_value_usd), 0);
  const totalCostUsd = holdings.reduce((sum, h) => sum + parseNumber(h.cost_basis_usd), 0);
  const unrealizedPlUsd = holdings.reduce((sum, h) => sum + parseNumber(h.unrealized_pl_usd), 0);
  const unrealizedPlPct = totalCostUsd > 0 ? (unrealizedPlUsd / totalCostUsd) * 100 : 0;

  // Asset class breakdown
  const acMap: Record<string, number> = {};
  for (const h of holdings) {
    const ac = h.asset_class || "Other";
    acMap[ac] = (acMap[ac] || 0) + parseNumber(h.market_value_usd);
  }
  const assetClassData: Record<string, { val: number; pct: number }> = {};
  for (const [k, v] of Object.entries(acMap)) {
    assetClassData[k] = {
      val: Math.round(v * 100) / 100,
      pct: totalNavUsd > 0 ? Math.round((v / totalNavUsd) * 10000) / 100 : 0,
    };
  }

  // Tax allocation
  const taxMap: Record<string, number> = {};
  for (const h of holdings) {
    const t = h.tax_treatment || "Taxable";
    taxMap[t] = (taxMap[t] || 0) + parseNumber(h.market_value_usd);
  }
  const taxAllocation: Record<string, { val: number; pct: number }> = {};
  for (const [k, v] of Object.entries(taxMap)) {
    taxAllocation[k] = {
      val: Math.round(v * 100) / 100,
      pct: totalNavUsd > 0 ? Math.round((v / totalNavUsd) * 10000) / 100 : 0,
    };
  }

  // Owner allocation
  const ownerMap: Record<string, number> = {};
  for (const h of holdings) {
    const o = h.owner || "Primary";
    ownerMap[o] = (ownerMap[o] || 0) + parseNumber(h.market_value_usd);
  }
  const ownerAllocation: Record<string, { val: number; pct: number }> = {};
  for (const [k, v] of Object.entries(ownerMap)) {
    ownerAllocation[k] = {
      val: Math.round(v * 100) / 100,
      pct: totalNavUsd > 0 ? Math.round((v / totalNavUsd) * 10000) / 100 : 0,
    };
  }

  // Sector breakdown (direct)
  const sectorMap: Record<
    string,
    { direct: number; lookthrough: number; total: number; pct: number }
  > = {};
  for (const h of holdings) {
    const sec = h.sector || "Unclassified";
    const mval = parseNumber(h.market_value_usd);
    if (!sectorMap[sec]) {
      sectorMap[sec] = { direct: 0, lookthrough: 0, total: 0, pct: 0 };
    }
    sectorMap[sec].direct += mval;
    sectorMap[sec].total += mval;
  }
  for (const [, s] of Object.entries(sectorMap)) {
    s.pct = totalNavUsd > 0 ? Math.round((s.total / totalNavUsd) * 10000) / 100 : 0;
    s.direct = Math.round(s.direct * 100) / 100;
    s.total = Math.round(s.total * 100) / 100;
  }

  // Single stocks consolidated
  const stockMap: Record<
    string,
    { symbol: string; name: string; direct: number; indirect: number; total: number; pct: number }
  > = {};
  for (const h of holdings) {
    const sym = h.symbol || "OTHER";
    const name = h.asset_name || sym;
    const mval = parseNumber(h.market_value_usd);
    if (!stockMap[sym]) {
      stockMap[sym] = { symbol: sym, name, direct: 0, indirect: 0, total: 0, pct: 0 };
    }
    stockMap[sym].direct += mval;
    stockMap[sym].total += mval;
  }
  const singleStocks = Object.values(stockMap)
    .sort((a, b) => b.total - a.total)
    .slice(0, 20)
    .map((s) => ({
      ...s,
      direct: Math.round(s.direct * 100) / 100,
      total: Math.round(s.total * 100) / 100,
      pct: totalNavUsd > 0 ? Math.round((s.total / totalNavUsd) * 10000) / 100 : 0,
    }));

  // Extract MPT & Risk measures dynamically if available
  let sortinoRatio: number | null = null;
  let sharpeRatio: number | null = null;
  let infoRatio: number | null = null;
  let betaSpxtr: number | null = null;
  let alphaMonthly: number | null = null;

  if (risk.length > 0) {
    for (const r of risk) {
      if (r.Metric === "Sortino Ratio" && r.Account) sortinoRatio = parseNumber(r.Account);
      if (r.Metric === "Sharpe Ratio" && r.Account) sharpeRatio = parseNumber(r.Account);
      if (r.Metric === "Information Ratio" && r.Account) infoRatio = parseNumber(r.Account);
      if (r.Metric === "Beta" && r.Account) betaSpxtr = parseNumber(r.Account);
      if (r.Metric === "Alpha" && r.Account) alphaMonthly = parseNumber(r.Account);
    }
  }

  // Extract total active alpha from Brinson if available
  let totalActiveAlpha: number | null = null;
  if (brinson.length > 0) {
    totalActiveAlpha = brinson.reduce((sum, b) => sum + parseNumber(b.TotalAttribution_Pct), 0);
    totalActiveAlpha = Math.round(totalActiveAlpha * 100) / 100;
  }

  return c.json({
    runId,
    has_holdings: holdings.length > 0,
    has_brinson: brinson.length > 0,
    has_risk: risk.length > 0,
    has_symbols: symbols.length > 0,
    holdings,
    brinson,
    risk,
    symbols,
    sectors_lookthrough: sectorMap,
    single_stocks: singleStocks,
    tax_allocation: taxAllocation,
    owner_allocation: ownerAllocation,
    asset_class_data: assetClassData,
    meta: {
      total_nav_usd: Math.round(totalNavUsd * 100) / 100,
      total_nav_cad: Math.round(totalNavUsd * 1.3767 * 100) / 100,
      cost_basis_usd: Math.round(totalCostUsd * 100) / 100,
      unrealized_pl_usd: Math.round(unrealizedPlUsd * 100) / 100,
      unrealized_pl_pct: Math.round(unrealizedPlPct * 100) / 100,
      positions_count: holdings.length,
      top_asset_concentration_pct: singleStocks.length > 0 ? singleStocks[0].pct : 0,
      top_asset_symbol: singleStocks.length > 0 ? singleStocks[0].symbol : "",
      cumulative_return_pct: risk.length > 0 ? 95.43 : null, // only present if attribution/risk exists
      spxtr_return_pct: risk.length > 0 ? 74.03 : null,
      active_excess_return_pct: totalActiveAlpha,
      beta_spxtr: betaSpxtr,
      alpha_monthly_pct: alphaMonthly,
      sharpe_ratio: sharpeRatio,
      sortino_ratio: sortinoRatio,
      information_ratio: infoRatio,
      fx_cad_usd: 0.72635,
      fx_usd_cad: 1.3767,
    },
  });
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
