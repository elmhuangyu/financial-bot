<script setup lang="ts">
import { useRuns } from '../composables/useRuns'
import { Clock, Archive, Sparkles, FolderKanban, CheckCircle2 } from 'lucide-vue-next'

const { runs, currentRunId, selectRun, isLoading } = useRuns()

function formatDate(isoString: string): string {
  try {
    const d = new Date(isoString)
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return isoString
  }
}
</script>

<template>
  <aside class="w-64 bg-base-200 border-r border-base-300 min-h-screen flex flex-col p-4 text-slate-200">
    <div class="flex items-center gap-2 px-2 pb-4 border-b border-base-300">
      <FolderKanban class="w-5 h-5 text-primary" />
      <span class="font-bold text-sm text-white">Execution Runs</span>
    </div>

    <!-- Runs List -->
    <div class="mt-4 flex-1 space-y-4 overflow-y-auto">
      <!-- Current Session -->
      <div>
        <div class="text-[10px] uppercase tracking-wider font-bold text-slate-500 px-2 mb-1.5 flex items-center gap-1">
          <Sparkles class="w-3 h-3 text-primary" /> Active Workspace
        </div>
        <ul class="menu menu-sm p-0 gap-1">
          <li v-for="run in runs.filter(r => r.isCurrent)" :key="run.id">
            <a 
              @click="selectRun(run.id)"
              class="flex items-center justify-between p-2.5 rounded-xl transition-all"
              :class="currentRunId === run.id ? 'bg-primary text-white font-bold shadow-md' : 'hover:bg-base-300 text-slate-300'"
            >
              <div class="flex items-center gap-2 truncate">
                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span class="truncate">{{ run.label }}</span>
              </div>
              <CheckCircle2 v-if="currentRunId === run.id" class="w-4 h-4 text-white shrink-0" />
            </a>
          </li>
        </ul>
      </div>

      <!-- Archived Runs -->
      <div>
        <div class="text-[10px] uppercase tracking-wider font-bold text-slate-500 px-2 mb-1.5 flex items-center gap-1">
          <Archive class="w-3 h-3 text-secondary" /> Historical Archive
        </div>

        <div v-if="runs.filter(r => !r.isCurrent).length === 0" class="text-xs text-slate-500 px-3 py-2 italic">
          No archived runs found in archived/
        </div>

        <ul class="menu menu-sm p-0 gap-1">
          <li v-for="run in runs.filter(r => !r.isCurrent)" :key="run.id">
            <a 
              @click="selectRun(run.id)"
              class="flex flex-col items-start p-2.5 rounded-xl transition-all"
              :class="currentRunId === run.id ? 'bg-base-300 border border-primary/50 text-white font-semibold' : 'hover:bg-base-300/60 text-slate-400'"
            >
              <div class="flex items-center justify-between w-full">
                <span class="truncate text-xs">{{ run.id }}</span>
                <CheckCircle2 v-if="currentRunId === run.id" class="w-3.5 h-3.5 text-primary shrink-0" />
              </div>
              <span class="text-[10px] text-slate-500 flex items-center gap-1 mt-0.5">
                <Clock class="w-3 h-3" /> {{ formatDate(run.timestamp) }}
              </span>
            </a>
          </li>
        </ul>
      </div>
    </div>

    <!-- Drawer Footer -->
    <div class="pt-3 border-t border-base-300 text-[11px] text-slate-500 text-center">
      <p>Financial Bot Web v0.1</p>
    </div>
  </aside>
</template>
