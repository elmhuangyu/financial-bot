<script setup lang="ts">
import { ref, watch, nextTick } from "vue";
import { marked } from "marked";
import mermaid from "mermaid";
import { FileText, Copy, Check } from "lucide-vue-next";

const props = defineProps<{
  runId: string;
  files: any[];
}>();

const selectedFile = ref<string>("");
const rawContent = ref<string>("");
const renderedHtml = ref<string>("");
const isLoading = ref<boolean>(false);
const copied = ref<boolean>(false);
const markdownContainer = ref<HTMLElement | null>(null);

const markdownFiles = ref<any[]>([]);
let currentFetchId = 0;

// Initialize Mermaid with Dark Financial Slate Theme
mermaid.initialize({
  startOnLoad: false,
  securityLevel: "loose",
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
    return `<div class="mermaid-container not-prose my-8 p-4 rounded-2xl bg-base-300/60 border border-base-300 flex justify-center overflow-x-auto" data-mermaid-code="${safeCode}"></div>`;
  }
  return `<pre class="bg-base-300 p-4 rounded-xl overflow-x-auto text-xs font-mono text-slate-200 my-4"><code>${text}</code></pre>`;
};

marked.use({ renderer });

watch(
  () => props.files,
  (newFiles) => {
    const validFiles = (newFiles || []).filter(
      (f) => f.type === "markdown" || f.name.endsWith(".md"),
    );
    markdownFiles.value = validFiles;
    if (validFiles.length > 0) {
      if (!selectedFile.value || !validFiles.some((f) => f.name === selectedFile.value)) {
        selectedFile.value = validFiles[0].name;
      }
    } else {
      selectedFile.value = "";
      rawContent.value = "";
      renderedHtml.value = "";
    }
  },
  { immediate: true },
);

watch(
  () => [props.runId, selectedFile.value],
  ([newRunId, newFile]) => {
    if (newRunId && newFile) {
      loadMarkdownContent();
    }
  },
  { immediate: true },
);

async function renderMermaidDiagrams() {
  await nextTick();
  if (!markdownContainer.value) return;

  const containers = markdownContainer.value.querySelectorAll<HTMLElement>(".mermaid-container");
  for (let i = 0; i < containers.length; i++) {
    const el = containers[i];
    const code = decodeURIComponent(el.getAttribute("data-mermaid-code") || "");
    if (code) {
      try {
        const svgId = `mermaid-svg-${Date.now()}-${i}-${Math.random().toString(36).substring(2, 7)}`;
        const { svg } = await mermaid.render(svgId, code);
        el.innerHTML = svg;
      } catch (mErr) {
        console.warn("Mermaid render error:", mErr);
        el.innerHTML = `<pre class="text-xs font-mono text-slate-300 bg-base-300 p-4 rounded-xl overflow-x-auto">${code}</pre>`;
      }
    }
  }
}

async function loadMarkdownContent() {
  if (!selectedFile.value || !props.runId) return;
  const fetchId = ++currentFetchId;
  isLoading.value = true;
  try {
    const res = await fetch(
      `/api/runs/${props.runId}/file?name=${encodeURIComponent(selectedFile.value)}`,
    );
    if (fetchId !== currentFetchId) return;
    if (res.ok) {
      rawContent.value = await res.text();
      renderedHtml.value = marked.parse(rawContent.value) as string;
      isLoading.value = false;
      await renderMermaidDiagrams();
    }
  } catch (e) {
    console.error(e);
  } finally {
    if (fetchId === currentFetchId) {
      isLoading.value = false;
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
</script>

<template>
  <div class="space-y-4">
    <!-- File Selector & Copy Bar -->
    <div
      class="card bg-base-200 border border-base-300 p-4 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3"
    >
      <div class="flex items-center gap-3 w-full sm:w-auto">
        <FileText class="w-5 h-5 text-primary" />
        <select
          v-model="selectedFile"
          class="select select-sm select-bordered bg-base-300 text-xs font-semibold rounded-lg w-full sm:w-80"
        >
          <option v-for="f in markdownFiles" :key="f.name" :value="f.name">{{ f.name }}</option>
        </select>
      </div>

      <button
        @click="copyContent"
        class="btn btn-sm btn-outline border-base-300 gap-1.5 text-xs text-slate-300 hover:text-white"
      >
        <component :is="copied ? Check : Copy" class="w-4 h-4 text-primary" />
        <span>{{ copied ? "Copied" : "Copy Markdown" }}</span>
      </button>
    </div>

    <!-- Rendered Markdown Container with Mermaid support & Generous Spacing -->
    <div class="card bg-base-200 border border-base-300 p-6 sm:p-8 shadow-sm min-h-[400px]">
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
  </div>
</template>
