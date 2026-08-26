<script setup lang="ts">
import { computed } from 'vue'
import { useCurrency } from '../composables/useCurrency'
import { usePrivacy } from '../composables/usePrivacy'
import { PieChart as PieIcon, Scan, Focus, BadgeDollarSign, Users } from 'lucide-vue-next'

const props = defineProps<{
  summary: any
}>()

const { formatMoney } = useCurrency()
const { isPrivacyMode } = usePrivacy()

const assetClasses = computed(() => props.summary?.asset_class_data || {})
const singleStocks = computed(() => props.summary?.single_stocks || [])
const taxAllocations = computed(() => props.summary?.tax_allocation || {})
const ownerAllocations = computed(() => props.summary?.owner_allocation || {})
const sectors = computed(() => props.summary?.sectors_lookthrough || {})

const colors = ['bg-emerald-500', 'bg-amber-500', 'bg-sky-500', 'bg-indigo-500', 'bg-pink-500', 'bg-purple-500']
</script>

<template>
  <div class="space-y-6">
    <!-- Macro Asset Classes & Sector Exposure Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Asset Class Breakdown -->
      <div class="card bg-base-200 border border-base-300 p-6 shadow-sm">
        <div class="flex items-center justify-between pb-3 border-b border-base-300">
          <div>
            <h3 class="text-base font-bold text-white flex items-center gap-2">
              <PieIcon class="w-5 h-5 text-primary" /> Asset Class Allocation
            </h3>
            <p class="text-xs text-slate-400">Macro breakdown across broad asset categories</p>
          </div>
        </div>

        <div class="mt-4 space-y-3">
          <div v-for="([k, v], idx) in Object.entries(assetClasses)" :key="k" class="space-y-1">
            <div class="flex justify-between text-xs font-medium">
              <span class="text-slate-300 flex items-center gap-2">
                <span class="w-2.5 h-2.5 rounded-full" :class="colors[idx % colors.length]"></span>
                {{ k }}
              </span>
              <span class="font-mono text-slate-100 font-bold">
                {{ v.pct.toFixed(2) }}% 
                <span class="text-slate-400 font-normal">({{ formatMoney(v.val, isPrivacyMode) }})</span>
              </span>
            </div>
            <!-- Progress Bar -->
            <div class="w-full bg-base-300 h-2 rounded-full overflow-hidden">
              <div class="h-full rounded-full transition-all" :class="colors[idx % colors.length]" :style="{ width: `${v.pct}%` }"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Sector Exposure -->
      <div class="card bg-base-200 border border-base-300 p-6 shadow-sm">
        <div class="flex items-center justify-between pb-3 border-b border-base-300">
          <div>
            <h3 class="text-base font-bold text-white flex items-center gap-2">
              <Scan class="w-5 h-5 text-secondary" /> Sector Allocation
            </h3>
            <p class="text-xs text-slate-400">Direct holdings & sector weightings</p>
          </div>
        </div>

        <div class="mt-4 space-y-2.5 max-h-72 overflow-y-auto pr-1">
          <div v-for="[sec, s] in Object.entries(sectors)" :key="sec" class="space-y-1">
            <div class="flex justify-between text-xs">
              <span class="text-slate-300 truncate max-w-[200px]">{{ sec }}</span>
              <span class="font-mono text-slate-200 font-bold">
                {{ s.pct.toFixed(2) }}% 
                <span class="text-slate-400 font-normal">({{ formatMoney(s.total, isPrivacyMode) }})</span>
              </span>
            </div>
            <div class="w-full bg-base-300 h-2 rounded-full overflow-hidden">
              <div class="h-full bg-secondary rounded-full" :style="{ width: `${s.pct}%` }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Single Stock Concentration Table -->
    <div class="card bg-base-200 border border-base-300 p-6 shadow-sm">
      <div class="flex items-center justify-between pb-3 border-b border-base-300">
        <div>
          <h3 class="text-base font-bold text-white flex items-center gap-2">
            <Focus class="w-5 h-5 text-primary" /> Top Single-Asset Concentration
          </h3>
          <p class="text-xs text-slate-400">Consolidated exposure ranking across top underlying assets</p>
        </div>
      </div>

      <div class="overflow-x-auto mt-4">
        <table class="table table-xs w-full font-mono">
          <thead>
            <tr class="text-slate-400 border-b border-base-300 uppercase font-sans">
              <th>Rank</th>
              <th>Symbol</th>
              <th>Asset Name</th>
              <th class="text-right">Direct Value</th>
              <th class="text-right font-bold text-white">Total Exposure</th>
              <th class="text-right font-bold text-primary">% Portfolio</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-base-300/60">
            <tr v-for="(s, idx) in singleStocks" :key="s.symbol" class="hover:bg-base-300/40">
              <td class="font-bold text-slate-500">{{ idx + 1 }}</td>
              <td class="font-bold text-white">{{ s.symbol }}</td>
              <td class="text-slate-300 font-sans truncate max-w-xs">{{ s.name }}</td>
              <td class="text-right text-slate-300">{{ formatMoney(s.direct, isPrivacyMode) }}</td>
              <td class="text-right font-bold text-white">{{ formatMoney(s.total, isPrivacyMode) }}</td>
              <td class="text-right font-bold text-primary">{{ s.pct.toFixed(2) }}%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Tax & Ownership Breakdown Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
      <!-- Tax Allocation -->
      <div class="card bg-base-200 border border-base-300 p-5 shadow-sm">
        <h4 class="text-sm font-bold text-white flex items-center gap-2 mb-3">
          <BadgeDollarSign class="w-4 h-4 text-emerald-400" /> Tax Structure Allocation
        </h4>
        <div class="space-y-3">
          <div v-for="[tax, t] in Object.entries(taxAllocations)" :key="tax" class="space-y-1">
            <div class="flex justify-between text-xs">
              <span class="text-slate-300">{{ tax }}</span>
              <span class="font-mono text-slate-100 font-bold">
                {{ t.pct.toFixed(2) }}% 
                <span class="text-slate-400 font-normal">({{ formatMoney(t.val, isPrivacyMode) }})</span>
              </span>
            </div>
            <div class="w-full bg-base-300 h-2 rounded-full overflow-hidden">
              <div 
                class="h-full rounded-full"
                :class="tax === 'Tax-Free' ? 'bg-emerald-500' : tax === 'Tax-Deferred' ? 'bg-amber-500' : 'bg-sky-500'"
                :style="{ width: `${t.pct}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Owner Allocation -->
      <div class="card bg-base-200 border border-base-300 p-5 shadow-sm">
        <h4 class="text-sm font-bold text-white flex items-center gap-2 mb-3">
          <Users class="w-4 h-4 text-sky-400" /> Account Owner Allocation
        </h4>
        <div class="space-y-3">
          <div v-for="[owner, o] in Object.entries(ownerAllocations)" :key="owner" class="space-y-1">
            <div class="flex justify-between text-xs">
              <span class="text-slate-300">{{ owner }}</span>
              <span class="font-mono text-slate-100 font-bold">
                {{ o.pct.toFixed(2) }}% 
                <span class="text-slate-400 font-normal">({{ formatMoney(o.val, isPrivacyMode) }})</span>
              </span>
            </div>
            <div class="w-full bg-base-300 h-2 rounded-full overflow-hidden">
              <div class="h-full bg-sky-500 rounded-full" :style="{ width: `${o.pct}%` }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
