<template>
  <div>
    <div class="card">
      <div class="card-title">账户说明</div>
      <div class="info-row"><span>账户模式</span><b>{{ accountStore.isLive ? '实盘' : '模拟盘' }}</b></div>
      <div class="info-row"><span>初始资金</span><b>{{ fmtMoney(accountStore.account?.initial_capital ?? 0) }}</b></div>
      <div class="info-row"><span>扫描时间</span><b>交易日 15:05 收盘后</b></div>
    </div>

    <div class="card">
      <div class="card-title">数据来源</div>
      <div class="info-row"><span>股票列表</span><b>新浪财经公开接口</b></div>
      <div class="info-row"><span>日线 / 分时 / 实时</span><b>腾讯行情公开接口</b></div>
      <div class="muted" style="margin-top: 8px; font-size: 12px">仅使用真实公开行情，不做合成数据。</div>
    </div>

    <div class="card">
      <div class="card-title">扫描范围</div>
      <div class="muted" style="font-size: 13px; line-height: 1.6">
        沪深 A 股主板，剔除创业板（300/301）与科创板（688/689），规避高波动与涨跌幅限制差异。
      </div>
    </div>

    <div class="card">
      <div class="card-title">交易费用（A 股规则）</div>
      <div class="info-row"><span>佣金</span><b>万 2.5（最低 5 元）</b></div>
      <div class="info-row"><span>印花税</span><b>0.05%（仅卖出）</b></div>
      <div class="info-row"><span>过户费</span><b>0.001%</b></div>
    </div>

    <div class="card">
      <div class="card-title">风控说明</div>
      <div class="info-row"><span>单笔委托上限</span><b>50 万元</b></div>
      <div class="info-row"><span>单日委托上限</span><b>200 万元</b></div>
      <div class="info-row"><span>生效条件</span><b>仅实盘模式</b></div>
    </div>

    <div class="card">
      <div class="muted" style="font-size: 12px; line-height: 1.6">
        本系统仅供学习与技术演示，模拟盘不构成任何投资建议。实盘交易存在风险，接入前请谨慎评估并核实每笔委托。
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAccountStore } from '../stores/account'
import { fmtMoney } from '../utils/format'

const accountStore = useAccountStore()
</script>

<style scoped>
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 7px 0;
  border-bottom: 1px dashed var(--border);
  font-size: 14px;
}

.info-row b {
  font-weight: 600;
}
</style>
