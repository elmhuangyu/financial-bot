<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount } from "vue";
import { Chart, registerables } from "chart.js";
import type { A2UIChartWidget } from "../../types/a2ui";

Chart.register(...registerables);

const props = defineProps<{
  widget: A2UIChartWidget;
}>();

const canvasRef = ref<HTMLCanvasElement | null>(null);
let chartInstance: Chart | null = null;

function renderChart() {
  if (!canvasRef.value) return;
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }

  const isHorizontal = props.widget.chartType === "horizontal-bar";
  const chartType = isHorizontal ? "bar" : props.widget.chartType || "donut";

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

  const datasets = props.widget.datasets.map((ds, idx) => ({
    ...ds,
    backgroundColor: ds.backgroundColor || defaultColors,
    borderColor: ds.borderColor || (chartType === "donut" ? "#0f172a" : "transparent"),
    borderWidth: chartType === "donut" ? 2 : 0,
    borderRadius: ds.borderRadius ?? (chartType === "donut" ? 0 : 6),
  }));

  chartInstance = new Chart(canvasRef.value, {
    type: chartType as any,
    data: {
      labels: props.widget.labels || [],
      datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: isHorizontal ? "y" : "x",
      plugins: {
        legend: {
          display: chartType === "donut",
          position: "right",
          labels: {
            color: "#94a3b8",
            font: { family: "Inter, system-ui, sans-serif", size: 11 },
            boxWidth: 12,
            boxHeight: 12,
            padding: 12,
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
        },
      },
      scales:
        chartType === "donut"
          ? {}
          : {
              x: {
                grid: { color: "rgba(51, 65, 85, 0.4)" },
                ticks: { color: "#94a3b8", font: { size: 10 } },
              },
              y: {
                grid: { color: "rgba(51, 65, 85, 0.4)" },
                ticks: { color: "#94a3b8", font: { size: 10 } },
              },
            },
      ...props.widget.options,
    },
  });
}

onMounted(() => {
  renderChart();
});

watch(
  () => props.widget,
  () => {
    renderChart();
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
  <div class="card bg-base-200 border border-base-300 p-6 shadow-sm flex flex-col">
    <div v-if="widget.title" class="pb-3 mb-4 border-b border-base-300">
      <h3 class="text-base font-bold text-white">{{ widget.title }}</h3>
      <p v-if="widget.description" class="text-xs text-slate-400 mt-0.5">
        {{ widget.description }}
      </p>
    </div>

    <div class="relative w-full h-64 sm:h-72 flex-1">
      <canvas ref="canvasRef"></canvas>
    </div>
  </div>
</template>
