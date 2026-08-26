<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import { marked } from "marked";
import { FileText, Copy, Check } from "lucide-vue-next";

const props = defineProps<{
  runId: string;
  files: any[];
}>();

const selectedFile = ref<string>("");
const content = ref<string>("");
const isLoading = ref<boolean>(false);
const copied = ref<boolean>(false);

const markdownFiles = ref<any[]>([]);

watch(
  () => props.files,
  (newFiles) => {
    markdownFiles.value = newFiles.filter((f) => f.type === "markdown" || f.name.endsWith(".md"));
    if (
      markdownFiles.value.length > 0 &&
      (!selectedFile.value || !markdownFiles.value.some((f) => f.name === selectedFile.value))
    ) {
      selectedFile.value = markdownFiles.value[0].name;
      loadMarkdownContent();
    }
  },
  { immediate: true },
);

watch(selectedFile, () => {
  loadMarkdownContent();
});

async function loadMarkdownContent() {
  if (!selectedFile.value) return;
  isLoading.value = true;
  try {
    const res = await fetch(
      `/api/runs/${props.runId}/file?name=${encodeURIComponent(selectedFile.value)}`,
    );
    if (res.ok) {
      content.value = await res.text();
    }
  } catch (e) {
    console.error(e);
  } finally {
    isLoading.value = false;
  }
}

function copyContent() {
  navigator.clipboard.writeText(content.value);
  copied.value = true;
  setTimeout(() => {
    copied.value = false;
  }, 2000);
}

function renderMarkdown(raw: string): string {
  return marked.parse(raw) as string;
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
          class="select select-sm select-bordered bg-base-300 text-xs font-semibold rounded-lg w-full sm:w-72"
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

    <!-- Rendered Markdown Container -->
    <div class="card bg-base-200 border border-base-300 p-6 shadow-sm min-h-[400px]">
      <div v-if="isLoading" class="flex justify-center items-center py-20">
        <span class="loading loading-spinner text-primary loading-lg"></span>
      </div>
      <div
        v-else
        class="prose prose-invert prose-slate max-w-none prose-headings:text-white prose-table:border-base-300 prose-th:bg-base-300/60 prose-th:p-2 prose-td:p-2 prose-th:text-xs prose-td:text-xs prose-td:font-mono text-sm leading-relaxed"
        v-html="renderMarkdown(content)"
      ></div>
    </div>
  </div>
</template>
