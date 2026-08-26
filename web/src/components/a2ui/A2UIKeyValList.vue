<script setup lang="ts">
import type { A2UIKeyValListWidget } from "../../types/a2ui";
import { useCurrency } from "../../composables/useCurrency";
import { usePrivacy } from "../../composables/usePrivacy";

const props = defineProps<{
  widget: A2UIKeyValListWidget;
}>();

const { formatMoney } = useCurrency();
const { isPrivacyMode, maskNumber } = usePrivacy();

function formatVal(item: any): string {
  if (item.format === "currency") {
    return formatMoney(item.value, isPrivacyMode.value);
  }
  if (item.format === "percent") {
    const num = typeof item.value === "number" ? item.value : parseFloat(String(item.value));
    return isNaN(num) ? String(item.value) : `${num > 0 ? "+" : ""}${num.toFixed(2)}%`;
  }
  if (item.format === "number") {
    const num = typeof item.value === "number" ? item.value : parseFloat(String(item.value));
    return isNaN(num) ? String(item.value) : maskNumber(num.toLocaleString());
  }
  return String(item.value);
}

const colorClassMap: Record<string, string> = {
  primary: "bg-primary",
  secondary: "bg-secondary",
  emerald: "bg-emerald-500",
  amber: "bg-amber-500",
  purple: "bg-purple-500",
  sky: "bg-sky-500",
  rose: "bg-rose-500",
};
</script>

<template>
  <div class="card bg-base-200 border border-base-300 p-6 shadow-sm space-y-4">
    <div v-if="widget.title" class="pb-2 border-b border-base-300">
      <h3 class="text-base font-bold text-white">{{ widget.title }}</h3>
      <p v-if="widget.description" class="text-xs text-slate-400 mt-0.5">
        {{ widget.description }}
      </p>
    </div>

    <div class="space-y-3.5">
      <div v-for="item in widget.items" :key="item.label" class="space-y-1">
        <div class="flex justify-between text-xs">
          <span class="text-slate-300 font-medium">{{ item.label }}</span>
          <span class="font-mono text-slate-100 font-bold">
            {{ formatVal(item) }}
            <span v-if="item.subtext" class="text-slate-400 font-normal ml-1 font-sans"
              >({{ item.subtext }})</span
            >
          </span>
        </div>

        <div
          v-if="item.progressPct != null"
          class="w-full bg-base-300 h-2 rounded-full overflow-hidden"
        >
          <div
            class="h-full rounded-full transition-all duration-500"
            :class="colorClassMap[item.color || 'primary'] || 'bg-primary'"
            :style="{ width: `${Math.min(100, Math.max(0, item.progressPct))}%` }"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>
