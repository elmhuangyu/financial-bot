<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from "vue";
import { marked } from "marked";
import katex from "katex";
import markedKatex from "marked-katex-extension";
import mermaid from "mermaid";
import type { A2UIMarkdownWidget } from "../../types/a2ui";
import { useTheme } from "../../composables/useTheme";
import { configureMermaidForTheme } from "../../utils/mermaidTheme";
import MermaidModal from "./MermaidModal.vue";
import { FileText, Copy, Check } from "lucide-vue-next";

const props = defineProps<{
  widget: A2UIMarkdownWidget;
  runId: string;
}>();

const { currentTheme } = useTheme();

const rawContent = ref<string>("");
const renderedHtml = ref<string>("");
const isLoading = ref<boolean>(false);
const copied = ref<boolean>(false);
const markdownContainer = ref<HTMLElement | null>(null);

// Mermaid zoom modal state
const isModalOpen = ref<boolean>(false);
const activeSvgHtml = ref<string>("");
let activeContainerEl: HTMLElement | null = null;

let themeObserver: MutationObserver | null = null;

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
    return `<div class="mermaid-block-wrapper relative group my-8">
      <div class="mermaid-container not-prose p-4 rounded-2xl bg-base-300/60 border border-base-300 flex justify-center overflow-x-auto cursor-zoom-in transition-colors hover:border-primary/40" data-mermaid-code="${safeCode}" title="Click to zoom and pan diagram"></div>
      <button
        type="button"
        class="mermaid-zoom-btn absolute top-3 right-3 btn btn-xs sm:btn-sm btn-neutral/90 hover:btn-primary backdrop-blur-md shadow-md border border-base-content/10 gap-1.5 opacity-90 sm:opacity-0 sm:group-hover:opacity-100 focus:opacity-100 transition-all duration-200 z-10 text-base-content hover:text-primary-content"
        title="Expand & Pan Diagram"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h6v6"/><path d="M9 21H3v-6"/><path d="M21 3l-7 7"/><path d="M3 21l7-7"/></svg>
        <span class="text-xs font-semibold">Expand</span>
      </button>
    </div>`;
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
  return `<pre class="bg-base-300 p-4 rounded-xl overflow-x-auto text-xs font-mono text-base-content my-4"><code>${escaped}</code></pre>`;
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

  // Dynamically re-configure mermaid with active DaisyUI theme colors
  configureMermaidForTheme();

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

  // Update active SVG modal if open
  if (isModalOpen.value && activeContainerEl) {
    const activeSvg = activeContainerEl.querySelector("svg");
    if (activeSvg) {
      activeSvgHtml.value = activeSvg.outerHTML;
    }
  }
}

function openModalForContainer(container: HTMLElement) {
  const svgEl = container.querySelector("svg");
  if (svgEl) {
    activeContainerEl = container;
    activeSvgHtml.value = svgEl.outerHTML;
    isModalOpen.value = true;
  }
}

function handleMarkdownClick(e: MouseEvent) {
  const target = e.target as HTMLElement | null;
  if (!target) return;

  const zoomBtn = target.closest<HTMLElement>(".mermaid-zoom-btn");
  if (zoomBtn) {
    e.preventDefault();
    e.stopPropagation();
    const wrapper = zoomBtn.closest<HTMLElement>(".mermaid-block-wrapper");
    const container = wrapper?.querySelector<HTMLElement>(".mermaid-container");
    if (container) {
      openModalForContainer(container);
    }
    return;
  }

  const container = target.closest<HTMLElement>(".mermaid-container");
  if (container && !target.closest("a, button, input, textarea, select")) {
    openModalForContainer(container);
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

  if (typeof MutationObserver !== "undefined" && typeof document !== "undefined") {
    themeObserver = new MutationObserver((mutations) => {
      for (const m of mutations) {
        if (m.type === "attributes" && m.attributeName === "data-theme") {
          renderMermaidDiagrams();
          break;
        }
      }
    });
    themeObserver.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });
  }
});

onBeforeUnmount(() => {
  if (themeObserver) {
    themeObserver.disconnect();
    themeObserver = null;
  }
});

watch(
  () => [props.widget, props.runId],
  () => {
    loadMarkdownContent();
  },
  { deep: true },
);

watch(currentTheme, async () => {
  await nextTick();
  await renderMermaidDiagrams();
});
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
      @click="handleMarkdownClick"
      class="prose max-w-none text-base-content prose-headings:text-base-content prose-p:text-base-content/90 prose-strong:text-base-content prose-table:border-base-300 prose-th:bg-base-300/60 prose-th:text-base-content prose-td:text-base-content/90 prose-th:p-2.5 prose-td:p-2.5 prose-th:text-xs prose-td:text-xs prose-td:font-mono text-sm leading-relaxed"
      v-html="renderedHtml"
    ></div>

    <!-- Mermaid Pan & Zoom Lightbox Modal -->
    <MermaidModal
      :is-open="isModalOpen"
      :svg-html="activeSvgHtml"
      :title="widget.title || 'Mermaid Diagram'"
      @close="isModalOpen = false"
    />
  </div>
</template>
