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
      <div class="stat-sub">
        盈利 {{ tradeStats.wins }} 笔 · 亏损 {{ tradeStats.losses }} 笔 · 卖出胜率 {{ tradeStats.winRate }}%
      </div>
    </div>

    <div class="card">
      <div class="card-title">{{ tab === 'trades' ? '成交记录' : '委托记录' }}</div>

      <template v-if="tab === 'trades'">
        <input v-model="tradeSearch" class="search-input" placeholder="按代码或名称搜索" />
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
        <div v-for="t in filteredTrades" :key="'t' + t.id" class="list-item trade-item" @click="toggleDetail(t.id)">
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
            <div class="muted">{{ fmtDateTime(t.traded_at) }}</div>
          </div>
          <div v-if="expandedId === t.id" class="trade-detail">
            <span>成交额 {{ fmtMoney(t.price * t.qty) }}</span>
            <span>佣金 {{ fmtMoney(t.commission) }}</span>
            <span>印花税 {{ fmtMoney(t.tax) }}</span>
          </div>
        </div>
        <button
          v-if="tradeStore.tradeHasMore"
          class="btn ghost load-more"
          :disabled="tradeStore.loadingMore"
          @click="tradeStore.fetchMoreTrades()"
        >
          {{ tradeStore.loadingMore ? '加载中...' : '加载更多' }}
        </button>
      </template>

      <template v-else>
        <div class="filter-row">
          <button
            v-for="f in orderFilters"
            :key="f.key"
            class="filter-btn"
            :class="{ active: orderFilter === f.key }"
            @click="orderFilter = f.key"
          >
            {{ f.label }}
          </button>
        </div>
        <div v-if="!filteredOrders.length" class="empty">暂无委托</div>
        <div v-for="o in filteredOrders" :key="'o' + o.id" class="list-item">
          <div style="flex: 1">
            <div style="font-weight: 500">
              {{ o.name }} <span class="muted">{{ o.code }}</span>
            </div>
            <div class="muted">
              {{ o.direction === 'buy' ? '买入' : '卖出' }} {{ o.qty }} 股 @ {{ fmtPrice(o.price) }}
            </div>
          </div>
          <div style="text-align: right">
            <div :class="o.status === 'filled' ? 'text-primary' : 'text-danger'">
              {{ o.status === 'filled' ? '已成交' : '已拒绝' }}
            </div>
            <div class="muted">{{ o.broker_type === 'live' ? '实盘' : '模拟' }}</div>
          </div>
        </div>
        <button
          v-if="tradeStore.orderHasMore"
          class="btn ghost load-more"
          :disabled="tradeStore.loadingMore"
          @click="tradeStore.fetchMoreOrders()"
        >
          {{ tradeStore.loadingMore ? '加载中...' : '加载更多' }}
        </button>
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
import { fmtMoney, fmtPrice, fmtDateTime } from '../utils/format'

const tradeStore = useTradeStore()
const tab = ref<'trades' | 'orders'>('trades')
const showOrder = ref(false)
const tradeFilter = ref<'all' | 'buy' | 'sell'>('all')
const tradeSearch = ref('')
const expandedId = ref<number | null>(null)

const tradeFilters = [
  { key: 'all', label: '全部' },
  { key: 'buy', label: '买入' },
  { key: 'sell', label: '卖出' },
] as const

const orderFilter = ref<'all' | 'filled' | 'rejected'>('all')

const orderFilters = [
  { key: 'all', label: '全部' },
  { key: 'filled', label: '已成交' },
  { key: 'rejected', label: '已拒绝' },
] as const

const filteredOrders = computed(() => {
  if (orderFilter.value === 'all') return tradeStore.orders
  return tradeStore.orders.filter((o) => o.status === orderFilter.value)
})

const filteredTrades = computed(() => {
  let list = tradeStore.trades
  if (tradeFilter.value !== 'all') list = list.filter((t) => t.direction === tradeFilter.value)
  const q = tradeSearch.value.trim()
  if (q) list = list.filter((t) => t.code.includes(q) || t.name.includes(q))
  return list
})

const tradeStats = computed(() => {
  const s = tradeStore.tradeSummary
  const sells = s.sells
  return {
    total: s.total,
    buys: s.buys,
    sells: s.sells,
    pnl: s.pnl,
    wins: s.wins,
    losses: s.losses,
    winRate: sells ? Math.round((s.wins / sells) * 100) : 0,
  }
})

function toggleDetail(id: number) {
  expandedId.value = expandedId.value === id ? null : id
}

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
  background: var(--card);
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

.stat-sub {
  margin-top: 10px;
  font-size: 13px;
  color: var(--text-2);
  text-align: center;
}

.search-input {
  margin-bottom: 10px;
  height: 38px;
}

.load-more {
  width: 100%;
  margin-top: 10px;
}

.trade-item {
  flex-wrap: wrap;
  cursor: pointer;
}

.trade-detail {
  flex-basis: 100%;
  display: flex;
  gap: 12px;
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px dashed var(--border);
  font-size: 12px;
  color: var(--text-2);
}
</style>
