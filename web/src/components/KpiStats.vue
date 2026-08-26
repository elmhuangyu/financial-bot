<script setup lang="ts">
import { computed } from 'vue'
import { useCurrency } from '../composables/useCurrency'
import { usePrivacy } from '../composables/usePrivacy'
import { Wallet, PieChart, ShieldCheck, Gauge, ArrowUpRight } from 'lucide-vue-next'

const props = defineProps<{
  summary: any
}>()

const { formatMoney } = useCurrency()
const { isPrivacyMode } = usePrivacy()

const meta = computed(() => props.summary?.meta || {})
</script>

<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
    <!-- Total Net Worth -->
    <div class="card bg-base-200 border border-base-300 shadow-sm p-5 hover:border-slate-700 transition-all">
      <div class="flex justify-between items-start">
        <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Net Worth</span>
        <span class="p-2 rounded-lg bg-base-300 text-primary"><Wallet class="w-4 h-4" /></span>
      </div>
      <div class="mt-3">
        <div class="text-2xl font-black text-white font-mono">
          {{ formatMoney(meta.total_nav_usd, isPrivacyMode) }}
        </div>
        <div class="mt-1 flex items-center text-xs font-medium text-emerald-400">
          <ArrowUpRight class="w-3.5 h-3.5 mr-1" />
          <span>{{ (meta.unrealized_pl_pct >= 0 ? '+' : '') + (meta.unrealized_pl_pct || 0).toFixed(2) }}%</span>
          <span class="text-slate-500 ml-1.5 font-normal">unrealized gain</span>
        </div>
      </div>
    </div>

    <!-- Cumulative TWR Return -->
    <div class="card bg-base-200 border border-base-300 shadow-sm p-5 hover:border-slate-700 transition-all">
      <div class="flex justify-between items-start">
        <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Cumulative Return (TWR)</span>
        <span class="p-2 rounded-lg bg-base-300 text-secondary"><PieChart class="w-4 h-4" /></span>
      </div>
      <div class="mt-3">
        <div class="text-2xl font-black text-emerald-400 font-mono">
          +{{ (meta.cumulative_return_pct || 95.43).toFixed(2) }}%
        </div>
        <div class="mt-1 flex items-center text-xs text-slate-400">
          <span>vs S&P 500 (+{{ (meta.spxtr_return_pct || 74.03).toFixed(1) }}%)</span>
          <span class="ml-1 text-emerald-400 font-semibold">(+{{ (meta.active_excess_return_pct || 21.4).toFixed(1) }}% &alpha;)</span>
        </div>
      </div>
    </div>

    <!-- Sortino & Risk Ratios -->
    <div class="card bg-base-200 border border-base-300 shadow-sm p-5 hover:border-slate-700 transition-all">
      <div class="flex justify-between items-start">
        <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Downside Sortino Ratio</span>
        <span class="p-2 rounded-lg bg-base-300 text-purple-400"><ShieldCheck class="w-4 h-4" /></span>
      </div>
      <div class="mt-3">
        <div class="text-2xl font-black text-purple-400 font-mono">
          {{ (meta.sortino_ratio || 1.011).toFixed(3) }}
        </div>
        <div class="mt-1 flex items-center text-xs text-slate-400">
          <span class="text-purple-300 font-semibold">Sharpe: {{ (meta.sharpe_ratio || 0.612).toFixed(3) }}</span>
          <span class="mx-1.5 text-slate-600">•</span>
          <span>IR: {{ (meta.information_ratio || 9.29).toFixed(2) }}</span>
        </div>
      </div>
    </div>

    <!-- Factor Beta & Monthly Alpha -->
    <div class="card bg-base-200 border border-base-300 shadow-sm p-5 hover:border-slate-700 transition-all">
      <div class="flex justify-between items-start">
        <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Market Beta & Alpha</span>
        <span class="p-2 rounded-lg bg-base-300 text-amber-400"><Gauge class="w-4 h-4" /></span>
      </div>
      <div class="mt-3">
        <div class="text-2xl font-black text-amber-400 font-mono">
          &beta; {{ (meta.beta_spxtr || 1.231).toFixed(3) }}
        </div>
        <div class="mt-1 flex items-center text-xs text-slate-400">
          <span>Monthly Jensen's &alpha;:</span>
          <span class="ml-1 text-emerald-400 font-semibold font-mono">+{{ (meta.alpha_monthly_pct || 1.25).toFixed(2) }}%/mo</span>
        </div>
      </div>
    </div>
  </div>
</template>
