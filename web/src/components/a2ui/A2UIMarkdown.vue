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
});

// Configure custom renderer for Marked to reliably isolate Mermaid blocks
const renderer = new marked.Renderer();
renderer.code = function (token: any, langParam?: string) {
  const text = typeof token === "string" ? token : token?.text || "";
  const lang = typeof token === "object" && token?.lang ? token.lang : langParam || "";

  if (lang.trim().toLowerCase() === "mermaid") {
    const safeCode = encodeURIComponent(text.trim());
    return `<div class="mermaid-container my-8 p-4 rounded-2xl bg-base-300/60 border border-base-300 flex justify-center overflow-x-auto" data-mermaid-code="${safeCode}"></div>`;
  }
  return `<pre class="bg-base-300 p-4 rounded-xl overflow-x-auto text-xs font-mono text-slate-200 my-4"><code>${text}</code></pre>`;
};

marked.use({ renderer });

async function loadMarkdownContent() {
  if (props.widget.content) {
    rawContent.value = props.widget.content;
    renderHtmlAndMermaid();
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
        renderHtmlAndMermaid();
      }
    } catch (e) {
      console.error(e);
    } finally {
      isLoading.value = false;
    }
  }
}

async function renderHtmlAndMermaid() {
  renderedHtml.value = marked.parse(rawContent.value) as string;
  await nextTick();
  if (markdownContainer.value) {
    const containers = markdownContainer.value.querySelectorAll(".mermaid-container");
    for (let i = 0; i < containers.length; i++) {
      const el = containers[i] as HTMLElement;
      const code = decodeURIComponent(el.getAttribute("data-mermaid-code") || "");
      if (code) {
        try {
          const svgId = `mermaid-svg-${i}-${Math.random().toString(36).substring(2, 7)}`;
          const { svg } = await mermaid.render(svgId, code);
          el.innerHTML = svg;
        } catch (mErr) {
          console.warn("Mermaid render error:", mErr);
          el.innerHTML = `<pre class="text-xs font-mono text-slate-300 bg-base-300 p-4 rounded-xl overflow-x-auto">${code}</pre>`;
        }
      }
    }
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
        <h3 class="text-base font-bold text-white">
          {{ widget.title || widget.sourceMd || "Markdown Document" }}
        </h3>
      </div>
      <button
        @click="copyContent"
        class="btn btn-sm btn-outline border-base-300 gap-1.5 text-xs text-slate-300 hover:text-white"
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
      class="prose prose-invert prose-slate max-w-none prose-headings:text-white prose-table:border-base-300 prose-th:bg-base-300/60 prose-th:p-2.5 prose-td:p-2.5 prose-th:text-xs prose-td:text-xs prose-td:font-mono text-sm leading-relaxed"
      v-html="renderedHtml"
    ></div>
  </div>
</template>
