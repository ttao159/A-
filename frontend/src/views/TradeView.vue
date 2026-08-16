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
      </div>
    </div>

    <div class="card">
      <div class="card-title">{{ tab === 'trades' ? '成交记录' : '委托记录' }}</div>

      <template v-if="tab === 'trades'">
        <div v-if="!tradeStore.trades.length" class="empty">暂无成交</div>
        <div v-for="t in tradeStore.trades" :key="'t' + t.id" class="list-item">
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
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useTradeStore } from '../stores/trade'
import { usePullRefresh } from '../composables/pullRefresh'
import { fmtMoney, fmtPrice } from '../utils/format'

const tradeStore = useTradeStore()
const tab = ref<'trades' | 'orders'>('trades')

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
