<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import type { A2UIDataTableWidget } from "../../types/a2ui";
import { useCurrency } from "../../composables/useCurrency";
import { usePrivacy } from "../../composables/usePrivacy";
import { Search, Combine, RotateCcw, Download, Table2 } from "lucide-vue-next";

const props = defineProps<{
  widget: A2UIDataTableWidget;
  runId: string;
}>();

const { formatMoney } = useCurrency();
const { isPrivacyMode, maskNumber } = usePrivacy();

const rawRows = ref<any[]>([]);
const headers = ref<string[]>([]);
const isLoading = ref<boolean>(false);

const searchQuery = ref<string>("");
const activeFilters = ref<Record<string, string>>({});
const isAggregateMode = ref<boolean>(false);
const sortKey = ref<string>("");
const sortAsc = ref<boolean>(false);

async function loadData() {
  if (props.widget.rows && props.widget.rows.length > 0) {
    rawRows.value = props.widget.rows;
    headers.value = props.widget.headers || Object.keys(props.widget.rows[0] || {});
    return;
  }

  if (props.widget.sourceCsv) {
    isLoading.value = true;
    try {
      const res = await fetch(
        `/api/runs/${props.runId}/file?name=${encodeURIComponent(props.widget.sourceCsv)}`,
      );
      if (res.ok) {
        const data = await res.json();
        headers.value = data.headers || [];
        rawRows.value = data.rows || [];
      }
    } catch (e) {
      console.error(e);
    } finally {
      isLoading.value = false;
    }
  }
}

onMounted(() => {
  loadData();
});

watch(
  () => [props.widget, props.runId],
  () => {
    loadData();
  },
  { deep: true },
);

// Filter Options extraction for declared filters
const filterOptionsMap = computed(() => {
  const map: Record<string, string[]> = {};
  const declaredFilters = props.widget.features?.filters || [];
  for (const f of declaredFilters) {
    if (f.options && f.options.length > 0) {
      map[f.key] = f.options;
    } else {
      const s = new Set<string>();
      rawRows.value.forEach((r) => {
        if (r[f.key]) s.add(String(r[f.key]));
      });
      map[f.key] = Array.from(s);
    }
  }
  return map;
});

function resetFilters() {
  searchQuery.value = "";
  activeFilters.value = {};
}

function toggleSort(key: string) {
  if (sortKey.value === key) {
    sortAsc.value = !sortAsc.value;
  } else {
    sortKey.value = key;
    sortAsc.value = true;
  }
}

// Columns definition
const columns = computed(() => {
  if (props.widget.columns && props.widget.columns.length > 0) {
    return props.widget.columns;
  }
  return headers.value.map((h) => ({
    key: h,
    label: h.replace(/_/g, " ").toUpperCase(),
    align: "left" as const,
    format: "text" as const,
    sortable: true,
  }));
});

// Processed Rows (Filtered + Aggregated + Sorted)
const processedRows = computed(() => {
  // 1. Filter
  const filtered = rawRows.value.filter((row) => {
    for (const [k, val] of Object.entries(activeFilters.value)) {
      if (val && String(row[k]) !== val) return false;
    }
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase();
      const match = Object.values(row).some((v) =>
        String(v || "")
          .toLowerCase()
          .includes(q),
      );
      if (!match) return false;
    }
    return true;
  });

  // 2. Aggregate if requested
  const aggKey = props.widget.features?.aggregateBy;
  let list = filtered;
  if (isAggregateMode.value && aggKey) {
    const groupMap: Record<string, any> = {};
    filtered.forEach((row) => {
      const primary = String(row[aggKey] || "OTHER");
      if (!groupMap[primary]) {
        groupMap[primary] = {
          ...row,
          _raw_accounts: new Set([row.account_label || row.account || "Default"]),
          _raw_tax: new Set([row.tax_treatment || "Taxable"]),
          _raw_owners: new Set([row.owner || "Primary"]),
          _is_aggregated: true,
        };
      } else {
        groupMap[primary]._raw_accounts.add(row.account_label || row.account || "Default");
        groupMap[primary]._raw_tax.add(row.tax_treatment || "Taxable");
        groupMap[primary]._raw_owners.add(row.owner || "Primary");

        // Sum numeric fields
        for (const col of columns.value) {
          if (["currency", "number", "percent"].includes(col.format || "") && col.key !== aggKey) {
            const numA = parseFloat(String(groupMap[primary][col.key] || 0).replace(/,/g, ""));
            const numB = parseFloat(String(row[col.key] || 0).replace(/,/g, ""));
            if (!isNaN(numA) && !isNaN(numB)) {
              groupMap[primary][col.key] = numA + numB;
            }
          }
        }
      }
    });

    list = Object.values(groupMap).map((g) => ({
      ...g,
      account_label: Array.from(g._raw_accounts).join(", "),
      account_count: g._raw_accounts.size,
      tax_treatment: Array.from(g._raw_tax).join(", "),
      tax_treatments_list: Array.from(g._raw_tax),
      owner: Array.from(g._raw_owners).join(", "),
    }));
  }

  // 3. Sort
  if (!sortKey.value) return list;
  return [...list].sort((a, b) => {
    let valA = a[sortKey.value];
    let valB = b[sortKey.value];
    const numA = parseFloat(String(valA || "").replace(/,/g, ""));
    const numB = parseFloat(String(valB || "").replace(/,/g, ""));
    if (!isNaN(numA) && !isNaN(numB)) {
      valA = numA;
      valB = numB;
    } else {
      valA = String(valA || "").toLowerCase();
      valB = String(valB || "").toLowerCase();
    }
    if (valA < valB) return sortAsc.value ? -1 : 1;
    if (valA > valB) return sortAsc.value ? 1 : -1;
    return 0;
  });
});

function formatCell(row: any, col: any): string {
  const val = row[col.key];
  if (col.format === "currency") {
    return formatMoney(val, isPrivacyMode.value);
  }
  if (col.format === "number") {
    const num = parseFloat(String(val || 0).replace(/,/g, ""));
    return isNaN(num) ? String(val || "") : maskNumber(num.toLocaleString());
  }
  if (col.format === "percent") {
    const num = parseFloat(String(val || 0).replace(/,/g, ""));
    return isNaN(num) ? String(val || "") : `${num > 0 ? "+" : ""}${num.toFixed(2)}%`;
  }
  return String(val || "");
}

function exportCsv() {
  if (!processedRows.value.length) return;
  const cols = columns.value;
  const csvContent = [
    cols.map((c) => `"${c.label}"`).join(","),
    ...processedRows.value.map((r) =>
      cols.map((c) => `"${(r[c.key] || "").toString().replace(/"/g, '""')}"`).join(","),
    ),
  ].join("\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${props.widget.title || "export"}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
</script>

<template>
  <div class="card bg-base-200 border border-base-300 shadow-sm p-5 space-y-4">
    <!-- Header & Controls -->
    <div
      class="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 pb-3 border-b border-base-300"
    >
      <div>
        <h3 v-if="widget.title" class="text-base font-bold text-white flex items-center gap-2">
          <Table2 class="w-5 h-5 text-primary" /> {{ widget.title }}
        </h3>
        <p v-if="widget.description" class="text-xs text-slate-400 mt-0.5">
          {{ widget.description }}
        </p>
      </div>

      <!-- Controls -->
      <div class="flex flex-wrap items-center gap-2 w-full md:w-auto">
        <!-- Cross-Account Aggregate Assets Button -->
        <button
          v-if="widget.features?.aggregateBy"
          @click="isAggregateMode = !isAggregateMode"
          class="btn btn-sm gap-1.5 text-xs font-semibold rounded-lg transition-all"
          :class="
            isAggregateMode
              ? 'btn-primary text-white shadow-md'
              : 'btn-outline border-base-300 text-slate-300'
          "
          title="Consolidate positions with identical symbols across all accounts"
        >
          <Combine class="w-4 h-4" />
          <span>{{ isAggregateMode ? "Aggregated" : "Aggregate Assets" }}</span>
        </button>

        <!-- Search Input -->
        <div v-if="widget.features?.search !== false" class="relative w-full sm:w-48">
          <Search class="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search..."
            class="input input-sm input-bordered w-full pl-9 rounded-lg bg-base-300 border-base-300 text-xs placeholder-slate-500"
          />
        </div>

        <!-- Filter Dropdowns -->
        <template v-if="widget.features?.filters">
          <select
            v-for="f in widget.features.filters"
            :key="f.key"
            v-model="activeFilters[f.key]"
            class="select select-sm select-bordered bg-base-300 text-xs rounded-lg"
          >
            <option value="">All {{ f.label }}</option>
            <option v-for="opt in filterOptionsMap[f.key] || []" :key="opt" :value="opt">
              {{ opt }}
            </option>
          </select>
        </template>

        <!-- Reset Button -->
        <button
          @click="resetFilters"
          class="btn btn-sm btn-ghost text-slate-400 hover:text-white"
          title="Reset Filters"
        >
          <RotateCcw class="w-3.5 h-3.5" />
        </button>

        <!-- Export CSV Button -->
        <button
          v-if="widget.features?.exportCsv !== false"
          @click="exportCsv"
          class="btn btn-sm btn-outline border-base-300 text-slate-300 hover:text-white gap-1 text-xs"
        >
          <Download class="w-3.5 h-3.5 text-primary" />
          <span>Export</span>
        </button>
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto rounded-xl border border-base-300">
      <div v-if="isLoading" class="flex justify-center items-center py-16">
        <span class="loading loading-spinner text-primary loading-md"></span>
      </div>
      <table v-else class="table table-xs w-full font-mono">
        <thead class="text-slate-400 bg-base-300/80 uppercase select-none font-sans">
          <tr>
            <th
              v-for="col in columns"
              :key="col.key"
              @click="col.sortable !== false ? toggleSort(col.key) : null"
              class="hover:text-white"
              :class="[
                col.align === 'right'
                  ? 'text-right'
                  : col.align === 'center'
                    ? 'text-center'
                    : 'text-left',
                col.sortable !== false ? 'cursor-pointer' : '',
              ]"
            >
              {{ col.label }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-base-300/60 text-slate-200">
          <tr
            v-for="(row, idx) in processedRows"
            :key="idx"
            class="hover:bg-base-300/40 transition-all"
          >
            <td
              v-for="col in columns"
              :key="col.key"
              :class="
                col.align === 'right'
                  ? 'text-right'
                  : col.align === 'center'
                    ? 'text-center'
                    : 'text-left'
              "
            >
              <!-- Multi-account badge for aggregated positions -->
              <div
                v-if="col.key === 'account_label' && row._is_aggregated && row.account_count > 1"
                class="flex items-center gap-1 font-sans"
              >
                <span class="badge badge-xs badge-info font-bold"
                  >{{ row.account_count }} Accounts</span
                >
                <span
                  class="truncate max-w-[120px] text-[11px] text-slate-400"
                  :title="row.account_label"
                  >{{ row.account_label }}</span
                >
              </div>
              <!-- Badge format -->
              <span
                v-else-if="col.format === 'badge'"
                class="badge badge-xs font-semibold"
                :class="col.badgeColorMap?.[row[col.key]] || 'badge-neutral badge-outline'"
              >
                {{ row[col.key] }}
              </span>
              <!-- Standard cell -->
              <span v-else :class="col.key === 'symbol' ? 'font-bold text-white' : ''">
                {{ formatCell(row, col) }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Table Footer / Count -->
    <div class="flex justify-between items-center text-xs text-slate-400 font-sans pt-1">
      <span
        >Showing {{ processedRows.length }}
        {{ isAggregateMode ? "consolidated items" : "rows" }}</span
      >
    </div>
  </div>
</template>
