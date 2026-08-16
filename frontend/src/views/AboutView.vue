<template>
  <div>
    <div class="card">
      <div class="card-title">账户说明</div>
      <div class="info-row"><span>账户模式</span><b>{{ accountStore.isLive ? '实盘' : '模拟盘' }}</b></div>
      <div class="info-row"><span>初始资金</span><b>{{ fmtMoney(accountStore.account?.initial_capital ?? 0) }}</b></div>
      <div class="info-row"><span>扫描时间</span><b>交易日 15:05 收盘后</b></div>
    </div>

    <div class="card">
      <div class="card-title">操作指南</div>
      <div class="guide-item"><b>账户</b><span>查看总资产、资金曲线、持仓概览与预警提醒，下拉可刷新。</span></div>
      <div class="guide-item"><b>策略</b><span>新建/编辑策略，查看详情预览，一键启停与删除。</span></div>
      <div class="guide-item"><b>回测</b><span>选择策略与日期区间运行回测，查看收益曲线、回撤与信号统计。</span></div>
      <div class="guide-item"><b>交易</b><span>手动下单，查看成交与委托记录，支持按状态筛选与搜索。</span></div>
      <div class="guide-item"><b>扫描</b><span>一键全市场扫描，按策略信号自动交易并生成报告。</span></div>
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
      <div class="card-title">策略参数说明</div>
      <div class="guide-item"><b>买入信号</b><span>均线金叉、MACD 金叉、突破新高、放量突破、RSI 超卖、KDJ 金叉、布林下轨反弹等，可多选组合。</span></div>
      <div class="guide-item"><b>卖出信号</b><span>止盈、止损、移动止盈、均线死叉、MACD 死叉、跌破均线、最大持有天数等。</span></div>
      <div class="guide-item"><b>风控参数</b><span>单只最大仓位、最大持仓数、单只最大亏损、组合整体止损、最大回撤，触发即强制生效。</span></div>
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

.guide-item {
  display: flex;
  gap: 10px;
  padding: 7px 0;
  border-bottom: 1px dashed var(--border);
  font-size: 13px;
  line-height: 1.5;
}

.guide-item:last-child {
  border-bottom: none;
}

.guide-item b {
  flex: 0 0 56px;
  font-weight: 600;
}

.guide-item span {
  color: var(--text-2);
}
</style>
