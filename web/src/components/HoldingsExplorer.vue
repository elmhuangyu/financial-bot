<script setup lang="ts">
import { ref, computed } from 'vue'
import { useCurrency } from '../composables/useCurrency'
import { usePrivacy } from '../composables/usePrivacy'
import { Search, Combine, RotateCcw } from 'lucide-vue-next'

const props = defineProps<{
  summary: any
}>()

const { formatMoney } = useCurrency()
const { isPrivacyMode, maskNumber } = usePrivacy()

const rawHoldings = computed<any[]>(() => props.summary?.holdings || [])

const searchQuery = ref('')
const selectedOwner = ref('')
const selectedTax = ref('')
const selectedClass = ref('')
const isAggregateMode = ref(false)
const sortKey = ref('market_value_usd')
const sortAsc = ref(false)

// Dynamic Filter Options
const ownerOptions = computed(() => {
  const s = new Set<string>()
  rawHoldings.value.forEach(h => { if (h.owner) s.add(h.owner) })
  return Array.from(s)
})

const taxOptions = computed(() => {
  const s = new Set<string>()
  rawHoldings.value.forEach(h => { if (h.tax_treatment) s.add(h.tax_treatment) })
  return Array.from(s)
})

const classOptions = computed(() => {
  const s = new Set<string>()
  rawHoldings.value.forEach(h => { if (h.asset_class) s.add(h.asset_class) })
  return Array.from(s)
})

function resetFilters() {
  searchQuery.value = ''
  selectedOwner.value = ''
  selectedTax.value = ''
  selectedClass.value = ''
}

function toggleSort(key: string) {
  if (sortKey.value === key) {
    sortAsc.value = !sortAsc.value
  } else {
    sortKey.value = key
    sortAsc.value = true
  }
}

// Filtered & Aggregated Holdings
const processedHoldings = computed(() => {
  // 1. Filter raw list
  const filtered = rawHoldings.value.filter(h => {
    if (selectedOwner.value && h.owner !== selectedOwner.value) return false
    if (selectedTax.value && h.tax_treatment !== selectedTax.value) return false
    if (selectedClass.value && h.asset_class !== selectedClass.value) return false
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      const text = `${h.symbol} ${h.asset_name} ${h.sector} ${h.account_label} ${h.industry}`.toLowerCase()
      if (!text.includes(q)) return false
    }
    return true
  })

  // 2. Aggregate if enabled
  let list = filtered
  if (isAggregateMode.value) {
    const groupMap: Record<string, any> = {}
    filtered.forEach(h => {
      const sym = h.symbol || 'OTHER'
      if (!groupMap[sym]) {
        groupMap[sym] = {
          symbol: h.symbol,
          asset_name: h.asset_name,
          asset_class: h.asset_class,
          sector: h.sector,
          industry: h.industry,
          accounts: new Set([h.account_label]),
          tax_treatments: new Set([h.tax_treatment]),
          owners: new Set([h.owner]),
          quantity: 0,
          market_value_usd: 0,
          cost_basis_usd: 0,
          unrealized_pl_usd: 0,
        }
      } else {
        groupMap[sym].accounts.add(h.account_label)
        groupMap[sym].tax_treatments.add(h.tax_treatment)
        groupMap[sym].owners.add(h.owner)
      }
      groupMap[sym].quantity += parseFloat(h.quantity || 0)
      groupMap[sym].market_value_usd += parseFloat(h.market_value_usd || 0)
      groupMap[sym].cost_basis_usd += parseFloat(h.cost_basis_usd || 0)
      groupMap[sym].unrealized_pl_usd += parseFloat(h.unrealized_pl_usd || 0)
    })

    list = Object.values(groupMap).map(g => ({
      symbol: g.symbol,
      asset_name: g.asset_name,
      asset_class: g.asset_class,
      sector: g.sector,
      industry: g.industry,
      account_label: Array.from(g.accounts).join(', '),
      account_count: g.accounts.size,
      tax_treatment: Array.from(g.tax_treatments).join(', '),
      tax_treatments_list: Array.from(g.tax_treatments),
      owner: Array.from(g.owners).join(', '),
      quantity: g.quantity,
      market_value_usd: g.market_value_usd,
      cost_basis_usd: g.cost_basis_usd,
      unrealized_pl_usd: g.unrealized_pl_usd,
      is_aggregated: true,
    }))
  }

  // 3. Sort
  return [...list].sort((a: any, b: any) => {
    let valA = a[sortKey.value]
    let valB = b[sortKey.value]
    if (['market_value_usd', 'unrealized_pl_usd', 'quantity', 'cost_basis_usd'].includes(sortKey.value)) {
      valA = parseFloat(valA || 0)
      valB = parseFloat(valB || 0)
    } else {
      valA = String(valA || '').toLowerCase()
      valB = String(valB || '').toLowerCase()
    }
    if (valA < valB) return sortAsc.value ? -1 : 1
    if (valA > valB) return sortAsc.value ? 1 : -1
    return 0
  })
})

const totals = computed(() => {
  let val = 0
  let pl = 0
  processedHoldings.value.forEach(h => {
    val += parseFloat(h.market_value_usd || 0)
    pl += parseFloat(h.unrealized_pl_usd || 0)
  })
  return { val, pl }
})
</script>

<template>
  <div class="space-y-4">
    <!-- Filter & Control Bar -->
    <div class="card bg-base-200 border border-base-300 p-4 shadow-sm">
      <div class="flex flex-col md:flex-row items-center justify-between gap-3">
        <!-- Search Input -->
        <div class="relative w-full md:w-80">
          <Search class="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
          <input 
            v-model="searchQuery"
            type="text" 
            placeholder="Search symbol, company, industry..."
            class="input input-sm input-bordered w-full pl-10 rounded-xl bg-base-300 border-base-300 text-xs placeholder-slate-500"
          />
        </div>

        <!-- Filter Dropdowns & Aggregate Toggle -->
        <div class="flex flex-wrap items-center gap-2 w-full md:w-auto">
          <!-- Aggregate Toggle Button -->
          <button 
            @click="isAggregateMode = !isAggregateMode"
            class="btn btn-sm gap-1.5 text-xs font-semibold rounded-lg transition-all"
            :class="isAggregateMode ? 'btn-primary text-white shadow-md' : 'btn-outline border-base-300 text-slate-300'"
            title="Consolidate positions with identical symbols across all accounts"
          >
            <Combine class="w-4 h-4" />
            <span>{{ isAggregateMode ? 'Aggregated (By Symbol)' : 'Aggregate Assets' }}</span>
          </button>

          <select v-model="selectedOwner" class="select select-sm select-bordered bg-base-300 text-xs rounded-lg">
            <option value="">All Owners</option>
            <option v-for="o in ownerOptions" :key="o" :value="o">{{ o }}</option>
          </select>

          <select v-model="selectedTax" class="select select-sm select-bordered bg-base-300 text-xs rounded-lg">
            <option value="">All Tax Types</option>
            <option v-for="t in taxOptions" :key="t" :value="t">{{ t }}</option>
          </select>

          <select v-model="selectedClass" class="select select-sm select-bordered bg-base-300 text-xs rounded-lg">
            <option value="">All Classes</option>
            <option v-for="c in classOptions" :key="c" :value="c">{{ c }}</option>
          </select>

          <button @click="resetFilters" class="btn btn-sm btn-ghost text-slate-400 hover:text-white" title="Reset Filters">
            <RotateCcw class="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>

    <!-- Holdings Data Grid -->
    <div class="card bg-base-200 border border-base-300 rounded-2xl overflow-hidden shadow-sm">
      <div class="overflow-x-auto">
        <table class="table table-xs w-full font-mono">
          <thead class="text-slate-400 bg-base-300/80 uppercase select-none font-sans">
            <tr>
              <th @click="toggleSort('symbol')" class="cursor-pointer hover:text-white">Symbol</th>
              <th @click="toggleSort('asset_name')" class="cursor-pointer hover:text-white">Asset Name</th>
              <th @click="toggleSort('account_label')" class="cursor-pointer hover:text-white">Account(s)</th>
              <th @click="toggleSort('tax_treatment')" class="cursor-pointer hover:text-white">Tax Status</th>
              <th @click="toggleSort('sector')" class="cursor-pointer hover:text-white">Sector</th>
              <th @click="toggleSort('quantity')" class="text-right cursor-pointer hover:text-white">Quantity</th>
              <th @click="toggleSort('market_value_usd')" class="text-right cursor-pointer hover:text-white font-bold text-white">Market Value</th>
              <th @click="toggleSort('unrealized_pl_usd')" class="text-right cursor-pointer hover:text-white">Unrealized P&L</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-base-300/60">
            <tr v-for="h in processedHoldings" :key="h.symbol + (h.account_label || '')" class="hover:bg-base-300/40 transition-all">
              <td class="font-bold text-white">{{ h.symbol }}</td>
              <td class="text-slate-300 truncate max-w-xs font-sans">{{ h.asset_name }}</td>
              <td>
                <div v-if="h.is_aggregated && h.account_count > 1" class="flex items-center gap-1">
                  <span class="badge badge-xs badge-info font-bold">{{ h.account_count }} Accounts</span>
                  <span class="truncate max-w-[120px] text-[11px] text-slate-400" :title="h.account_label">{{ h.account_label }}</span>
                </div>
                <span v-else class="text-slate-400 font-sans">{{ h.account_label }}</span>
              </td>
              <td>
                <div v-if="h.is_aggregated && h.tax_treatments_list" class="flex flex-wrap gap-1">
                  <span 
                    v-for="t in h.tax_treatments_list" 
                    :key="t"
                    class="badge badge-xs font-semibold"
                    :class="t === 'Tax-Free' ? 'badge-success badge-outline' : t === 'Tax-Deferred' ? 'badge-warning badge-outline' : 'badge-info badge-outline'"
                  >
                    {{ t }}
                  </span>
                </div>
                <span 
                  v-else 
                  class="badge badge-xs font-semibold"
                  :class="h.tax_treatment === 'Tax-Free' ? 'badge-success badge-outline' : h.tax_treatment === 'Tax-Deferred' ? 'badge-warning badge-outline' : 'badge-info badge-outline'"
                >
                  {{ h.tax_treatment }}
                </span>
              </td>
              <td class="text-slate-400 font-sans truncate max-w-[130px]">{{ h.sector }}</td>
              <td class="text-right text-slate-300">{{ maskNumber(parseFloat(h.quantity || 0).toLocaleString()) }}</td>
              <td class="text-right font-bold text-white">{{ formatMoney(h.market_value_usd, isPrivacyMode) }}</td>
              <td class="text-right font-semibold" :class="parseFloat(h.unrealized_pl_usd || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'">
                {{ isPrivacyMode ? '••••••' : ((parseFloat(h.unrealized_pl_usd || 0) >= 0 ? '+' : '') + formatMoney(h.unrealized_pl_usd)) }}
              </td>
            </tr>
          </tbody>
          <!-- Footer Totals -->
          <tfoot class="bg-base-300 font-sans border-t border-base-300 font-bold text-white">
            <tr>
              <td colspan="5" class="py-3 px-4 text-xs text-slate-400">
                Showing {{ processedHoldings.length }} {{ isAggregateMode ? 'consolidated assets' : 'positions' }}
              </td>
              <td class="py-3 px-4 text-right text-slate-400 text-xs">Total:</td>
              <td class="py-3 px-4 text-right text-primary font-mono text-sm">
                {{ formatMoney(totals.val, isPrivacyMode) }}
              </td>
              <td 
                class="py-3 px-4 text-right font-mono text-sm"
                :class="totals.pl >= 0 ? 'text-emerald-400' : 'text-rose-400'"
              >
                {{ isPrivacyMode ? '••••••' : ((totals.pl >= 0 ? '+' : '') + formatMoney(totals.pl)) }}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  </div>
</template>
