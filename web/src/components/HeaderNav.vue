<script setup lang="ts">
import { useCurrency } from "../composables/useCurrency";
import { usePrivacy } from "../composables/usePrivacy";
import { useRuns } from "../composables/useRuns";
import { TrendingUp, Eye, EyeOff, Menu, RefreshCw, Palette } from "lucide-vue-next";

const { currentCurrency, setCurrency } = useCurrency();
const { isPrivacyMode, togglePrivacy } = usePrivacy();
const { currentRunId, loadRunData, isLoading } = useRuns();

const themes = ["darkFinancial", "night", "dim", "dark", "nord"];

function changeTheme(theme: string) {
  document.documentElement.setAttribute("data-theme", theme);
}
</script>

<template>
  <header
    class="sticky top-0 z-40 bg-base-200/80 backdrop-blur-md border-b border-base-300 px-4 lg:px-6 py-3"
  >
    <div class="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
      <!-- Left: Drawer Toggle & Brand -->
      <div class="flex items-center gap-3">
        <label
          for="drawer-runs"
          class="btn btn-ghost btn-sm btn-square lg:hidden"
          aria-label="Toggle Runs Drawer"
        >
          <Menu class="w-5 h-5" />
        </label>

        <div
          class="p-2 bg-gradient-to-tr from-primary to-secondary rounded-xl shadow-md text-white"
        >
          <TrendingUp class="w-5 h-5" />
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-base font-bold tracking-tight text-white">Financial Intelligence</h1>
            <span class="badge badge-sm badge-primary badge-outline font-semibold">
              {{ currentRunId === "current" ? "Current Session" : currentRunId }}
            </span>
          </div>
          <p class="text-xs text-slate-400 hidden sm:block">
            Deterministic Analytics • Attribution & Asset Allocation
          </p>
        </div>
      </div>

      <!-- Right: Global Controls (Privacy, Currency, Refresh, Theme) -->
      <div class="flex items-center gap-2">
        <!-- Refresh Button -->
        <button
          @click="loadRunData(currentRunId)"
          class="btn btn-ghost btn-sm btn-square"
          :class="{ 'animate-spin': isLoading }"
          title="Reload Run Data"
        >
          <RefreshCw class="w-4 h-4 text-slate-400 hover:text-white" />
        </button>

        <!-- Privacy Toggle -->
        <button
          @click="togglePrivacy"
          class="btn btn-sm gap-1.5 font-medium transition-all"
          :class="
            isPrivacyMode
              ? 'btn-secondary shadow-sm shadow-secondary/20'
              : 'btn-outline border-base-300 text-slate-300'
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
                : 'btn-ghost text-slate-400'
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
                : 'btn-ghost text-slate-400'
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
            class="btn btn-ghost btn-sm btn-square"
            title="Select Theme"
          >
            <Palette class="w-4 h-4 text-slate-400 hover:text-white" />
          </div>
          <ul
            tabindex="0"
            class="dropdown-content z-50 menu p-2 shadow-2xl bg-base-200 rounded-box w-36 border border-base-300 text-xs"
          >
            <li class="menu-title text-[10px] uppercase text-slate-500">Theme</li>
            <li v-for="t in themes" :key="t">
              <a @click="changeTheme(t)" class="capitalize">{{ t }}</a>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </header>
</template>
