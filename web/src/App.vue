<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRuns } from './composables/useRuns'
import HeaderNav from './components/HeaderNav.vue'
import ArchivedDrawer from './components/ArchivedDrawer.vue'
import KpiStats from './components/KpiStats.vue'
import AllocationTab from './components/AllocationTab.vue'
import AttributionTab from './components/AttributionTab.vue'
import HoldingsExplorer from './components/HoldingsExplorer.vue'
import MarkdownViewer from './components/MarkdownViewer.vue'
import RawCsvInspector from './components/RawCsvInspector.vue'
import { Layers, Activity, Table2, FileText, Database } from 'lucide-vue-next'

const { currentRunId, runSummary, runFiles, isLoading, fetchRuns, loadRunData } = useRuns()

const activeTab = ref<'allocation' | 'attribution' | 'holdings' | 'markdown' | 'raw'>('allocation')

onMounted(async () => {
  await fetchRuns()
  await loadRunData(currentRunId.value)
})
</script>

<template>
  <div class="drawer lg:drawer-open min-h-screen bg-base-100 font-sans">
    <input id="drawer-runs" type="checkbox" class="drawer-toggle" />

    <!-- Drawer Content (Main Page) -->
    <div class="drawer-content flex flex-col min-h-screen">
      <HeaderNav />

      <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">
        <!-- Top KPI Stats Grid -->
        <KpiStats :summary="runSummary" />

        <!-- Navigation Tabs (DaisyUI Tabs) -->
        <div class="tabs tabs-boxed bg-base-200 p-1.5 rounded-2xl border border-base-300 flex flex-wrap gap-1">
          <a 
            @click="activeTab = 'allocation'"
            class="tab text-xs sm:text-sm font-semibold rounded-xl transition-all flex items-center gap-1.5"
            :class="activeTab === 'allocation' ? 'tab-active bg-primary text-white font-bold shadow-md' : 'text-slate-400 hover:text-white'"
          >
            <Layers class="w-4 h-4" />
            Asset Allocation & Look-Through
          </a>
          <a 
            @click="activeTab = 'attribution'"
            class="tab text-xs sm:text-sm font-semibold rounded-xl transition-all flex items-center gap-1.5"
            :class="activeTab === 'attribution' ? 'tab-active bg-secondary text-white font-bold shadow-md' : 'text-slate-400 hover:text-white'"
          >
            <Activity class="w-4 h-4" />
            Attribution & Factor Risk
          </a>
          <a 
            @click="activeTab = 'holdings'"
            class="tab text-xs sm:text-sm font-semibold rounded-xl transition-all flex items-center gap-1.5"
            :class="activeTab === 'holdings' ? 'tab-active bg-primary text-white font-bold shadow-md' : 'text-slate-400 hover:text-white'"
          >
            <Table2 class="w-4 h-4" />
            Holdings Explorer
          </a>
          <a 
            @click="activeTab = 'markdown'"
            class="tab text-xs sm:text-sm font-semibold rounded-xl transition-all flex items-center gap-1.5"
            :class="activeTab === 'markdown' ? 'tab-active bg-accent text-slate-900 font-bold shadow-md' : 'text-slate-400 hover:text-white'"
          >
            <FileText class="w-4 h-4" />
            Markdown Reports
          </a>
          <a 
            @click="activeTab = 'raw'"
            class="tab text-xs sm:text-sm font-semibold rounded-xl transition-all flex items-center gap-1.5"
            :class="activeTab === 'raw' ? 'tab-active bg-secondary text-white font-bold shadow-md' : 'text-slate-400 hover:text-white'"
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
          <AllocationTab v-if="activeTab === 'allocation'" :summary="runSummary" />
          <AttributionTab v-if="activeTab === 'attribution'" :summary="runSummary" />
          <HoldingsExplorer v-if="activeTab === 'holdings'" :summary="runSummary" />
          <MarkdownViewer v-if="activeTab === 'markdown'" :run-id="currentRunId" :files="runFiles" />
          <RawCsvInspector v-if="activeTab === 'raw'" :run-id="currentRunId" :files="runFiles" />
        </div>
      </main>

      <!-- Footer -->
      <footer class="footer footer-center p-6 border-t border-base-300 text-xs text-slate-500 mt-auto">
        <p>Financial Bot Modern Web Dashboard • Powered by Vue 3 + DaisyUI + Hono • Fully Deterministic Analysis</p>
      </footer>
    </div>

    <!-- Drawer Side (Left Sidebar) -->
    <div class="drawer-side z-50">
      <label for="drawer-runs" aria-label="close sidebar" class="drawer-overlay"></label>
      <ArchivedDrawer />
    </div>
  </div>
</template>
