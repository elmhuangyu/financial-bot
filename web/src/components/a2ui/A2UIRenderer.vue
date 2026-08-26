<script setup lang="ts">
import { ref, computed, watch } from "vue";
import type { A2UIManifest, A2UITab } from "../../types/a2ui";
import A2UIKpiGrid from "./A2UIKpiGrid.vue";
import A2UIChart from "./A2UIChart.vue";
import A2UIDataTable from "./A2UIDataTable.vue";
import A2UIHoldingsTable from "./A2UIHoldingsTable.vue";
import A2UIMarkdown from "./A2UIMarkdown.vue";
import A2UIKeyValList from "./A2UIKeyValList.vue";
import {
  Layers,
  Activity,
  Table2,
  FileText,
  Database,
  PieChart,
  LineChart,
  ShieldCheck,
  Coins,
} from "lucide-vue-next";

const props = defineProps<{
  manifest: A2UIManifest;
  runId: string;
}>();

const activeTabId = ref<string>("");

const sortedTabs = computed<A2UITab[]>(() => {
  if (!props.manifest?.tabs) return [];
  return [...props.manifest.tabs].sort((a, b) =>
    (a.label || "").localeCompare(b.label || "", undefined, { sensitivity: "base" }),
  );
});

const iconMap: Record<string, any> = {
  layers: Layers,
  activity: Activity,
  table: Table2,
  "file-text": FileText,
  database: Database,
  "pie-chart": PieChart,
  "line-chart": LineChart,
  shield: ShieldCheck,
  coins: Coins,
};

function getTabIcon(name?: string) {
  if (!name) return Layers;
  return iconMap[name.toLowerCase()] || Layers;
}

watch(
  sortedTabs,
  (newTabs) => {
    if (newTabs && newTabs.length > 0) {
      if (!activeTabId.value || !newTabs.some((t) => t.id === activeTabId.value)) {
        activeTabId.value = newTabs[0].id;
      }
    }
  },
  { immediate: true },
);

function getActiveTab(): A2UITab | undefined {
  return sortedTabs.value.find((t) => t.id === activeTabId.value) || sortedTabs.value[0];
}
</script>

<template>
  <div v-if="manifest" class="space-y-6">
    <!-- Top Declarative KPI Cards Grid -->
    <A2UIKpiGrid v-if="manifest.kpis && manifest.kpis.length > 0" :kpis="manifest.kpis" />

    <!-- Dynamic Tabs Bar -->
    <div
      v-if="sortedTabs && sortedTabs.length > 0"
      class="tabs tabs-boxed bg-base-200 p-1.5 rounded-2xl border border-base-300 flex flex-wrap gap-1"
    >
      <a
        v-for="tab in sortedTabs"
        :key="tab.id"
        @click="activeTabId = tab.id"
        class="tab text-xs sm:text-sm font-semibold rounded-xl transition-all flex items-center gap-1.5"
        :class="
          activeTabId === tab.id
            ? 'tab-active bg-primary text-primary-content font-bold shadow-md'
            : 'text-base-content/70 hover:text-base-content'
        "
      >
        <component :is="getTabIcon(tab.icon)" class="w-4 h-4" />
        {{ tab.label }}
      </a>
    </div>

    <!-- Active Tab Widgets Container -->
    <div v-if="getActiveTab()" class="space-y-6">
      <!-- Grid-2 Layout -->
      <div v-if="getActiveTab()?.layout === 'grid-2'" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <template v-for="w in getActiveTab()?.widgets" :key="w.id">
          <div :class="w.colSpan === 2 ? 'lg:col-span-2' : ''">
            <A2UIChart v-if="w.type === 'chart'" :widget="w as any" />
            <A2UIHoldingsTable
              v-else-if="w.type === 'holdings-table'"
              :widget="w as any"
              :run-id="runId"
            />
            <A2UIDataTable v-else-if="w.type === 'data-table'" :widget="w as any" :run-id="runId" />
            <A2UIMarkdown v-else-if="w.type === 'markdown'" :widget="w as any" :run-id="runId" />
            <A2UIKeyValList v-else-if="w.type === 'key-val-list'" :widget="w as any" />
          </div>
        </template>
      </div>

      <!-- Stacked Layout (Default) -->
      <div v-else class="space-y-6">
        <template v-for="w in getActiveTab()?.widgets" :key="w.id">
          <A2UIChart v-if="w.type === 'chart'" :widget="w as any" />
          <A2UIHoldingsTable
            v-else-if="w.type === 'holdings-table'"
            :widget="w as any"
            :run-id="runId"
          />
          <A2UIDataTable v-else-if="w.type === 'data-table'" :widget="w as any" :run-id="runId" />
          <A2UIMarkdown v-else-if="w.type === 'markdown'" :widget="w as any" :run-id="runId" />
          <A2UIKeyValList v-else-if="w.type === 'key-val-list'" :widget="w as any" />
        </template>
      </div>
    </div>
  </div>
</template>
