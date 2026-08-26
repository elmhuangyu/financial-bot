<script setup lang="ts">
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
  Check,
} from "lucide-vue-next";

const { currentCurrency, setCurrency } = useCurrency();
const { isPrivacyMode, togglePrivacy } = usePrivacy();
const { currentRunId, loadRunData, isLoading } = useRuns();
const { isSidebarCollapsed, toggleSidebar } = useSidebar();
const { themes, currentTheme, setTheme } = useTheme();
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
            <span class="badge badge-sm badge-primary badge-outline font-semibold">
              {{ currentRunId === "current" ? "Current Session" : currentRunId }}
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

        <!-- Theme Dropdown -->
        <div class="dropdown dropdown-end">
          <div
            tabindex="0"
            role="button"
            class="btn btn-ghost btn-sm btn-square text-base-content/60 hover:text-base-content"
            title="Select Theme"
          >
            <Palette class="w-4 h-4" />
          </div>
          <ul
            tabindex="0"
            class="dropdown-content z-50 menu p-1.5 shadow-2xl bg-base-200 rounded-2xl w-44 border border-base-300 text-xs gap-0.5"
          >
            <li class="menu-title text-[10px] uppercase text-base-content/50 px-2 py-1">Theme</li>
            <li v-for="t in themes" :key="t.id">
              <a
                @click="setTheme(t.id)"
                class="flex items-center justify-between py-1.5 px-2.5 rounded-lg transition-all"
                :class="
                  currentTheme === t.id
                    ? 'bg-primary/15 text-primary font-bold'
                    : 'text-base-content/80 hover:bg-base-300'
                "
              >
                <span>{{ t.label }}</span>
                <Check v-if="currentTheme === t.id" class="w-3.5 h-3.5 text-primary shrink-0" />
              </a>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </header>
</template>
