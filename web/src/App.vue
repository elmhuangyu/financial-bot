<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRuns } from "./composables/useRuns";
import { useSidebar } from "./composables/useSidebar";
import HeaderNav from "./components/HeaderNav.vue";
import ArchivedDrawer from "./components/ArchivedDrawer.vue";
import A2UIRenderer from "./components/a2ui/A2UIRenderer.vue";
import { ArrowUp } from "lucide-vue-next";

const { currentRunId, runManifest, isLoading, fetchRuns, loadRunData } = useRuns();
const { isSidebarCollapsed } = useSidebar();

const scrollViewport = ref<HTMLElement | null>(null);
const showBackToTop = ref<boolean>(false);

function handleScroll() {
  if (!scrollViewport.value) return;
  showBackToTop.value = scrollViewport.value.scrollTop > 300;
}

function scrollToTop() {
  scrollViewport.value?.scrollTo({
    top: 0,
    behavior: "smooth",
  });
}

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
      <div
        ref="scrollViewport"
        @scroll="handleScroll"
        class="flex-1 overflow-y-auto w-full flex flex-col relative"
      >
        <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">
          <div v-if="isLoading" class="flex justify-center items-center py-32">
            <span class="loading loading-spinner text-primary loading-lg"></span>
          </div>
          <A2UIRenderer v-else-if="runManifest" :manifest="runManifest" :run-id="currentRunId" />
          <div v-else class="text-center py-24 text-base-content/50">
            No report data found for this run.
          </div>
        </main>

        <!-- Footer -->
        <footer
          class="footer footer-center p-6 border-t border-base-300 text-xs text-base-content/50 mt-auto shrink-0"
        >
          <p>
            Financial Bot Modern Web Dashboard • Powered by Vue 3 + A2UI Declarative Schema + Hono
          </p>
        </footer>

        <!-- Floating Back to Top Button -->
        <Transition
          enter-active-class="transition duration-200 ease-out"
          enter-from-class="opacity-0 translate-y-3 scale-90"
          enter-to-class="opacity-100 translate-y-0 scale-100"
          leave-active-class="transition duration-150 ease-in"
          leave-from-class="opacity-100 translate-y-0 scale-100"
          leave-to-class="opacity-0 translate-y-3 scale-90"
        >
          <button
            v-show="showBackToTop"
            @click="scrollToTop"
            class="fixed bottom-8 right-8 z-50 btn btn-circle btn-primary shadow-xl shadow-primary/20 hover:shadow-primary/40 hover:scale-105 active:scale-95 transition-all text-primary-content border-none"
            title="Back to top"
            aria-label="Back to top"
          >
            <ArrowUp class="w-5 h-5" />
          </button>
        </Transition>
      </div>
    </div>
  </div>
</template>
