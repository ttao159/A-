<template>
  <div>
    <div class="card">
      <div class="card-title">账户说明</div>
      <div class="info-row"><span>账户模式</span><b>{{ accountStore.isLive ? '实盘' : '模拟盘' }}</b></div>
      <div class="info-row"><span>初始资金</span><b>{{ fmtMoney(accountStore.account?.initial_capital ?? 0) }}</b></div>
      <div class="info-row"><span>资金曲线</span><b>按日记录总资产</b></div>
      <div class="info-row"><span>扫描时间</span><b>{{ schedule }}</b></div>
    </div>

    <div class="card">
      <div class="card-title">操作指南</div>
      <div class="guide-item"><b>账户</b><span>查看总资产、资金曲线、持仓概览与预警提醒，下拉可刷新。</span></div>
      <div class="guide-item"><b>股票</b><span>点击持仓代码进入详情，支持日K/分时切换、双指缩放、十字光标与均线开关。</span></div>
      <div class="guide-item"><b>策略</b><span>新建/编辑策略，查看详情预览，一键启停与删除。</span></div>
      <div class="guide-item"><b>回测</b><span>选择策略与日期区间运行回测，支持近 1 月/3 月/6 月/1 年快捷区间；核心指标突出展示，历史回测可按盈亏分类、按收益/胜率/回撤排序，点击查看以弹窗展示结果，支持删除。</span></div>
      <div class="guide-item"><b>交易</b><span>手动下单，查看成交与委托记录，支持分页加载、状态筛选与搜索。</span></div>
      <div class="guide-item"><b>扫描</b><span>一键全市场扫描，按策略信号自动交易；支持 AI 生成策略与多观点分析。</span></div>
      <div class="guide-item"><b>生成</b><span>按风险偏好一键生成策略组合，历史记录可按偏好筛选、查看与删除。</span></div>
    </div>

    <div class="card">
      <div class="card-title">数据来源</div>
      <div class="info-row"><span>股票列表</span><b>新浪财经公开接口</b></div>
      <div class="info-row"><span>日线 / 分时 / 实时</span><b>腾讯行情公开接口</b></div>
      <div class="info-row"><span>策略生成</span><b>内置智能体推理</b></div>
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
      <div class="card-title">版本信息</div>
      <div class="info-row"><span>当前版本</span><b>v{{ version }}</b></div>
      <div class="changelog">
        <div class="changelog-item"><span class="changelog-tag">优化</span>账户页：今日盈亏、指数涨跌点数与闪烁、策略收益率高亮、盘前倒计时</div>
        <div class="changelog-item"><span class="changelog-tag">优化</span>实时收益高亮：总盈亏大号强调、实时角标、刷新闪烁</div>
        <div class="changelog-item"><span class="changelog-tag">修复</span>持仓收益实时显示：现价改用实时行情接口，盘中随行情更新</div>
        <div class="changelog-item"><span class="changelog-tag">优化</span>历史回测查看改为弹窗展示，关闭后停留列表原位</div>
        <div class="changelog-item"><span class="changelog-tag">优化</span>回测页排版：快捷日期区间、核心指标突出、参数优化触控选择</div>
        <div class="changelog-item"><span class="changelog-tag">新增</span>回测历史查看与删除、生成历史分类筛选与删除</div>
        <div class="changelog-item"><span class="changelog-tag">新增</span>扫描历史详情、实盘扫描确认与下次扫描倒计时</div>
        <div class="changelog-item"><span class="changelog-tag">新增</span>K线双指缩放、十字光标与均线显示开关</div>
        <div class="changelog-item"><span class="changelog-tag">新增</span>委托与成交分页加载、下单数字键盘</div>
        <div class="changelog-item"><span class="changelog-tag">优化</span>全站暗色适配、图表高清与触控体验</div>
        <div class="changelog-item"><span class="changelog-tag">新增</span>AI 策略生成与智能体多观点分析</div>
      </div>
    </div>

    <div class="card">
      <div class="disclaimer">
        本系统仅供学习与技术演示，模拟盘不构成任何投资建议。实盘交易存在风险，接入前请谨慎评估并核实每笔委托。
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useAccountStore } from '../stores/account'
import { scanApi } from '../api'
import { fmtMoney } from '../utils/format'
import { version } from '../../package.json'

const accountStore = useAccountStore()

const schedule = ref('交易日 15:05 收盘后')
onMounted(async () => {
  try {
    const r = await scanApi.reports()
    const s = r.scan_schedule
    if (s) {
      const h = String(s.hour).padStart(2, '0')
      const m = String(s.minute).padStart(2, '0')
      schedule.value = `每交易日 ${h}:${m} 自动扫描`
    }
  } catch {
    // 调度信息加载失败时保留默认文案
  }
})
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
  flex: 0 0 48px;
  font-weight: 600;
}

.guide-item span {
  color: var(--text-2);
}

.changelog {
  margin-top: 8px;
}

.changelog-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 0;
  font-size: 13px;
  color: var(--text-2);
}

.changelog-tag {
  flex: 0 0 auto;
  font-size: 11px;
  font-weight: 600;
  color: var(--primary);
  background: var(--focus-ring);
  padding: 1px 6px;
  border-radius: 4px;
}

.disclaimer {
  background: var(--warning-bg);
  border: 1px solid var(--warning);
  color: var(--warning);
  border-radius: 10px;
  padding: 12px 14px;
  font-size: 13px;
  line-height: 1.6;
}
</style>
