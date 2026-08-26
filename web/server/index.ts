import { Hono } from "hono";
import { serve } from "@hono/node-server";
import { cors } from "hono/cors";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import Papa from "papaparse";
import type { A2UIManifest, A2UITab } from "../src/types/a2ui";

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
      console.error("Error reading ui_manifest.json:", err);
      return c.json({ error: "Failed to parse ui_manifest.json" }, 500);
    }
  }

  // 2. Generic zero-assumption fallback for Markdown and CSV files present in run directory
  const files = fs.readdirSync(dir).filter((f) => !f.startsWith("."));
  const mdFiles = files.filter((f) => f.endsWith(".md")).sort();
  const csvFiles = files.filter((f) => f.endsWith(".csv")).sort();

  if (mdFiles.length === 0 && csvFiles.length === 0) {
    return c.json({ error: `No deliverables found in run ${runId}` }, 404);
  }

  const tabs: A2UITab[] = [];

  // Generic Markdown Tabs
  for (let i = 0; i < mdFiles.length; i++) {
    const mdFile = mdFiles[i];
    const title = mdFile.replace(/_/g, " ").replace(/\.md$/i, "");
    tabs.push({
      id: `report-${i}`,
      label: title.toUpperCase(),
      icon: "file-text",
      layout: "stacked",
      widgets: [
        {
          id: `doc-${i}`,
          type: "markdown",
          title: title.toUpperCase(),
          sourceMd: mdFile,
        },
      ],
    });
  }

  // Generic CSV Data Table Tabs
  for (let i = 0; i < csvFiles.length; i++) {
    const csvFile = csvFiles[i];
    const title = csvFile.replace(/_/g, " ").replace(/\.csv$/i, "");
    tabs.push({
      id: `csv-${i}`,
      label: title,
      icon: "table",
      layout: "stacked",
      widgets: [
        {
          id: `table-${i}`,
          type: "data-table",
          title: csvFile,
          sourceCsv: csvFile,
          features: {
            search: true,
            sort: true,
            exportCsv: true,
          },
        },
      ],
    });
  }

  const manifest: A2UIManifest = {
    schemaVersion: "1.0",
    title: runId === "current" ? "Current Session Deliverables" : `Run: ${runId}`,
    asOfDate: new Date().toISOString().split("T")[0],
    kpis: [],
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
