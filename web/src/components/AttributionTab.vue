<script setup lang="ts">
import { computed } from 'vue'
import { BarChart3, Sliders, Shield, TrendingUp, TrendingDown } from 'lucide-vue-next'

const props = defineProps<{
  summary: any
}>()

const brinson = computed(() => props.summary?.brinson || [])
const risk = computed(() => props.summary?.risk || [])
const symbols = computed(() => props.summary?.symbols || [])

const keyMetrics = ['Ending VAMI', 'Mean Return', 'Sharpe Ratio', 'Sortino Ratio', 'Calmar Ratio', 'Standard Deviation', 'Downside Deviation', 'Max Drawdown', 'Recovery']

const filteredRisk = computed(() => {
  return risk.value.filter((r: any) => r.Category === 'Absolute Risk & Return' && keyMetrics.includes(r.Metric))
})

const topContributors = computed(() => {
  return [...symbols.value]
    .sort((a: any, b: any) => parseFloat(b.Contribution_Pct || 0) - parseFloat(a.Contribution_Pct || 0))
    .slice(0, 6)
})

const topDetractors = computed(() => {
  return [...symbols.value]
    .sort((a: any, b: any) => parseFloat(a.Contribution_Pct || 0) - parseFloat(b.Contribution_Pct || 0))
    .slice(0, 6)
})
</script>

<template>
  <div class="space-y-6">
    <!-- Brinson-Fachler Multi-Period Attribution Table -->
    <div class="card bg-base-200 border border-base-300 p-6 shadow-sm">
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-3 border-b border-base-300 gap-2">
        <div>
          <h3 class="text-base font-bold text-white flex items-center gap-2">
            <BarChart3 class="w-5 h-5 text-secondary" /> Brinson-Fachler Multi-Period Attribution vs S&P 500
          </h3>
          <p class="text-xs text-slate-400">Frongello-smoothed Allocation (+27.63%) vs Selection (-1.58%)</p>
        </div>
        <div class="text-right">
          <span class="text-xs text-slate-400">Total Active Alpha: </span>
          <span class="text-base font-extrabold text-emerald-400 font-mono">+26.06%</span>
        </div>
      </div>

      <div class="overflow-x-auto mt-4">
        <table class="table table-xs w-full font-mono">
          <thead>
            <tr class="text-slate-400 border-b border-base-300 uppercase font-sans">
              <th>Sector</th>
              <th class="text-right">Allocation Effect</th>
              <th class="text-right">Selection Effect</th>
              <th class="text-right font-bold text-white">Total Attribution</th>
              <th class="text-right">Account Contrib</th>
              <th class="text-right">Benchmark Contrib</th>
              <th class="text-right font-bold text-secondary">Contrib Diff</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-base-300/60">
            <tr v-for="b in brinson" :key="b.Sector" class="hover:bg-base-300/40">
              <td class="font-bold text-white font-sans">{{ b.Sector }}</td>
              <td class="text-right font-semibold" :class="parseFloat(b.AllocationEffect_Pct) >= 0 ? 'text-emerald-400' : 'text-rose-400'">
                {{ parseFloat(b.AllocationEffect_Pct) > 0 ? '+' : '' }}{{ parseFloat(b.AllocationEffect_Pct).toFixed(2) }}%
              </td>
              <td class="text-right font-semibold" :class="parseFloat(b.SelectionEffect_Pct) >= 0 ? 'text-emerald-400' : 'text-rose-400'">
                {{ parseFloat(b.SelectionEffect_Pct) > 0 ? '+' : '' }}{{ parseFloat(b.SelectionEffect_Pct).toFixed(2) }}%
              </td>
              <td class="text-right font-bold" :class="parseFloat(b.TotalAttribution_Pct) >= 0 ? 'text-emerald-400' : 'text-rose-400'">
                {{ parseFloat(b.TotalAttribution_Pct) > 0 ? '+' : '' }}{{ parseFloat(b.TotalAttribution_Pct).toFixed(2) }}%
              </td>
              <td class="text-right text-slate-300">{{ parseFloat(b.AccountContribution_Pct).toFixed(2) }}%</td>
              <td class="text-right text-slate-400">{{ parseFloat(b.BenchmarkContribution_Pct).toFixed(2) }}%</td>
              <td class="text-right font-bold text-secondary">
                {{ parseFloat(b.ContributionDifference_Pct) > 0 ? '+' : '' }}{{ parseFloat(b.ContributionDifference_Pct).toFixed(2) }}%
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- MPT & Multi-Benchmark Risk Comparison -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- CAPM & Factor Exposure -->
      <div class="card bg-base-200 border border-base-300 p-6 shadow-sm">
        <h3 class="text-sm font-bold text-white flex items-center gap-2 mb-4 pb-2 border-b border-base-300">
          <Sliders class="w-4 h-4 text-amber-400" /> CAPM & Fama Benchmark Factor Exposures
        </h3>
        <div class="space-y-3">
          <div class="p-3 rounded-xl bg-base-300/60 border border-base-300 flex justify-between items-center">
            <div>
              <span class="text-xs font-bold text-white">Beta (&beta;) vs S&P 500</span>
              <p class="text-[11px] text-slate-400">High-momentum aggressive growth sensitivity</p>
            </div>
            <span class="text-base font-black text-amber-400 font-mono">1.231</span>
          </div>
          <div class="p-3 rounded-xl bg-base-300/60 border border-base-300 flex justify-between items-center">
            <div>
              <span class="text-xs font-bold text-white">Jensen's Alpha (&alpha;)</span>
              <p class="text-[11px] text-slate-400">Monthly risk-adjusted managerial skill</p>
            </div>
            <span class="text-base font-black text-emerald-400 font-mono">+1.25%/mo</span>
          </div>
          <div class="p-3 rounded-xl bg-base-300/60 border border-base-300 flex justify-between items-center">
            <div>
              <span class="text-xs font-bold text-white">Information Ratio (IR)</span>
              <p class="text-[11px] text-slate-400">Active return per unit tracking risk (2.30% TE)</p>
            </div>
            <span class="text-base font-black text-sky-400 font-mono">9.29</span>
          </div>
          <div class="p-3 rounded-xl bg-base-300/60 border border-base-300 flex justify-between items-center">
            <div>
              <span class="text-xs font-bold text-white">Correlation (r) vs S&P 500</span>
              <p class="text-[11px] text-slate-400">Co-movement correlation coefficient</p>
            </div>
            <span class="text-base font-black text-slate-200 font-mono">0.938</span>
          </div>
        </div>
      </div>

      <!-- Risk Comparison vs Benchmarks -->
      <div class="card bg-base-200 border border-base-300 p-6 shadow-sm">
        <h3 class="text-sm font-bold text-white flex items-center gap-2 mb-4 pb-2 border-b border-base-300">
          <Shield class="w-4 h-4 text-purple-400" /> Multi-Benchmark Risk Comparison
        </h3>
        <div class="overflow-x-auto">
          <table class="table table-xs w-full font-mono">
            <thead>
              <tr class="text-slate-400 border-b border-base-300 font-sans">
                <th>Metric</th>
                <th class="text-right font-bold text-primary">Portfolio</th>
                <th class="text-right">S&P 500</th>
                <th class="text-right">World (VT)</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-base-300/60">
              <tr v-for="r in filteredRisk" :key="r.Metric" class="hover:bg-base-300/40">
                <td class="font-semibold text-slate-200 font-sans">{{ r.Metric }}</td>
                <td class="text-right font-bold text-primary">{{ isNaN(parseFloat(r.Account)) ? r.Account : parseFloat(r.Account).toFixed(2) }}</td>
                <td class="text-right text-slate-300">{{ isNaN(parseFloat(r['SPXTR (S&P 500 TR)'])) ? r['SPXTR (S&P 500 TR)'] : parseFloat(r['SPXTR (S&P 500 TR)']).toFixed(2) }}</td>
                <td class="text-right text-slate-400">{{ isNaN(parseFloat(r['VT (World)'])) ? r['VT (World)'] : parseFloat(r['VT (World)']).toFixed(2) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Top Alpha Contributors & Detractors -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="card bg-base-200 border border-base-300 p-6 shadow-sm">
        <h4 class="text-xs font-bold text-emerald-400 flex items-center gap-1.5 mb-3">
          <TrendingUp class="w-4 h-4" /> Top Alpha Generators (Contribution %)
        </h4>
        <div class="overflow-x-auto">
          <table class="table table-xs w-full font-mono">
            <thead>
              <tr class="text-slate-400 border-b border-base-300">
                <th>Symbol</th>
                <th>Sector</th>
                <th class="text-right">Return</th>
                <th class="text-right font-bold text-emerald-400">Contribution</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-base-300/60">
              <tr v-for="s in topContributors" :key="s.Symbol">
                <td class="font-bold text-white">{{ s.Symbol }}</td>
                <td class="text-slate-400 font-sans truncate max-w-[120px]">{{ s.Sector }}</td>
                <td class="text-right text-emerald-400">+{{ parseFloat(s.Return_Pct).toFixed(1) }}%</td>
                <td class="text-right font-bold text-emerald-400">+{{ parseFloat(s.Contribution_Pct).toFixed(2) }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card bg-base-200 border border-base-300 p-6 shadow-sm">
        <h4 class="text-xs font-bold text-rose-400 flex items-center gap-1.5 mb-3">
          <TrendingDown class="w-4 h-4" /> Top Performance Detractors (Contribution %)
        </h4>
        <div class="overflow-x-auto">
          <table class="table table-xs w-full font-mono">
            <thead>
              <tr class="text-slate-400 border-b border-base-300">
                <th>Symbol</th>
                <th>Sector</th>
                <th class="text-right">Return</th>
                <th class="text-right font-bold text-rose-400">Contribution</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-base-300/60">
              <tr v-for="s in topDetractors" :key="s.Symbol">
                <td class="font-bold text-white">{{ s.Symbol }}</td>
                <td class="text-slate-400 font-sans truncate max-w-[120px]">{{ s.Sector }}</td>
                <td class="text-right" :class="parseFloat(s.Return_Pct) >= 0 ? 'text-slate-300' : 'text-rose-400'">
                  {{ parseFloat(s.Return_Pct).toFixed(1) }}%
                </td>
                <td class="text-right font-bold text-rose-400">{{ parseFloat(s.Contribution_Pct).toFixed(2) }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
