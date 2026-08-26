<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from "vue";
import { marked } from "marked";
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

// Initialize Mermaid with Dark Financial Slate Theme
mermaid.initialize({
  startOnLoad: false,
  theme: "dark",
  themeVariables: {
    darkMode: true,
    background: "#0f172a",
    primaryColor: "#22c55e",
    primaryTextColor: "#f8fafc",
    primaryBorderColor: "#334155",
    lineColor: "#38bdf8",
    secondaryColor: "#0ea5e9",
    tertiaryColor: "#1e293b",
    fontFamily: "Inter, system-ui, sans-serif",
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

// Configure custom renderer for Marked to reliably isolate Mermaid blocks
const renderer = new marked.Renderer();
renderer.code = function (token: any, langParam?: string) {
  const text = typeof token === "string" ? token : token?.text || "";
  const lang = (typeof token === "object" && token?.lang ? token.lang : langParam || "")
    .trim()
    .toLowerCase();

  if (lang === "mermaid" || lang.startsWith("mermaid")) {
    const safeCode = encodeURIComponent(text.trim());
    return `<div class="mermaid-container my-8 p-4 rounded-2xl bg-base-300/60 border border-base-300 flex justify-center overflow-x-auto" data-mermaid-code="${safeCode}"></div>`;
  }
  const escaped = typeof token === "object" && token?.escaped ? text : escapeHtml(text);
  return `<pre class="bg-base-300 p-4 rounded-xl overflow-x-auto text-xs font-mono text-slate-200 my-4"><code>${escaped}</code></pre>`;
};

marked.use({ renderer });

async function renderMermaidDiagrams() {
  if (!markdownContainer.value) return;
  const containers = markdownContainer.value.querySelectorAll<HTMLElement>(".mermaid-container");
  for (let i = 0; i < containers.length; i++) {
    const el = containers[i];
    const code = decodeURIComponent(el.getAttribute("data-mermaid-code") || "");
    if (code) {
      const svgId = `mermaid-svg-${Date.now()}-${i}-${Math.random().toString(36).substring(2, 7)}`;
      try {
        const { svg } = await mermaid.render(svgId, code);
        el.innerHTML = svg;
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
