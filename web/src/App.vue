<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { useRuns } from "./composables/useRuns";
import { useSidebar } from "./composables/useSidebar";
import HeaderNav from "./components/HeaderNav.vue";
import ArchivedDrawer from "./components/ArchivedDrawer.vue";
import KpiStats from "./components/KpiStats.vue";
import AllocationTab from "./components/AllocationTab.vue";
import AttributionTab from "./components/AttributionTab.vue";
import HoldingsExplorer from "./components/HoldingsExplorer.vue";
import MarkdownViewer from "./components/MarkdownViewer.vue";
import RawCsvInspector from "./components/RawCsvInspector.vue";
import { Layers, Activity, Table2, FileText, Database } from "lucide-vue-next";

const { currentRunId, runSummary, runFiles, isLoading, fetchRuns, loadRunData } = useRuns();
const { isSidebarCollapsed } = useSidebar();

const activeTab = ref<"allocation" | "attribution" | "holdings" | "markdown" | "raw">("allocation");

const hasAttribution = computed(() => {
  return (
    runSummary.value?.has_brinson || runSummary.value?.has_risk || runSummary.value?.has_symbols
  );
});

const hasHoldings = computed(() => {
  return runSummary.value?.has_holdings;
});

const hasMarkdown = computed(() => {
  return runFiles.value.some((f) => f.type === "markdown" || f.name.endsWith(".md"));
});

const hasCsv = computed(() => {
  return runFiles.value.some((f) => f.type === "csv" || f.name.endsWith(".csv"));
});

watch(hasAttribution, (hasAttr) => {
  if (!hasAttr && activeTab.value === "attribution") {
    activeTab.value = hasHoldings.value ? "allocation" : hasMarkdown.value ? "markdown" : "raw";
  }
});

onMounted(async () => {
  await fetchRuns();
  await loadRunData(currentRunId.value);
});
</script>

<template>
  <div class="min-h-screen bg-base-100 font-sans flex flex-row w-full overflow-x-hidden">
    <!-- Collapsible Sidebar (Drawer) -->
    <div
      class="transition-all duration-300 ease-in-out overflow-hidden z-30 shrink-0 border-r border-base-300"
      :class="isSidebarCollapsed ? 'w-0 border-none' : 'w-64'"
    >
      <ArchivedDrawer />
    </div>

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col min-w-0">
      <HeaderNav />

      <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">
        <!-- Top KPI Stats Grid (Dynamic) -->
        <KpiStats :summary="runSummary" />

        <!-- Navigation Tabs -->
        <div
          class="tabs tabs-boxed bg-base-200 p-1.5 rounded-2xl border border-base-300 flex flex-wrap gap-1"
        >
          <a
            v-if="hasHoldings"
            @click="activeTab = 'allocation'"
            class="tab text-xs sm:text-sm font-semibold rounded-xl transition-all flex items-center gap-1.5"
            :class="
              activeTab === 'allocation'
                ? 'tab-active bg-primary text-white font-bold shadow-md'
                : 'text-slate-400 hover:text-white'
            "
          >
            <Layers class="w-4 h-4" />
            Asset Allocation & Look-Through
          </a>

          <a
            v-if="hasAttribution"
            @click="activeTab = 'attribution'"
            class="tab text-xs sm:text-sm font-semibold rounded-xl transition-all flex items-center gap-1.5"
            :class="
              activeTab === 'attribution'
                ? 'tab-active bg-secondary text-white font-bold shadow-md'
                : 'text-slate-400 hover:text-white'
            "
          >
            <Activity class="w-4 h-4" />
            Attribution & Factor Risk
          </a>

          <a
            v-if="hasHoldings"
            @click="activeTab = 'holdings'"
            class="tab text-xs sm:text-sm font-semibold rounded-xl transition-all flex items-center gap-1.5"
            :class="
              activeTab === 'holdings'
                ? 'tab-active bg-primary text-white font-bold shadow-md'
                : 'text-slate-400 hover:text-white'
            "
          >
            <Table2 class="w-4 h-4" />
            Holdings Explorer
          </a>

          <a
            v-if="hasMarkdown"
            @click="activeTab = 'markdown'"
            class="tab text-xs sm:text-sm font-semibold rounded-xl transition-all flex items-center gap-1.5"
            :class="
              activeTab === 'markdown'
                ? 'tab-active bg-accent text-slate-900 font-bold shadow-md'
                : 'text-slate-400 hover:text-white'
            "
          >
            <FileText class="w-4 h-4" />
            Markdown Reports
          </a>

          <a
            v-if="hasCsv"
            @click="activeTab = 'raw'"
            class="tab text-xs sm:text-sm font-semibold rounded-xl transition-all flex items-center gap-1.5"
            :class="
              activeTab === 'raw'
                ? 'tab-active bg-secondary text-white font-bold shadow-md'
                : 'text-slate-400 hover:text-white'
            "
          >
            <Database class="w-4 h-4" />
            Raw Data (CSVs)
          </a>
        </div>

        <!-- Tab Content Views -->
        <div v-if="isLoading" class="flex justify-center items-center py-24">
          <span class="loading loading-spinner text-primary loading-lg"></span>
        </div>
        <div v-else>
          <AllocationTab v-if="activeTab === 'allocation' && hasHoldings" :summary="runSummary" />
          <AttributionTab
            v-if="activeTab === 'attribution' && hasAttribution"
            :summary="runSummary"
          />
          <HoldingsExplorer v-if="activeTab === 'holdings' && hasHoldings" :summary="runSummary" />
          <MarkdownViewer
            v-if="activeTab === 'markdown' && hasMarkdown"
            :run-id="currentRunId"
            :files="runFiles"
          />
          <RawCsvInspector
            v-if="activeTab === 'raw' && hasCsv"
            :run-id="currentRunId"
            :files="runFiles"
          />
        </div>
      </main>

      <!-- Footer -->
      <footer
        class="footer footer-center p-6 border-t border-base-300 text-xs text-slate-500 mt-auto"
      >
        <p>
          Financial Bot Modern Web Dashboard • Powered by Vue 3 + DaisyUI + Hono • Fully
          Deterministic Analysis
        </p>
      </footer>
    </div>
  </div>
</template>
