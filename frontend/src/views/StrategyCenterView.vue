<template>
  <div>
    <div class="sub-tabs">
      <router-link :to="{ path: '/strategy' }" class="sub-tab" exact-active-class="active">策略</router-link>
      <router-link to="/strategy/backtest" class="sub-tab" active-class="active">回测</router-link>
      <router-link to="/strategy/screener" class="sub-tab" active-class="active">选股</router-link>
      <router-link to="/strategy/scan" class="sub-tab" active-class="active">扫描</router-link>
    </div>
    <router-view v-slot="{ Component }">
      <Transition name="page" mode="out-in">
        <component :is="Component" />
      </Transition>
    </router-view>
  </div>
</template>

<style scoped>
.sub-tabs {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  gap: 6px;
  padding: 8px 16px 0;
  background: var(--bg);
}

.sub-tab {
  flex: 1;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: var(--text-2);
  text-decoration: none;
  border-radius: 9px;
  background: var(--card);
  border: 1px solid var(--border);
  transition: color 0.15s, border-color 0.15s, transform 0.1s ease;
  -webkit-tap-highlight-color: transparent;
}

.sub-tab:active {
  transform: scale(0.95);
}

.sub-tab.active {
  color: var(--primary);
  border-color: var(--primary);
  background: var(--focus-ring);
  font-weight: 600;
}
</style>
