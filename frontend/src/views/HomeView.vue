<template>
  <div>
    <div v-if="accountStore.loading && !accountStore.account" class="empty">加载中...</div>
    <div v-else-if="accountStore.error" class="empty">{{ accountStore.error }}</div>
    <template v-else>
      <AssetCard v-if="accountStore.account" :account="accountStore.account" />
      <PositionList :positions="positionStore.positions" />
      <div class="card">
        <button class="btn ghost block" @click="onReset">重置模拟账户</button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import AssetCard from '../components/AssetCard.vue'
import PositionList from '../components/PositionList.vue'
import { useAccountStore } from '../stores/account'
import { usePositionStore } from '../stores/position'
import { usePullRefresh } from '../composables/pullRefresh'

const accountStore = useAccountStore()
const positionStore = usePositionStore()

onMounted(() => {
  refresh()
})

usePullRefresh(refresh)

function refresh() {
  accountStore.fetch()
  positionStore.fetch()
}

async function onReset() {
  if (!window.confirm('确认重置模拟账户？将清空持仓与交易记录，各策略资金恢复本金。')) return
  await accountStore.reset()
  positionStore.fetch()
}
</script>
