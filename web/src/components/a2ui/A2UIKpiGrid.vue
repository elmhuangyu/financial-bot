<script setup lang="ts">
import { computed } from "vue";
import type { A2UIKpi } from "../../types/a2ui";
import { useCurrency } from "../../composables/useCurrency";
import { usePrivacy } from "../../composables/usePrivacy";
import {
  Wallet,
  PieChart,
  ShieldCheck,
  Gauge,
  ArrowUpRight,
  Coins,
  Percent,
  Layers,
  Activity,
  TrendingUp,
  TrendingDown,
  DollarSign,
} from "lucide-vue-next";

const props = defineProps<{
  kpis: A2UIKpi[];
}>();

const { formatMoney } = useCurrency();
const { isPrivacyMode, maskNumber } = usePrivacy();

const iconMap: Record<string, any> = {
  wallet: Wallet,
  "pie-chart": PieChart,
  "shield-check": ShieldCheck,
  gauge: Gauge,
  coins: Coins,
  percent: Percent,
  layers: Layers,
  activity: Activity,
  "trending-up": TrendingUp,
  "trending-down": TrendingDown,
  dollar: DollarSign,
};

function getIcon(name?: string) {
  if (!name) return DollarSign;
  return iconMap[name.toLowerCase()] || DollarSign;
}

function formatValue(kpi: A2UIKpi): string {
  if (kpi.format === "currency") {
    return formatMoney(kpi.value, isPrivacyMode.value);
  }
  if (kpi.format === "percent") {
    const num = typeof kpi.value === "number" ? kpi.value : parseFloat(String(kpi.value));
    return isNaN(num) ? String(kpi.value) : `${num > 0 ? "+" : ""}${num.toFixed(2)}%`;
  }
  if (kpi.format === "number") {
    const num = typeof kpi.value === "number" ? kpi.value : parseFloat(String(kpi.value));
    return isNaN(num) ? String(kpi.value) : maskNumber(num.toLocaleString());
  }
  return String(kpi.value);
}

const colorClassMap: Record<string, string> = {
  primary: "text-primary",
  secondary: "text-secondary",
  accent: "text-accent",
  emerald: "text-emerald-400",
  amber: "text-amber-400",
  purple: "text-purple-400",
  sky: "text-sky-400",
  rose: "text-rose-400",
};
</script>

<template>
  <div v-if="kpis && kpis.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
    <div
      v-for="kpi in kpis"
      :key="kpi.id || kpi.label"
      class="card bg-base-200 border border-base-300 shadow-sm p-5 hover:border-base-content/20 transition-all"
    >
      <div class="flex justify-between items-start">
        <span class="text-xs font-semibold uppercase tracking-wider text-base-content/60">{{
          kpi.label
        }}</span>
        <span class="p-2 rounded-lg bg-base-300" :class="colorClassMap[kpi.color || 'primary']">
          <component :is="getIcon(kpi.icon)" class="w-4 h-4" />
        </span>
      </div>

      <div class="mt-3">
        <div
          class="text-2xl font-black font-mono tracking-tight"
          :class="colorClassMap[kpi.color || ''] || 'text-base-content'"
        >
          {{ formatValue(kpi) }}
        </div>

        <!-- Optional Change / Badge -->
        <div
          v-if="kpi.change"
          class="mt-1 flex items-center text-xs font-medium"
          :class="kpi.changeType === 'negative' ? 'text-rose-500' : 'text-emerald-500'"
        >
          <component
            :is="kpi.changeType === 'negative' ? TrendingDown : ArrowUpRight"
            class="w-3.5 h-3.5 mr-1 shrink-0"
          />
          <span>{{ kpi.change }}</span>
          <span v-if="kpi.subtext" class="text-base-content/50 ml-1.5 font-normal truncate">{{
            kpi.subtext
          }}</span>
        </div>

        <!-- Optional Subtext without change -->
        <div v-else-if="kpi.subtext" class="mt-1 text-xs text-base-content/60 truncate">
          {{ kpi.subtext }}
        </div>
      </div>
    </div>
  </div>
</template>
