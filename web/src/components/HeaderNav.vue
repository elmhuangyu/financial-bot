<script setup lang="ts">
import { computed } from "vue";
import { useCurrency } from "../composables/useCurrency";
import { usePrivacy } from "../composables/usePrivacy";
import { useRuns } from "../composables/useRuns";
import { useSidebar } from "../composables/useSidebar";
import { useTheme } from "../composables/useTheme";
import {
  TrendingUp,
  Eye,
  EyeOff,
  PanelLeftClose,
  PanelLeftOpen,
  RefreshCw,
  Palette,
} from "lucide-vue-next";

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
    class="shrink-0 bg-base-200/80 backdrop-blur-md border-b border-base-300 px-4 lg:px-6 py-3"
  >
    <div class="w-full flex flex-wrap items-center justify-between gap-3">
      <!-- Left: Sidebar Toggle & Brand -->
      <div class="flex items-center gap-3">
        <!-- Desktop & Mobile Sidebar Collapse Toggle Button -->
        <button
          @click="toggleSidebar"
          class="btn btn-ghost btn-sm btn-square text-base-content/60 hover:text-base-content"
          :title="isSidebarCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'"
          aria-label="Toggle Sidebar"
        >
          <component
            :is="isSidebarCollapsed ? PanelLeftOpen : PanelLeftClose"
            class="w-5 h-5 text-primary"
          />
        </button>

        <div
          class="p-2 bg-gradient-to-tr from-primary to-secondary rounded-xl shadow-md text-white"
        >
          <TrendingUp class="w-5 h-5" />
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-base font-bold tracking-tight text-base-content">
              Financial Intelligence
            </h1>
            <span
              class="badge badge-sm badge-primary badge-outline font-semibold max-w-[200px] truncate"
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

        <!-- Privacy Toggle -->
        <button
          @click="togglePrivacy"
          class="btn btn-sm gap-1.5 font-medium transition-all"
          :class="
            isPrivacyMode
              ? 'btn-secondary shadow-sm shadow-secondary/20'
              : 'btn-outline border-base-300 text-base-content/80 hover:text-base-content'
          "
          title="Toggle Privacy Mode (Mask Balances)"
        >
          <component :is="isPrivacyMode ? EyeOff : Eye" class="w-4 h-4" />
          <span class="text-xs">{{ isPrivacyMode ? "Hidden" : "Privacy" }}</span>
        </button>

        <!-- Dual Currency Switcher -->
        <div class="join bg-base-300 p-0.5 rounded-lg border border-base-300">
          <button
            @click="setCurrency('USD')"
            class="join-item btn btn-xs font-semibold px-2.5 transition-all"
            :class="
              currentCurrency === 'USD'
                ? 'btn-primary text-white shadow'
                : 'btn-ghost text-base-content/60 hover:text-base-content'
            "
          >
            USD ($)
          </button>
          <button
            @click="setCurrency('CAD')"
            class="join-item btn btn-xs font-semibold px-2.5 transition-all"
            :class="
              currentCurrency === 'CAD'
                ? 'btn-primary text-white shadow'
                : 'btn-ghost text-base-content/60 hover:text-base-content'
            "
          >
            CAD (C$)
          </button>
        </div>

        <!-- DaisyUI Official Theme Controller Dropdown -->
        <div class="dropdown dropdown-end">
          <div
            tabindex="0"
            role="button"
            class="btn btn-ghost btn-sm text-base-content/70 hover:text-base-content gap-1.5 font-normal text-xs"
          >
            <Palette class="w-4 h-4 text-primary" />
            <span class="hidden md:inline font-medium">Theme</span>
            <svg
              width="10px"
              height="10px"
              class="inline-block h-2 w-2 fill-current opacity-60 ml-0.5"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 2048 2048"
            >
              <path d="M1799 349l242 241-1017 1017L7 590l242-241 775 775 775-775z"></path>
            </svg>
          </div>
          <ul
            tabindex="-1"
            class="dropdown-content bg-base-300 rounded-box z-50 w-48 p-2 shadow-2xl border border-base-300 menu text-xs gap-1 mt-2"
          >
            <li v-for="t in themes" :key="t.id">
              <input
                type="radio"
                name="theme-dropdown"
                class="theme-controller w-full btn btn-sm btn-block btn-ghost justify-start text-xs font-normal"
                :aria-label="t.label"
                :value="t.id"
                :checked="currentTheme === t.id"
                @change="setTheme(t.id)"
              />
            </li>
          </ul>
        </div>
      </div>
    </div>
  </header>
</template>
