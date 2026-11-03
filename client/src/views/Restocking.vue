<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budget') }}</h3>
          <span class="budget-value">{{ money(budget) }}</span>
        </div>
        <input
          v-model.number="budget"
          class="budget-slider"
          type="range"
          min="0"
          :max="maxBudget"
          step="50"
          :aria-label="t('restocking.budget')"
        />
        <div class="slider-scale">
          <span>{{ money(0) }}</span>
          <span>{{ money(maxBudget) }}</span>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.itemsRecommended') }}</div>
          <div class="stat-value">{{ recommendations.length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.budgetUsed') }}</div>
          <div class="stat-value">{{ money(totalCost) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.budgetRemaining') }}</div>
          <div class="stat-value">{{ money(budget - totalCost) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.leadTime') }}</div>
          <div class="stat-value">{{ t('restocking.days', { count: maxLeadTime }) }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
          <button
            class="place-order"
            :disabled="recommendations.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="lastOrder" class="confirmation">
          {{ t('restocking.confirmation', { number: lastOrder.order_number }) }}
          <router-link to="/orders">{{ t('restocking.viewInOrders') }}</router-link>
        </div>
        <div v-if="submitError" class="error">{{ submitError }}</div>

        <p v-if="recommendations.length === 0" class="empty">{{ t('restocking.empty') }}</p>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.item') }}</th>
                <th>{{ t('restocking.table.demandGap') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.lineTotal') }}</th>
                <th class="num">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in recommendations" :key="rec.item_sku">
                <td><strong>{{ rec.item_sku }}</strong></td>
                <td>{{ translateProductName(rec.item_name) }}</td>
                <td>
                  +{{ rec.gap }}
                  <span v-if="rec.quantity < rec.gap" class="badge warning">{{ t('restocking.partial') }}</span>
                </td>
                <td class="num">{{ rec.quantity }}</td>
                <td class="num">{{ money(rec.unit_cost, 2) }}</td>
                <td class="num"><strong>{{ money(rec.line_total, 2) }}</strong></td>
                <td class="num">{{ t('restocking.days', { count: rec.lead_time_days }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n()
    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const budget = ref(0)
    const submitting = ref(false)
    const submitError = ref(null)
    const lastOrder = ref(null)

    const money = (amount, decimals = 0) =>
      formatCurrencyWithDecimals(amount, currentCurrency.value, decimals)

    // Items whose forecast exceeds current demand, biggest gap first
    const candidates = computed(() =>
      forecasts.value
        .map(f => ({ ...f, gap: f.forecasted_demand - f.current_demand }))
        .filter(f => f.gap > 0)
        .sort((a, b) => b.gap - a.gap)
    )

    const maxBudget = computed(() => {
      const full = candidates.value.reduce((sum, c) => sum + c.gap * c.unit_cost, 0)
      return Math.ceil(full / 100) * 100
    })

    // Fill the budget greedily; the last affordable item may get a partial quantity
    const recommendations = computed(() => {
      let remaining = budget.value
      const result = []
      for (const c of candidates.value) {
        const quantity = Math.min(c.gap, Math.floor(remaining / c.unit_cost))
        if (quantity <= 0) continue
        const line_total = Math.round(quantity * c.unit_cost * 100) / 100
        remaining -= line_total
        result.push({ ...c, quantity, line_total })
      }
      return result
    })

    const totalCost = computed(() => recommendations.value.reduce((sum, r) => sum + r.line_total, 0))
    const maxLeadTime = computed(() =>
      recommendations.value.reduce((max, r) => Math.max(max, r.lead_time_days), 0)
    )

    const placeOrder = async () => {
      submitting.value = true
      submitError.value = null
      try {
        lastOrder.value = await api.createRestockOrder({
          items: recommendations.value.map(r => ({ item_sku: r.item_sku, quantity: r.quantity }))
        })
      } catch (err) {
        submitError.value = t('restocking.submitFailed') + ': ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(async () => {
      try {
        forecasts.value = await api.getDemandForecasts()
        budget.value = Math.round(maxBudget.value / 2 / 50) * 50
      } catch (err) {
        error.value = t('restocking.loadFailed') + ': ' + err.message
      } finally {
        loading.value = false
      }
    })

    return {
      t, translateProductName, money, loading, error, budget, maxBudget,
      recommendations, totalCost, maxLeadTime, placeOrder, submitting, submitError, lastOrder
    }
  }
}
</script>

<style scoped>
.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
  margin: 0.5rem 0 0.25rem;
}

.slider-scale {
  display: flex;
  justify-content: space-between;
  font-size: 0.813rem;
  color: #64748b;
}

.stats-grid {
  margin-top: 1.5rem;
}

.place-order {
  background: #0f172a;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 0.6rem 1.25rem;
  font-weight: 600;
  cursor: pointer;
}

.place-order:hover:not(:disabled) {
  background: #1e293b;
}

.place-order:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.confirmation {
  background: #dcfce7;
  color: #166534;
  border-radius: 6px;
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
}

.confirmation a {
  color: #166534;
  font-weight: 600;
  margin-left: 0.5rem;
}

.empty {
  color: #64748b;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
}

th {
  font-size: 0.75rem;
  text-transform: uppercase;
  color: #64748b;
}

.num {
  text-align: right;
}

.badge {
  margin-left: 0.5rem;
}
</style>
