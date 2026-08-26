<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount, nextTick } from "vue";
import { Chart, registerables } from "chart.js";
import type { A2UIChartWidget } from "../../types/a2ui";
import { useCurrency } from "../../composables/useCurrency";
import { usePrivacy } from "../../composables/usePrivacy";

Chart.register(...registerables);

const props = defineProps<{
  widget: A2UIChartWidget;
}>();

const { formatMoney } = useCurrency();
const { isPrivacyMode } = usePrivacy();

const canvasRef = ref<HTMLCanvasElement | null>(null);
let chartInstance: Chart | null = null;

function renderChart() {
  if (!canvasRef.value) return;
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }

  const rawType = props.widget.chartType || "doughnut";
  const isHorizontal = rawType === "horizontal-bar";
  // Chart.js uses 'doughnut', normalize 'donut' to 'doughnut'
  const chartType = isHorizontal ? "bar" : rawType === "donut" ? "doughnut" : rawType;
  const isDonutOrPie = chartType === "doughnut" || chartType === "pie";

  const defaultColors = [
    "#22c55e",
    "#0ea5e9",
    "#f59e0b",
    "#8b5cf6",
    "#ec4899",
    "#14b8a6",
    "#f97316",
    "#64748b",
  ];

  const datasets = (props.widget.datasets || []).map((ds) => ({
    ...ds,
    backgroundColor: ds.backgroundColor || defaultColors,
    borderColor: ds.borderColor || (isDonutOrPie ? "#0f172a" : "transparent"),
    borderWidth: isDonutOrPie ? 2 : 0,
    borderRadius: ds.borderRadius ?? (isDonutOrPie ? 0 : 6),
  }));

  const configOptions: any = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: isHorizontal ? "y" : "x",
    plugins: {
      legend: {
        display: isDonutOrPie,
        position: "right",
        labels: {
          color: "#94a3b8",
          font: { family: "Inter, system-ui, sans-serif", size: 11 },
          boxWidth: 12,
          boxHeight: 12,
          padding: 10,
        },
      },
      tooltip: {
        backgroundColor: "#0f172a",
        titleColor: "#f8fafc",
        bodyColor: "#94a3b8",
        borderColor: "#334155",
        borderWidth: 1,
        padding: 10,
        boxPadding: 4,
        usePointStyle: true,
        callbacks: {
          label: (context: any) => {
            const label = context.label || context.dataset.label || "";
            const val =
              context.parsed?.y !== undefined && !isHorizontal
                ? context.parsed.y
                : context.parsed?.x !== undefined && isHorizontal
                  ? context.parsed.x
                  : context.raw;
            if (typeof val === "number") {
              return ` ${label}: ${formatMoney(val, isPrivacyMode.value)}`;
            }
            return ` ${label}: ${val}`;
          },
        },
      },
    },
  };

  if (!isDonutOrPie) {
    configOptions.scales = {
      x: {
        grid: { color: "rgba(51, 65, 85, 0.4)" },
        ticks: { color: "#94a3b8", font: { size: 10 } },
      },
      y: {
        grid: { color: "rgba(51, 65, 85, 0.4)" },
        ticks: { color: "#94a3b8", font: { size: 10 } },
      },
    };
  } else {
    configOptions.cutout = "65%";
  }

  try {
    chartInstance = new Chart(canvasRef.value, {
      type: chartType as any,
      data: {
        labels: props.widget.labels || [],
        datasets,
      },
      options: {
        ...configOptions,
        ...props.widget.options,
      },
    });
  } catch (err) {
    console.error("Failed to create Chart.js instance:", err);
  }
}

onMounted(() => {
  nextTick(() => {
    renderChart();
  });
});

watch(
  () => [props.widget, isPrivacyMode.value],
  () => {
    nextTick(() => {
      renderChart();
    });
  },
  { deep: true },
);

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }
});
</script>

<template>
  <div class="card bg-base-200 border border-base-300 p-6 shadow-sm flex flex-col min-h-[340px]">
    <div v-if="widget.title" class="pb-3 mb-4 border-b border-base-300">
      <h3 class="text-base font-bold text-white">{{ widget.title }}</h3>
      <p v-if="widget.description" class="text-xs text-slate-400 mt-0.5">
        {{ widget.description }}
      </p>
    </div>

    <div class="relative w-full flex-1 min-h-[240px]">
      <canvas ref="canvasRef"></canvas>
    </div>
  </div>
</template>
