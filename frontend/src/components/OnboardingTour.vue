<template>
  <div class="onboarding-mask" @click.self="close">
    <Transition name="onboard-card" mode="out-in">
      <div :key="step" class="onboard-card">
        <div class="onboard-icon">
          <Icon :name="steps[step].icon" :size="28" />
        </div>
        <div class="onboard-step">{{ step + 1 }} / {{ steps.length }}</div>
        <h3 class="onboard-title">{{ steps[step].title }}</h3>
        <p class="onboard-desc">{{ steps[step].desc }}</p>

        <div class="onboard-dots">
          <span
            v-for="i in steps.length"
            :key="i"
            class="onboard-dot"
            :class="{ active: i - 1 === step, done: i - 1 < step }"
          ></span>        </div>

        <div class="onboard-actions">
          <button class="btn ghost" @click="close">跳过</button>
          <button v-if="step < steps.length - 1" class="btn" @click="step++">下一步</button>
          <button v-else class="btn" @click="finish">开始使用</button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Icon from './Icon.vue'

const STORAGE_KEY = 'onboarding_v1_done'

const steps = [
  {
    icon: 'wallet',
    title: '账户总览',
    desc: '首页展示总资产、今日盈亏、资金曲线与持仓概览，下拉可刷新行情，右上角可切换模拟盘 / 实盘演示。',
  },
  {
    icon: 'swap',
    title: '快捷交易',
    desc: '在「交易」页输入股票代码或名称，支持 1成 / 3成 / 半仓 / 满仓快捷下单，并查看委托与成交记录。',
  },
  {
    icon: 'target',
    title: '策略中心',
    desc: '底部「策略中心」提供策略、回测、选股、扫描四个二级页签，可新建策略、运行回测并智能选股。',
  },
  {
    icon: 'bell',
    title: '预警与通知',
    desc: '右上角铃铛查看预警通知，头像进入个人中心设置主题与数据；「说明」页含完整操作指南与 FAQ。',
  },
]

const step = ref(0)

function close() {
  localStorage.setItem(STORAGE_KEY, '1')
  document.body.style.overflow = ''
  emitClose()
}

function finish() {
  close()
}

function emitClose() {
  const el = document.querySelector('.onboarding-mask')
  el?.remove()
}

onMounted(() => {
  document.body.style.overflow = 'hidden'
})
</script>

<style scoped>
.onboarding-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  animation: mask-in 0.2s ease;
}

.onboard-card {
  background: var(--card);
  border-radius: 20px;
  padding: 28px 24px;
  width: 100%;
  max-width: 340px;
  text-align: center;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.24);
}

.onboard-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  margin: 0 auto 16px;
  background: linear-gradient(135deg, var(--brand-from), var(--brand-to));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.onboard-step {
  font-size: 12px;
  color: var(--text-3);
  margin-bottom: 6px;
}

.onboard-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 10px;
}

.onboard-desc {
  font-size: 14px;
  color: var(--text-2);
  line-height: 1.7;
  margin: 0 0 20px;
}

.onboard-dots {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 20px;
}

.onboard-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--border);
  transition: background 0.2s, transform 0.2s;
}

.onboard-dot.active {
  background: var(--primary);
  transform: scale(1.25);
}

.onboard-dot.done {
  background: var(--brand-to);
}

.onboard-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.onboard-actions .btn {
  flex: 1;
  justify-content: center;
}

.onboard-card-enter-active,
.onboard-card-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.onboard-card-enter-from {
  opacity: 0;
  transform: translateY(14px);
}

.onboard-card-leave-to {
  opacity: 0;
  transform: translateY(-14px);
}

@keyframes mask-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
