<script setup lang="ts">
import { ref, watch, computed } from "vue";
import { Table as TableIcon, Download, Search } from "lucide-vue-next";

const props = defineProps<{
  runId: string;
  files: any[];
}>();

const selectedFile = ref<string>("");
const csvHeaders = ref<string[]>([]);
const csvRows = ref<any[]>([]);
const isLoading = ref<boolean>(false);
const searchQuery = ref<string>("");

const csvFiles = computed(() => {
  return props.files.filter((f) => f.type === "csv" || f.name.endsWith(".csv"));
});

watch(
  csvFiles,
  (newFiles) => {
    if (
      newFiles.length > 0 &&
      (!selectedFile.value || !newFiles.some((f) => f.name === selectedFile.value))
    ) {
      selectedFile.value = newFiles[0].name;
      loadCsvData();
    }
  },
  { immediate: true },
);

watch(selectedFile, () => {
  loadCsvData();
});

async function loadCsvData() {
  if (!selectedFile.value) return;
  isLoading.value = true;
  try {
    const res = await fetch(
      `/api/runs/${props.runId}/file?name=${encodeURIComponent(selectedFile.value)}`,
    );
    if (res.ok) {
      const data = await res.json();
      csvHeaders.value = data.headers || [];
      csvRows.value = data.rows || [];
    }
  } catch (e) {
    console.error(e);
  } finally {
    isLoading.value = false;
  }
}

const filteredRows = computed(() => {
  if (!searchQuery.value) return csvRows.value;
  const q = searchQuery.value.toLowerCase();
  return csvRows.value.filter((row) => {
    return Object.values(row).some((v) => String(v).toLowerCase().includes(q));
  });
});

function exportCurrentCsv() {
  if (!csvRows.value.length) return;
  const csvContent = [
    csvHeaders.value.join(","),
    ...csvRows.value.map((row) =>
      csvHeaders.value.map((h) => `"${(row[h] || "").replace(/"/g, '""')}"`).join(","),
    ),
  ].join("\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = selectedFile.value || "export.csv";
  a.click();
  URL.revokeObjectURL(url);
}
</script>

<template>
  <div class="space-y-4">
    <!-- CSV Selector & Controls -->
    <div
      class="card bg-base-200 border border-base-300 p-4 shadow-sm flex flex-col md:flex-row items-center justify-between gap-3"
    >
      <div class="flex items-center gap-3 w-full md:w-auto">
        <TableIcon class="w-5 h-5 text-secondary" />
        <select
          v-model="selectedFile"
          class="select select-sm select-bordered bg-base-300 text-xs font-semibold rounded-lg w-full md:w-80"
        >
          <option v-for="f in csvFiles" :key="f.name" :value="f.name">{{ f.name }}</option>
        </select>
      </div>

      <div class="flex items-center gap-2 w-full md:w-auto">
        <div class="relative w-full md:w-64">
          <Search class="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search rows..."
            class="input input-sm input-bordered w-full pl-9 rounded-lg bg-base-300 border-base-300 text-xs"
          />
        </div>

        <button
          @click="exportCurrentCsv"
          class="btn btn-sm btn-outline border-base-300 gap-1.5 text-xs text-slate-300 hover:text-white"
        >
          <Download class="w-4 h-4 text-primary" />
          <span>Export</span>
        </button>
      </div>
    </div>

    <!-- Data Table -->
    <div class="card bg-base-200 border border-base-300 rounded-2xl overflow-hidden shadow-sm">
      <div v-if="isLoading" class="flex justify-center items-center py-20">
        <span class="loading loading-spinner text-primary loading-lg"></span>
      </div>
      <div v-else class="overflow-x-auto max-h-[600px]">
        <table class="table table-xs table-pin-rows font-mono">
          <thead>
            <tr class="text-slate-400 bg-base-300 font-sans uppercase">
              <th v-for="h in csvHeaders" :key="h">{{ h }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-base-300/60 text-slate-300">
            <tr v-for="(row, idx) in filteredRows" :key="idx" class="hover:bg-base-300/40">
              <td v-for="h in csvHeaders" :key="h" class="truncate max-w-xs">{{ row[h] }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="p-3 bg-base-300 text-xs text-slate-400 font-sans border-t border-base-300">
        Showing {{ filteredRows.length }} of {{ csvRows.length }} rows
      </div>
    </div>
  </div>
</template>
