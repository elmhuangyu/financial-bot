<script setup lang="ts">
import { onMounted } from "vue";
import { useRuns } from "./composables/useRuns";
import { useSidebar } from "./composables/useSidebar";
import HeaderNav from "./components/HeaderNav.vue";
import ArchivedDrawer from "./components/ArchivedDrawer.vue";
import A2UIRenderer from "./components/a2ui/A2UIRenderer.vue";

const { currentRunId, runManifest, isLoading, fetchRuns, loadRunData } = useRuns();
const { isSidebarCollapsed } = useSidebar();

onMounted(async () => {
  await fetchRuns();
  await loadRunData(currentRunId.value);
});
</script>

<template>
  <div class="h-screen w-screen flex flex-row bg-base-100 font-sans overflow-hidden">
    <!-- Collapsible Sidebar (Drawer) -->
    <div
      class="h-full transition-all duration-300 ease-in-out overflow-hidden z-30 shrink-0 border-r border-base-300 flex flex-col"
      :class="isSidebarCollapsed ? 'w-0 border-none' : 'w-64'"
    >
      <ArchivedDrawer />
    </div>

    <!-- Main Content Column Area -->
    <div class="flex-1 flex flex-col h-full min-w-0 overflow-hidden">
      <HeaderNav />

      <!-- Scrollable Main Viewport Container -->
      <div class="flex-1 overflow-y-auto w-full flex flex-col">
        <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">
          <div v-if="isLoading" class="flex justify-center items-center py-32">
            <span class="loading loading-spinner text-primary loading-lg"></span>
          </div>
          <A2UIRenderer v-else-if="runManifest" :manifest="runManifest" :run-id="currentRunId" />
          <div v-else class="text-center py-24 text-slate-500">
            No report data found for this run.
          </div>
        </main>

        <!-- Footer -->
        <footer
          class="footer footer-center p-6 border-t border-base-300 text-xs text-slate-500 mt-auto shrink-0"
        >
          <p>
            Financial Bot Modern Web Dashboard • Powered by Vue 3 + A2UI Declarative Schema + Hono
          </p>
        </footer>
      </div>
    </div>
  </div>
</template>
