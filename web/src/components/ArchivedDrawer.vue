<script setup lang="ts">
import { useRuns } from "../composables/useRuns";
import { useSidebar } from "../composables/useSidebar";
import { Clock, Archive, Sparkles, FolderKanban, CheckCircle2, ChevronLeft } from "lucide-vue-next";

const { runs, currentRunId, selectRun } = useRuns();
const { toggleSidebar } = useSidebar();

function formatDate(isoString: string): string {
  try {
    const d = new Date(isoString);
    return d.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return isoString;
  }
}
</script>

<template>
  <aside class="w-full bg-base-200 h-full flex flex-col p-4 text-base-content shrink-0 select-none">
    <div class="flex items-center justify-between px-2 pb-4 border-b border-base-300">
      <div class="flex items-center gap-2">
        <FolderKanban class="w-5 h-5 text-primary" />
        <span class="font-bold text-sm text-base-content">Execution Runs</span>
      </div>
      <button
        @click="toggleSidebar"
        class="btn btn-ghost btn-xs btn-square text-base-content/60 hover:text-base-content"
        title="Collapse Sidebar"
      >
        <ChevronLeft class="w-4 h-4" />
      </button>
    </div>

    <!-- Runs List -->
    <div class="mt-4 flex-1 space-y-4 overflow-y-auto pr-1">
      <!-- Current Session -->
      <div>
        <div
          class="text-[10px] uppercase tracking-wider font-bold text-base-content/50 px-2 mb-1.5 flex items-center gap-1"
        >
          <Sparkles class="w-3 h-3 text-primary" /> Active Workspace
        </div>
        <div class="space-y-1">
          <div v-for="run in runs.filter((r) => r.isCurrent)" :key="run.id">
            <button
              type="button"
              @click="selectRun(run.id)"
              class="w-full text-left flex items-center justify-between px-2.5 py-2 rounded-lg border border-transparent transition-colors duration-150 focus:outline-none"
              :class="
                currentRunId === run.id
                  ? 'bg-primary text-primary-content font-semibold shadow-sm'
                  : 'hover:bg-base-300 text-base-content/80'
              "
            >
              <div class="flex items-center gap-2 truncate">
                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shrink-0"></span>
                <span class="truncate text-xs">{{
                  run.name ? `Active (${run.name})` : run.label
                }}</span>
              </div>
              <CheckCircle2
                v-if="currentRunId === run.id"
                class="w-3.5 h-3.5 text-primary-content shrink-0"
              />
            </button>
          </div>
        </div>
      </div>

      <!-- Archived Runs -->
      <div>
        <div
          class="text-[10px] uppercase tracking-wider font-bold text-base-content/50 px-2 mb-1.5 flex items-center gap-1"
        >
          <Archive class="w-3 h-3 text-secondary" /> Historical Archive
        </div>

        <div
          v-if="runs.filter((r) => !r.isCurrent).length === 0"
          class="text-xs text-base-content/50 px-3 py-2 italic"
        >
          No archived runs found in archived/
        </div>

        <div class="space-y-1">
          <div v-for="run in runs.filter((r) => !r.isCurrent)" :key="run.id">
            <button
              type="button"
              @click="selectRun(run.id)"
              class="w-full text-left flex flex-col items-start px-2.5 py-2 rounded-lg border transition-colors duration-150 focus:outline-none"
              :class="
                currentRunId === run.id
                  ? 'bg-base-300 border-primary/50 text-base-content font-semibold'
                  : 'border-transparent hover:bg-base-300/60 text-base-content/70'
              "
            >
              <div class="flex items-center justify-between w-full">
                <span class="truncate text-xs font-medium text-base-content">
                  {{ run.name || run.id }}
                </span>
                <CheckCircle2
                  v-if="currentRunId === run.id"
                  class="w-3.5 h-3.5 text-primary shrink-0"
                />
              </div>
              <div
                class="text-[10px] text-base-content/50 flex items-center justify-between w-full mt-0.5"
              >
                <span class="flex items-center gap-1">
                  <Clock class="w-3 h-3 text-base-content/40" />
                  {{ formatDate(run.timestamp) }}
                </span>
                <span
                  v-if="run.name"
                  class="font-mono text-[9px] opacity-40 truncate max-w-[90px]"
                  :title="run.id"
                >
                  {{ run.id }}
                </span>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Drawer Footer -->
    <div class="pt-3 border-t border-base-300 text-[11px] text-base-content/50 text-center">
      <p>Financial Bot Web v0.1</p>
    </div>
  </aside>
</template>
