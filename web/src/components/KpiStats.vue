<script setup lang="ts">
import { computed } from "vue";
import { useCurrency } from "../composables/useCurrency";
import { usePrivacy } from "../composables/usePrivacy";
import {
  Wallet,
  PieChart,
  ShieldCheck,
  Gauge,
  ArrowUpRight,
  Coins,
  Percent,
  Layers,
} from "lucide-vue-next";

const props = defineProps<{
  summary: any;
}>();

const { formatMoney } = useCurrency();
const { isPrivacyMode, maskNumber } = usePrivacy();

const meta = computed(() => props.summary?.meta || {});
const hasAttribution = computed(
  () => meta.value.cumulative_return_pct != null || meta.value.sortino_ratio != null,
);
</script>

<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
    <!-- Card 1: Total Net Worth (Always shown) -->
    <div
      class="card bg-base-200 border border-base-300 shadow-sm p-5 hover:border-slate-700 transition-all"
    >
      <div class="flex justify-between items-start">
        <span class="text-xs font-semibold uppercase tracking-wider text-slate-400"
          >Total Net Worth</span
        >
        <span class="p-2 rounded-lg bg-base-300 text-primary"><Wallet class="w-4 h-4" /></span>
      </div>
      <div class="mt-3">
        <div class="text-2xl font-black text-white font-mono">
          {{ formatMoney(meta.total_nav_usd, isPrivacyMode) }}
        </div>
        <div
          v-if="meta.unrealized_pl_pct != null"
          class="mt-1 flex items-center text-xs font-medium"
          :class="meta.unrealized_pl_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'"
        >
          <ArrowUpRight class="w-3.5 h-3.5 mr-1" />
          <span
            >{{
              (meta.unrealized_pl_pct >= 0 ? "+" : "") + meta.unrealized_pl_pct.toFixed(2)
            }}%</span
          >
          <span class="text-slate-500 ml-1.5 font-normal">unrealized gain</span>
        </div>
      </div>
    </div>

    <!-- Card 2: Cumulative TWR (if attribution exists) OR Cost Basis (if allocation only) -->
    <div
      v-if="hasAttribution && meta.cumulative_return_pct != null"
      class="card bg-base-200 border border-base-300 shadow-sm p-5 hover:border-slate-700 transition-all"
    >
      <div class="flex justify-between items-start">
        <span class="text-xs font-semibold uppercase tracking-wider text-slate-400"
          >Cumulative Return (TWR)</span
        >
        <span class="p-2 rounded-lg bg-base-300 text-secondary"><PieChart class="w-4 h-4" /></span>
      </div>
      <div class="mt-3">
        <div class="text-2xl font-black text-emerald-400 font-mono">
          +{{ meta.cumulative_return_pct.toFixed(2) }}%
        </div>
        <div class="mt-1 flex items-center text-xs text-slate-400">
          <span v-if="meta.spxtr_return_pct != null"
            >vs S&P 500 (+{{ meta.spxtr_return_pct.toFixed(1) }}%)</span
          >
          <span
            v-if="meta.active_excess_return_pct != null"
            class="ml-1 text-emerald-400 font-semibold"
            >(+{{ meta.active_excess_return_pct.toFixed(1) }}% &alpha;)</span
          >
        </div>
      </div>
    </div>
    <div
      v-else
      class="card bg-base-200 border border-base-300 shadow-sm p-5 hover:border-slate-700 transition-all"
    >
      <div class="flex justify-between items-start">
        <span class="text-xs font-semibold uppercase tracking-wider text-slate-400"
          >Total Cost Basis</span
        >
        <span class="p-2 rounded-lg bg-base-300 text-secondary"><Coins class="w-4 h-4" /></span>
      </div>
      <div class="mt-3">
        <div class="text-2xl font-black text-white font-mono">
          {{ formatMoney(meta.cost_basis_usd, isPrivacyMode) }}
        </div>
        <div class="mt-1 text-xs text-slate-400">
          <span>Book value of invested capital</span>
        </div>
      </div>
    </div>

    <!-- Card 3: Sortino Ratio (if exists) OR Total Unrealized Gain/Loss -->
    <div
      v-if="hasAttribution && meta.sortino_ratio != null"
      class="card bg-base-200 border border-base-300 shadow-sm p-5 hover:border-slate-700 transition-all"
    >
      <div class="flex justify-between items-start">
        <span class="text-xs font-semibold uppercase tracking-wider text-slate-400"
          >Downside Sortino Ratio</span
        >
        <span class="p-2 rounded-lg bg-base-300 text-purple-400"
          ><ShieldCheck class="w-4 h-4"
        /></span>
      </div>
      <div class="mt-3">
        <div class="text-2xl font-black text-purple-400 font-mono">
          {{ meta.sortino_ratio.toFixed(3) }}
        </div>
        <div class="mt-1 flex items-center text-xs text-slate-400">
          <span v-if="meta.sharpe_ratio != null" class="text-purple-300 font-semibold"
            >Sharpe: {{ meta.sharpe_ratio.toFixed(3) }}</span
          >
          <span v-if="meta.information_ratio != null" class="mx-1.5 text-slate-600">•</span>
          <span v-if="meta.information_ratio != null"
            >IR: {{ meta.information_ratio.toFixed(2) }}</span
          >
        </div>
      </div>
    </div>
    <div
      v-else
      class="card bg-base-200 border border-base-300 shadow-sm p-5 hover:border-slate-700 transition-all"
    >
      <div class="flex justify-between items-start">
        <span class="text-xs font-semibold uppercase tracking-wider text-slate-400"
          >Unrealized P&L</span
        >
        <span class="p-2 rounded-lg bg-base-300 text-emerald-400"><Percent class="w-4 h-4" /></span>
      </div>
      <div class="mt-3">
        <div
          class="text-2xl font-black font-mono"
          :class="(meta.unrealized_pl_usd || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'"
        >
          {{
            isPrivacyMode
              ? "••••••"
              : ((meta.unrealized_pl_usd || 0) >= 0 ? "+" : "") +
                formatMoney(meta.unrealized_pl_usd)
          }}
        </div>
        <div class="mt-1 text-xs text-slate-400">
          <span>Net portfolio capital appreciation</span>
        </div>
      </div>
    </div>

    <!-- Card 4: Beta & Alpha (if exists) OR Positions & Concentration -->
    <div
      v-if="hasAttribution && meta.beta_spxtr != null"
      class="card bg-base-200 border border-base-300 shadow-sm p-5 hover:border-slate-700 transition-all"
    >
      <div class="flex justify-between items-start">
        <span class="text-xs font-semibold uppercase tracking-wider text-slate-400"
          >Market Beta & Alpha</span
        >
        <span class="p-2 rounded-lg bg-base-300 text-amber-400"><Gauge class="w-4 h-4" /></span>
      </div>
      <div class="mt-3">
        <div class="text-2xl font-black text-amber-400 font-mono">
          &beta; {{ meta.beta_spxtr.toFixed(3) }}
        </div>
        <div class="mt-1 flex items-center text-xs text-slate-400">
          <span>Monthly Jensen's &alpha;:</span>
          <span
            v-if="meta.alpha_monthly_pct != null"
            class="ml-1 text-emerald-400 font-semibold font-mono"
            >+{{ meta.alpha_monthly_pct.toFixed(2) }}%/mo</span
          >
          <span v-else class="ml-1 text-slate-400 font-mono">-</span>
        </div>
      </div>
    </div>
    <div
      v-else
      class="card bg-base-200 border border-base-300 shadow-sm p-5 hover:border-slate-700 transition-all"
    >
      <div class="flex justify-between items-start">
        <span class="text-xs font-semibold uppercase tracking-wider text-slate-400"
          >Holdings Concentration</span
        >
        <span class="p-2 rounded-lg bg-base-300 text-amber-400"><Layers class="w-4 h-4" /></span>
      </div>
      <div class="mt-3">
        <div class="text-2xl font-black text-amber-400 font-mono">
          {{ maskNumber(meta.positions_count || 0) }} Positions
        </div>
        <div class="mt-1 text-xs text-slate-400">
          <span v-if="meta.top_asset_symbol"
            >Top: <strong class="text-white">{{ meta.top_asset_symbol }}</strong> ({{
              (meta.top_asset_concentration_pct || 0).toFixed(1)
            }}%)</span
          >
          <span v-else>Active portfolio holdings</span>
        </div>
      </div>
    </div>
  </div>
</template>
