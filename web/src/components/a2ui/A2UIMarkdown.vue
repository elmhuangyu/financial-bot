<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from "vue";
import { marked } from "marked";
import katex from "katex";
import markedKatex from "marked-katex-extension";
import mermaid from "mermaid";
import type { A2UIMarkdownWidget } from "../../types/a2ui";
import { FileText, Copy, Check } from "lucide-vue-next";

const props = defineProps<{
  widget: A2UIMarkdownWidget;
  runId: string;
}>();

const rawContent = ref<string>("");
const renderedHtml = ref<string>("");
const isLoading = ref<boolean>(false);
const copied = ref<boolean>(false);
const markdownContainer = ref<HTMLElement | null>(null);

// Initialize Mermaid with Dark Financial Theme & Pure SVG text rendering (htmlLabels: false)
// Setting htmlLabels: false at both root and flowchart levels guarantees mathematical vector centering
// without any foreignObject box clipping, line-height inflation, or Tailwind CSS conflicts.
mermaid.initialize({
  startOnLoad: false,
  htmlLabels: false,
  theme: "dark",
  themeVariables: {
    darkMode: true,
    background: "#0f172a",
    mainBkg: "#1e293b",
    nodeBorder: "#475569",
    nodeTextColor: "#f8fafc",
    primaryColor: "#1e293b",
    primaryTextColor: "#f8fafc",
    primaryBorderColor: "#475569",
    lineColor: "#38bdf8",
    secondaryColor: "#0ea5e9",
    tertiaryColor: "#0f172a",
    tertiaryBorderColor: "#334155",
    tertiaryTextColor: "#94a3b8",
    edgeLabelBackground: "#0f172a",
    fontFamily:
      "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    fontSize: "13px",
  },
  flowchart: {
    htmlLabels: false,
    useMaxWidth: true,
    nodeSpacing: 50,
    rankSpacing: 65,
    padding: 20,
    curve: "basis",
  },
  securityLevel: "loose",
});

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function sanitizeMermaidCode(code: string): string {
  let cleaned = code.trim();
  // Standardize legacy 'graph TD/LR' to 'flowchart TD/LR' for Mermaid v11 engine consistency
  cleaned = cleaned.replace(/^graph\s+([A-Za-z]+)/i, "flowchart $1");
  return cleaned;
}

// Configure custom renderer for Marked to reliably isolate Mermaid blocks and Math blocks
const renderer = new marked.Renderer();
renderer.code = function (token: any, langParam?: string) {
  const text = typeof token === "string" ? token : token?.text || "";
  const lang = (typeof token === "object" && token?.lang ? token.lang : langParam || "")
    .trim()
    .toLowerCase();

  if (lang === "mermaid" || lang.startsWith("mermaid")) {
    const safeCode = encodeURIComponent(text.trim());
    return `<div class="mermaid-container not-prose my-8 p-4 rounded-2xl bg-base-300/60 border border-base-300 flex justify-center overflow-x-auto" data-mermaid-code="${safeCode}"></div>`;
  }
  if (lang === "math" || lang === "latex" || lang === "katex") {
    try {
      const rendered = katex.renderToString(text.trim(), {
        displayMode: true,
        throwOnError: false,
      });
      return `<div class="katex-block not-prose my-4 overflow-x-auto flex justify-center">${rendered}</div>`;
    } catch (e) {
      console.warn("KaTeX code block render error:", e);
    }
  }
  const escaped = typeof token === "object" && token?.escaped ? text : escapeHtml(text);
  return `<pre class="bg-base-300 p-4 rounded-xl overflow-x-auto text-xs font-mono text-slate-200 my-4"><code>${escaped}</code></pre>`;
};

marked.use(
  markedKatex({
    throwOnError: false,
    nonStandard: true,
  }),
);
marked.use({ renderer });

async function renderMermaidDiagrams() {
  if (!markdownContainer.value) return;

  // Wait for document fonts to load completely before measuring SVG text bounding boxes
  if (document.fonts) {
    await document.fonts.ready;
  }

  const containers = markdownContainer.value.querySelectorAll<HTMLElement>(".mermaid-container");
  for (let i = 0; i < containers.length; i++) {
    const el = containers[i];
    const rawCode = decodeURIComponent(el.getAttribute("data-mermaid-code") || "");
    if (rawCode) {
      const code = sanitizeMermaidCode(rawCode);
      const svgId = `mermaid-svg-${Date.now()}-${i}-${Math.random().toString(36).substring(2, 7)}`;
      try {
        const { svg } = await mermaid.render(svgId, code);
        el.innerHTML = svg;

        // Post-render safety: expand any foreignObject bounds if present
        const svgEl = el.querySelector("svg");
        if (svgEl) {
          const foreignObjects = svgEl.querySelectorAll("foreignObject");
          foreignObjects.forEach((fo) => {
            const h = parseFloat(fo.getAttribute("height") || "0");
            if (h > 0) {
              fo.setAttribute("height", `${h + 16}`);
            }
          });
        }
      } catch (mErr) {
        console.warn("Mermaid render error:", mErr);
        // Clean up any stray error element inserted into the DOM by Mermaid
        const stray = document.getElementById(svgId) || document.getElementById(`d${svgId}`);
        stray?.remove();
        el.innerHTML = `<pre class="text-xs font-mono text-rose-400 bg-base-300 p-4 rounded-xl overflow-x-auto">${escapeHtml(code)}</pre>`;
      }
    }
  }
}

async function renderHtmlAndMermaid() {
  renderedHtml.value = marked.parse(rawContent.value) as string;
  await nextTick();
  await renderMermaidDiagrams();
}

async function loadMarkdownContent() {
  if (props.widget.content) {
    rawContent.value = props.widget.content;
    isLoading.value = false;
    await renderHtmlAndMermaid();
    return;
  }

  if (props.widget.sourceMd) {
    isLoading.value = true;
    try {
      const res = await fetch(
        `/api/runs/${props.runId}/file?name=${encodeURIComponent(props.widget.sourceMd)}`,
      );
      if (res.ok) {
        rawContent.value = await res.text();
      }
    } catch (e) {
      console.error(e);
    } finally {
      isLoading.value = false;
    }
    await renderHtmlAndMermaid();
  }
}

function copyContent() {
  navigator.clipboard.writeText(rawContent.value);
  copied.value = true;
  setTimeout(() => {
    copied.value = false;
  }, 2000);
}

onMounted(() => {
  loadMarkdownContent();
});

watch(
  () => [props.widget, props.runId],
  () => {
    loadMarkdownContent();
  },
  { deep: true },
);
</script>

<template>
  <div class="card bg-base-200 border border-base-300 p-6 sm:p-8 shadow-sm min-h-[400px] space-y-4">
    <div class="flex items-center justify-between pb-3 border-b border-base-300">
      <div class="flex items-center gap-2">
        <FileText class="w-5 h-5 text-primary" />
        <h3 class="text-base font-bold text-base-content">
          {{ widget.title || widget.sourceMd || "Markdown Document" }}
        </h3>
      </div>
      <button
        @click="copyContent"
        class="btn btn-sm btn-outline border-base-300 gap-1.5 text-xs text-base-content/80 hover:text-base-content"
      >
        <component :is="copied ? Check : Copy" class="w-4 h-4 text-primary" />
        <span>{{ copied ? "Copied" : "Copy Markdown" }}</span>
      </button>
    </div>

    <div v-if="isLoading" class="flex justify-center items-center py-20">
      <span class="loading loading-spinner text-primary loading-lg"></span>
    </div>
    <div
      v-else
      ref="markdownContainer"
      class="prose max-w-none text-base-content prose-headings:text-base-content prose-p:text-base-content/90 prose-strong:text-base-content prose-table:border-base-300 prose-th:bg-base-300/60 prose-th:text-base-content prose-td:text-base-content/90 prose-th:p-2.5 prose-td:p-2.5 prose-th:text-xs prose-td:text-xs prose-td:font-mono text-sm leading-relaxed"
      v-html="renderedHtml"
    ></div>
  </div>
</template>
