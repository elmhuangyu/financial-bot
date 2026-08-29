<script setup lang="ts">
import { computed } from "vue";
import { useCurrency } from "../composables/useCurrency";
import { usePrivacy } from "../composables/usePrivacy";
import { useRuns } from "../composables/useRuns";
import { useSidebar } from "../composables/useSidebar";
import { useTheme } from "../composables/useTheme";
import { TrendingUp, Eye, EyeOff, RefreshCw, Palette } from "lucide-vue-next";

const { currentCurrency, setCurrency } = useCurrency();
const { isPrivacyMode, togglePrivacy } = usePrivacy();
const { runs, currentRunId, loadRunData, isLoading } = useRuns();
const { isSidebarCollapsed, toggleSidebar } = useSidebar();
const { themes, currentTheme, setTheme } = useTheme();

const currentRunBadge = computed(() => {
  const run = runs.value.find((r) => r.id === currentRunId.value);
  if (!run) return currentRunId.value === "current" ? "Current Session" : currentRunId.value;
  if (run.name) return run.name;
  return run.isCurrent ? "Current Session" : run.id;
});
</script>

<template>
  <header
    class="relative z-30 shrink-0 bg-base-200/80 backdrop-blur-md border-b border-base-300 px-4 lg:px-6 py-3"
  >
    <div class="w-full flex flex-wrap items-center justify-between gap-3">
      <!-- Left: Brand (Clickable to Expand when collapsed) -->
      <div class="flex items-center gap-3">
        <button
          type="button"
          @click="isSidebarCollapsed ? toggleSidebar() : null"
          class="p-2 bg-gradient-to-tr from-primary to-secondary rounded-xl shadow-md text-white transition-all flex items-center justify-center"
          :class="
            isSidebarCollapsed
              ? 'cursor-pointer hover:scale-105 hover:shadow-lg active:scale-95'
              : 'cursor-default'
          "
          :title="isSidebarCollapsed ? 'Click to expand sidebar' : undefined"
          :aria-label="isSidebarCollapsed ? 'Expand Sidebar' : 'Financial Intelligence Brand Icon'"
        >
          <TrendingUp class="w-5 h-5" />
        </button>
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-base font-bold tracking-tight text-base-content">
              Financial Intelligence
            </h1>
            <span
              class="badge badge-sm badge-tag-sky font-semibold max-w-[200px] truncate"
              :title="currentRunBadge"
            >
              {{ currentRunBadge }}
            </span>
          </div>
          <p class="text-xs text-base-content/60 hidden sm:block">
            Deterministic Analytics • Attribution & Asset Allocation
          </p>
        </div>
      </div>

      <!-- Right: Global Controls (Privacy, Currency, Refresh, Theme) -->
      <div class="flex items-center gap-2">
        <!-- Refresh Button -->
        <button
          @click="loadRunData(currentRunId)"
          class="btn btn-ghost btn-sm btn-square text-base-content/60 hover:text-base-content"
          :class="{ 'animate-spin': isLoading }"
          title="Reload Run Data"
        >
          <RefreshCw class="w-4 h-4" />
        </button>

        <!-- Currency Selector -->
        <div class="join bg-base-300 rounded-lg p-0.5 border border-base-300">
          <button
            v-for="curr in ['USD', 'CAD'] as const"
            :key="curr"
            @click="setCurrency(curr)"
            class="join-item btn btn-xs border-none font-mono text-xs"
            :class="
              currentCurrency === curr
                ? 'btn-primary text-white shadow-xs font-bold'
                : 'btn-ghost text-base-content/70 hover:text-base-content'
            "
          >
            {{ curr }}
          </button>
        </div>

        <!-- Privacy Mode Toggle -->
        <button
          @click="togglePrivacy"
          class="btn btn-sm btn-ghost btn-square text-base-content/70 hover:text-base-content"
          :class="{ 'text-warning': isPrivacyMode }"
          :title="isPrivacyMode ? 'Disable Privacy Mode' : 'Enable Privacy Mode (Mask Numbers)'"
        >
          <EyeOff v-if="isPrivacyMode" class="w-4 h-4" />
          <Eye v-else class="w-4 h-4" />
        </button>

        <!-- Theme Selector Dropdown -->
        <div class="dropdown dropdown-end">
          <label
            tabindex="0"
            class="btn btn-sm btn-ghost btn-square text-base-content/70 hover:text-base-content"
            title="Select Theme"
          >
            <Palette class="w-4 h-4" />
          </label>
          <ul
            tabindex="0"
            class="dropdown-content z-50 menu p-2 shadow-2xl bg-base-200 border border-base-300 rounded-box w-52 text-xs space-y-1 mt-2 font-sans"
          >
            <li class="menu-title text-[10px] uppercase font-bold text-base-content/40 px-2 py-1">
              Select Theme
            </li>
            <li v-for="theme in themes" :key="theme.id">
              <button
                @click="setTheme(theme.id)"
                class="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-base-300 transition-colors"
                :class="{ 'active font-bold text-primary': currentTheme === theme.id }"
              >
                <span>{{ theme.label }}</span>
                <span
                  class="w-3 h-3 rounded-full border border-base-content/20"
                  :style="{
                    backgroundColor:
                      theme.id === 'business'
                        ? '#1c232b'
                        : theme.id === 'emerald'
                          ? '#66cc8a'
                          : theme.id === 'forest'
                            ? '#171212'
                            : theme.id === 'night'
                              ? '#0f172a'
                              : theme.id === 'dim'
                                ? '#2a303c'
                                : theme.id === 'nord'
                                  ? '#eceff4'
                                  : theme.id === 'corporate'
                                    ? '#ffffff'
                                    : '#f2f2f2',
                  }"
                ></span>
              </button>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </header>
</template>
