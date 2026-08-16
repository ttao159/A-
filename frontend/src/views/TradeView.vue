<template>
  <div>
    <div class="card">
      <div class="row" style="gap: 8px">
        <button class="btn" :class="tab === 'trades' ? '' : 'ghost'" style="flex: 1" @click="setTab('trades')">
          成交
        </button>
        <button class="btn" :class="tab === 'orders' ? '' : 'ghost'" style="flex: 1" @click="setTab('orders')">
          委托
        </button>
        <button class="btn ghost" style="flex: 1" @click="showOrder = true">下单</button>
      </div>
    </div>

    <div class="card">
      <div class="card-title">交易统计</div>
      <div class="stat-grid">
        <div class="metric">
          <div class="muted">累计成交</div>
          <div>{{ tradeStats.total }}</div>
        </div>
        <div class="metric">
          <div class="muted">买入</div>
          <div class="up">{{ tradeStats.buys }}</div>
        </div>
        <div class="metric">
          <div class="muted">卖出</div>
          <div class="down">{{ tradeStats.sells }}</div>
        </div>
        <div class="metric">
          <div class="muted">已实现盈亏</div>
          <div :class="tradeStats.pnl >= 0 ? 'up' : 'down'">{{ fmtMoney(tradeStats.pnl) }}</div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">{{ tab === 'trades' ? '成交记录' : '委托记录' }}</div>

      <template v-if="tab === 'trades'">
        <div class="filter-row">
          <button
            v-for="f in tradeFilters"
            :key="f.key"
            class="filter-btn"
            :class="{ active: tradeFilter === f.key }"
            @click="tradeFilter = f.key"
          >
            {{ f.label }}
          </button>
        </div>
        <div v-if="!filteredTrades.length" class="empty">暂无成交</div>
        <div v-for="t in filteredTrades" :key="'t' + t.id" class="list-item">
          <div style="flex: 1">
            <div style="font-weight: 500">
              {{ t.name }} <span class="muted">{{ t.code }}</span>
            </div>
            <div class="muted">
              {{ t.direction === 'buy' ? '买入' : '卖出' }} {{ t.qty }} 股 @ {{ fmtPrice(t.price) }}
            </div>
          </div>
          <div style="text-align: right">
            <div :class="t.pnl >= 0 ? 'up' : 'down'">{{ fmtMoney(t.pnl) }}</div>
            <div class="muted">{{ (t.traded_at || '').slice(5, 16) }}</div>
          </div>
        </div>
      </template>

      <template v-else>
        <div v-if="!tradeStore.orders.length" class="empty">暂无委托</div>
        <div v-for="o in tradeStore.orders" :key="'o' + o.id" class="list-item">
          <div style="flex: 1">
            <div style="font-weight: 500">
              {{ o.name }} <span class="muted">{{ o.code }}</span>
            </div>
            <div class="muted">
              {{ o.direction === 'buy' ? '买入' : '卖出' }} {{ o.qty }} 股 @ {{ fmtPrice(o.price) }}
            </div>
          </div>
          <div style="text-align: right">
            <div :class="o.status === 'filled' ? 'down' : 'up'">
              {{ o.status === 'filled' ? '已成交' : '已拒绝' }}
            </div>
            <div class="muted">{{ o.broker_type === 'live' ? '实盘' : '模拟' }}</div>
          </div>
        </div>
      </template>
    </div>

    <OrderPanel :visible="showOrder" @close="showOrder = false" @done="load" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import OrderPanel from '../components/OrderPanel.vue'
import { useTradeStore } from '../stores/trade'
import { usePullRefresh } from '../composables/pullRefresh'
import { fmtMoney, fmtPrice } from '../utils/format'

const tradeStore = useTradeStore()
const tab = ref<'trades' | 'orders'>('trades')
const showOrder = ref(false)
const tradeFilter = ref<'all' | 'buy' | 'sell'>('all')

const tradeFilters = [
  { key: 'all', label: '全部' },
  { key: 'buy', label: '买入' },
  { key: 'sell', label: '卖出' },
] as const

const filteredTrades = computed(() => {
  if (tradeFilter.value === 'all') return tradeStore.trades
  return tradeStore.trades.filter((t) => t.direction === tradeFilter.value)
})

const tradeStats = computed(() => {
  const trades = tradeStore.trades
  return {
    total: trades.length,
    buys: trades.filter((t) => t.direction === 'buy').length,
    sells: trades.filter((t) => t.direction === 'sell').length,
    pnl: trades.reduce((s, t) => s + (t.pnl || 0), 0),
  }
})

onMounted(load)
usePullRefresh(load)

function load() {
  if (tab.value === 'trades') tradeStore.fetchTrades()
  else tradeStore.fetchOrders()
}

function setTab(t: 'trades' | 'orders') {
  tab.value = t
  load()
}
</script>

<style scoped>
.filter-row {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.filter-btn {
  flex: 1;
  height: 32px;
  border-radius: 16px;
  border: 1px solid var(--border);
  background: #fff;
  color: var(--text);
  font-size: 13px;
}

.filter-btn.active {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.metric {
  background: var(--bg);
  border-radius: 8px;
  padding: 10px 6px;
  text-align: center;
}

.metric div:last-child {
  font-size: 15px;
  font-weight: 600;
  margin-top: 2px;
}
</style>
