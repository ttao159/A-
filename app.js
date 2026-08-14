// ===== 信号与风控定义 =====
const SIGNAL_DEFS = {
  buy: [
    { key: 'maCross', name: '均线金叉', desc: '短期均线上穿长期均线', params: [
      { key: 'shortPeriod', label: '短周期', value: 5 },
      { key: 'longPeriod', label: '长周期', value: 20 },
    ]},
    { key: 'macdCross', name: 'MACD 金叉', desc: 'DIF 上穿 DEA', params: [
      { key: 'fast', label: '快线', value: 12 },
      { key: 'slow', label: '慢线', value: 26 },
      { key: 'signal', label: '信号线', value: 9 },
    ]},
    { key: 'breakHigh', name: '突破 N 日最高价', desc: '收盘价突破近 N 日最高价', params: [
      { key: 'days', label: '天数', value: 20 },
    ]},
    { key: 'volumeBreak', name: '放量突破', desc: '成交量突破均量倍数', params: [
      { key: 'multiple', label: '倍数', value: 1.5 },
      { key: 'avgDays', label: '均量周期', value: 5 },
    ]},
    { key: 'hammer', name: '锤子线', desc: '实体小、下影线长，见底反转', params: []},
    { key: 'bullishEngulfing', name: '看涨吞没', desc: '阳线实体吞没前一根阴线', params: []},
    { key: 'morningStar', name: '早晨之星', desc: '阴线+星线+阳线，见底反转', params: []},
    { key: 'threeWhiteSoldiers', name: '红三兵', desc: '连续三根阳线，收盘逐日抬高', params: []},
    { key: 'doubleBottom', name: '双底', desc: '两个相近低点后突破颈线', params: []},
  ],
  sell: [
    { key: 'takeProfit', name: '固定止盈', desc: '盈利达到百分比卖出', params: [
      { key: 'percent', label: '止盈 %', value: 10 },
    ]},
    { key: 'stopLoss', name: '固定止损', desc: '亏损达到百分比卖出', params: [
      { key: 'percent', label: '止损 %', value: 5 },
    ]},
    { key: 'trailingStop', name: '移动止盈', desc: '从最高价回撤百分比卖出', params: [
      { key: 'drawdown', label: '回撤 %', value: 8 },
    ]},
    { key: 'maDeathCross', name: '均线死叉', desc: '短期均线下穿长期均线', params: [
      { key: 'shortPeriod', label: '短周期', value: 5 },
      { key: 'longPeriod', label: '长周期', value: 20 },
    ]},
    { key: 'macdDeathCross', name: 'MACD 死叉', desc: 'DIF 下穿 DEA', params: []},
    { key: 'belowMA', name: '跌破均线', desc: '收盘价跌破某均线', params: [
      { key: 'period', label: '均线周期', value: 20 },
    ]},
    { key: 'maxHoldDays', name: '持有天数到期', desc: '持有超过 N 个交易日卖出', params: [
      { key: 'days', label: '天数', value: 20 },
    ]},
    { key: 'hangingMan', name: '上吊线', desc: '上涨末端，实体小、下影线长', params: []},
    { key: 'bearishEngulfing', name: '看跌吞没', desc: '阴线实体吞没前一根阳线', params: []},
    { key: 'eveningStar', name: '黄昏之星', desc: '阳线+星线+阴线，见顶反转', params: []},
    { key: 'threeBlackCrows', name: '三只乌鸦', desc: '连续三根阴线，收盘逐日走低', params: []},
    { key: 'doubleTop', name: '双顶', desc: '两个相近高点后跌破颈线', params: []},
  ],
};

const RISK_DEFS = [
  { key: 'maxPositionPercent', label: '单只股票最大仓位 %', value: 20 },
  { key: 'maxHoldings', label: '最大同时持仓数量', value: 10 },
  { key: 'maxSingleLoss', label: '单只股票最大亏损 %', value: 15 },
  { key: 'totalStopLoss', label: '组合整体止损 %', value: 20 },
  { key: 'maxDrawdown', label: '最大回撤限制 %', value: 25 },
];

// ===== API 封装 =====
async function api(path, opts = {}) {
  const init = { headers: { 'Content-Type': 'application/json' }, ...opts };
  if (init.body && typeof init.body !== 'string') init.body = JSON.stringify(init.body);
  const r = await fetch(path, init);
  if (!r.ok) {
    let msg = '请求失败';
    try { msg = (await r.json()).detail || msg; } catch (e) {}
    throw new Error(msg);
  }
  return r.json();
}

// ===== 状态 =====
let strategies = [];
let currentTab = 'home';
let editingId = null;
let accountData = null;
let positionsData = [];
let tradesData = [];

// ===== 工具 =====
const $ = (sel, root = document) => root.querySelector(sel);
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const fmtMoney = n => '¥' + Number(n).toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
const fmtMoney2 = n => '¥' + Number(n).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const pnlClass = n => n >= 0 ? 'up' : 'down';
const sign = n => n >= 0 ? '+' : '';

function defaultStrategy() {
  const buy = {}, sell = {}, risk = {};
  SIGNAL_DEFS.buy.forEach(s => {
    buy[s.key] = { enabled: false, ...Object.fromEntries(s.params.map(p => [p.key, p.value])) };
  });
  SIGNAL_DEFS.sell.forEach(s => {
    sell[s.key] = { enabled: false, ...Object.fromEntries(s.params.map(p => [p.key, p.value])) };
  });
  RISK_DEFS.forEach(r => risk[r.key] = r.value);
  buy.breakHigh.enabled = true;
  sell.takeProfit.enabled = true;
  sell.stopLoss.enabled = true;
  return { id: null, name: '新策略', enabled: true, config: { buy, sell, risk } };
}

function toast(msg) {
  const t = $('#toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove('show'), 1800);
}

// ===== 状态栏 =====
function updateClock() {
  const now = new Date();
  $('#sb-time').textContent = String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0');
}

// ===== 渲染：首页 =====
function renderHome() {
  $('#appbar-title').textContent = '账户总览';
  const acct = accountData || { available_cash: 0, market_value: 0, total_asset: 0, total_pnl: 0, initial_capital: 0 };
  $('#content').innerHTML = `
    <div class="asset-card">
      <div class="asset-total-label">总资产 (元)</div>
      <div class="asset-total">${fmtMoney(acct.total_asset)}</div>
      <div class="asset-row"><span>可用资金</span><span class="val">${fmtMoney2(acct.available_cash)}</span></div>
      <div class="asset-row"><span>持仓市值</span><span class="val">${fmtMoney2(acct.market_value)}</span></div>
      <div class="asset-row"><span>累计盈亏</span><span class="val ${pnlClass(acct.total_pnl)}">${sign(acct.total_pnl)}${fmtMoney2(acct.total_pnl)}</span></div>
    </div>
    <div class="card">
      <div class="card-title">当前持仓</div>
      ${positionsData.length ? positionsData.map(p => `
        <div class="holding" data-code="${esc(p.code)}" data-name="${esc(p.name)}">
          <div>
            <div class="holding-name">${esc(p.name)}</div>
            <div class="holding-code">${esc(p.code)} · ${p.qty} 股${p.hold_days === 0 ? ' · <span class="tag t1-lock">T+1 锁定</span>' : ' · 持 ${p.hold_days} 天'}</div>
          </div>
          <div class="holding-right">
            <div class="holding-pnl ${pnlClass(p.pnl_pct)}">${sign(p.pnl_pct)}${p.pnl_pct}% <span class="holding-amt">${sign(p.pnl)}${fmtMoney2(p.pnl)}</span></div>
            <div class="holding-pct">成本 ${p.avg_cost} / 现价 ${p.price}</div>
          </div>
        </div>
      `).join('') : '<div class="empty">暂无持仓</div>'}
    </div>
  `;
  document.querySelectorAll('.holding').forEach(el => {
    el.addEventListener('click', () => showKline(el.dataset.code, el.dataset.name));
  });
}

// ===== 渲染：策略 =====
function renderStrategy() {
  $('#appbar-title').textContent = '策略管理';
  $('#content').innerHTML = `
    ${strategies.length ? strategies.map(s => strategyCard(s)).join('') : '<div class="empty">暂无策略，点击右下角 + 新建</div>'}
    <button class="fab" id="fab-add">+</button>
  `;
  $('#fab-add').addEventListener('click', () => openEditor(null));

  document.querySelectorAll('.strategy-card').forEach(el => {
    el.addEventListener('click', e => {
      if (e.target.closest('.switch') || e.target.closest('.strat-action')) return;
      openEditor(el.dataset.id);
    });
  });
  document.querySelectorAll('[data-toggle]').forEach(el => {
    el.addEventListener('click', async () => {
      const s = strategies.find(x => x.id === Number(el.dataset.id));
      s.enabled = !s.enabled;
      try { await api('/api/strategies/' + s.id, { method: 'PUT', body: { enabled: s.enabled } }); }
      catch (err) { toast(err.message); s.enabled = !s.enabled; }
      renderStrategy();
    });
  });
  document.querySelectorAll('[data-action="backtest"]').forEach(el => {
    el.addEventListener('click', () => runBacktest(Number(el.dataset.id)));
  });
  document.querySelectorAll('[data-action="history"]').forEach(el => {
    el.addEventListener('click', () => showHistory(Number(el.dataset.id)));
  });
  document.querySelectorAll('[data-action="edit"]').forEach(el => {
    el.addEventListener('click', () => openEditor(Number(el.dataset.id)));
  });
  document.querySelectorAll('[data-action="delete"]').forEach(el => {
    el.addEventListener('click', async () => {
      if (!confirm('确定删除该策略？')) return;
      try { await api('/api/strategies/' + el.dataset.id, { method: 'DELETE' }); }
      catch (err) { toast(err.message); }
      await refreshData();
      renderStrategy();
    });
  });
}

function strategyCard(s) {
  const buyTags = SIGNAL_DEFS.buy.filter(d => s.config.buy[d.key] && s.config.buy[d.key].enabled);
  const sellTags = SIGNAL_DEFS.sell.filter(d => s.config.sell[d.key] && s.config.sell[d.key].enabled);
  const tags = [...buyTags.map(d => d.name), ...sellTags.map(d => d.name)];
  return `
    <div class="card strategy-card" data-id="${s.id}">
      <div class="strategy-head">
        <span class="strategy-name">${esc(s.name)}</span>
        <div class="switch ${s.enabled ? 'on' : ''}" data-toggle data-id="${s.id}"></div>
      </div>
      <div class="strategy-tags">
        ${tags.length ? tags.map(t => `<span class="tag">${esc(t)}</span>`).join('') : '<span class="tag off">未配置信号</span>'}
      </div>
      <div class="strat-actions">
        <button class="strat-action" data-action="backtest" data-id="${s.id}">回测</button>
        <button class="strat-action" data-action="history" data-id="${s.id}">历史</button>
        <button class="strat-action" data-action="edit" data-id="${s.id}">编辑</button>
        <button class="strat-action danger" data-action="delete" data-id="${s.id}">删除</button>
      </div>
    </div>
  `;
}

// ===== 渲染：交易 =====
function renderTrade() {
  $('#appbar-title').textContent = '交易记录';
  $('#content').innerHTML = `
    <div class="filter-tabs">
      <span class="filter-tab active" data-f="all">全部</span>
      <span class="filter-tab" data-f="buy">买入</span>
      <span class="filter-tab" data-f="sell">卖出</span>
    </div>
    <div class="card">
      ${tradesData.length ? tradesData.map(t => `
        <div class="trade-item">
          <div class="trade-top">
            <span>${esc(t.name)} <span class="badge-${t.direction === 'buy' ? 'buy' : 'sell'}">${t.direction === 'buy' ? '买入' : '卖出'}</span></span>
            <span>${t.qty} 股</span>
          </div>
          <div class="trade-mid"><span>${esc(t.code)}</span><span>成交价 ${t.price}</span></div>
          <div class="trade-mid"><span style="color:#c0c4cc">${(t.traded_at || '').slice(0, 19).replace('T', ' ')}</span></div>
        </div>
      `).join('') : '<div class="empty">暂无交易记录</div>'}
    </div>
  `;
  document.querySelectorAll('.filter-tab').forEach(el => {
    el.addEventListener('click', () => {
      document.querySelectorAll('.filter-tab').forEach(x => x.classList.remove('active'));
      el.classList.add('active');
    });
  });
}

// ===== 渲染：我的 =====
function renderMine() {
  $('#appbar-title').textContent = '我的';
  $('#content').innerHTML = `
    <div class="card">
      <div class="row"><div class="row-left"><div class="row-title">模拟账户</div><div class="row-sub">初始资金 100 万元 · A 股主板</div></div></div>
      <div class="row"><div class="row-left"><div class="row-title">扫描范围</div><div class="row-sub">沪深主板（排除创业板、科创板）</div></div></div>
      <div class="row"><div class="row-left"><div class="row-title">行情数据源</div><div class="row-sub">akshare</div></div></div>
      <div class="row"><div class="row-left"><div class="row-title">撮合模式</div><div class="row-sub">本地模拟撮合</div></div></div>
    </div>
    <div class="card">
      <div class="row"><div class="row-left"><div class="row-title">系统运行状态</div><div class="row-sub">策略引擎运行中 · 每日 15:05 自动扫描</div></div><span class="tag">运行中</span></div>
    </div>
    <div class="card">
      <button class="btn" id="scan-btn" style="margin-bottom:10px">立即扫描交易</button>
      <button class="btn btn-ghost" id="reset-btn">重置模拟账户</button>
    </div>
  `;
  $('#scan-btn').addEventListener('click', scanNow);
  $('#reset-btn').addEventListener('click', resetAccount);
}

async function scanNow() {
  toast('扫描中，请稍候...');
  try {
    const r = await api('/api/scan', { method: 'POST' });
    await refreshData();
    const msg = '扫描完成：买入 ' + r.buys.length + ' 笔，卖出 ' + r.sells.length + ' 笔'
      + (r.rejected && r.rejected.length ? '，' + r.rejected.length + ' 笔被风控拦截' : '');
    toast(msg);
    switchTab('home');
  } catch (err) { toast(err.message); }
}

async function resetAccount() {
  if (!confirm('确定重置模拟账户？将清空持仓与交易记录，资金恢复 100 万。')) return;
  try {
    await api('/api/account/reset', { method: 'POST' });
    await refreshData();
    toast('账户已重置');
    switchTab('home');
  } catch (err) { toast(err.message); }
}

// ===== 策略编辑器 =====
function openEditor(id) {
  editingId = id;
  const s = id ? strategies.find(x => x.id === Number(id)) : defaultStrategy();
  $('#editor').innerHTML = editorHtml(s);
  $('#editor').classList.add('open');

  const editor = $('#editor');
  $('#editor-back').addEventListener('click', closeEditor);
  $('#editor-cancel').addEventListener('click', closeEditor);
  $('#editor-save').addEventListener('click', () => saveEditor(s));

  editor.addEventListener('click', e => {
    const chip = e.target.closest('.chip');
    if (!chip) return;
    const [type, key] = chip.dataset.sig.split('.');
    s.config[type][key].enabled = !s.config[type][key].enabled;
    refreshSignals(s);
  });

  editor.addEventListener('input', e => {
    const inp = e.target;
    if (!(inp instanceof HTMLInputElement)) return;
    const v = parseFloat(inp.value);
    if (inp.dataset.risk) s.config.risk[inp.dataset.risk] = isNaN(v) ? 0 : v;
    else if (inp.dataset.type) s.config[inp.dataset.type][inp.dataset.key][inp.dataset.param] = isNaN(v) ? 0 : v;
  });
}

function refreshSignals(s) {
  document.querySelectorAll('.chip').forEach(chip => {
    const [type, key] = chip.dataset.sig.split('.');
    chip.classList.toggle('on', s.config[type][key].enabled);
  });
  $('#buy-params').innerHTML = paramsHtml('buy', s.config.buy);
  $('#sell-params').innerHTML = paramsHtml('sell', s.config.sell);
}

function editorHtml(s) {
  const buyChips = SIGNAL_DEFS.buy.map(d => chipHtml('buy', d, s.config.buy[d.key].enabled)).join('');
  const sellChips = SIGNAL_DEFS.sell.map(d => chipHtml('sell', d, s.config.sell[d.key].enabled)).join('');
  const riskSection = RISK_DEFS.map(r => `
    <div class="field" style="flex:1 1 45%; min-width:140px">
      <label>${esc(r.label)}</label>
      <input type="number" data-risk="${r.key}" value="${s.config.risk[r.key]}" step="0.1" />
    </div>
  `).join('');

  return `
    <div class="editor-head">
      <span class="editor-back" id="editor-back">‹</span>
      <span class="editor-title">${editingId ? '编辑策略' : '新建策略'}</span>
    </div>
    <div class="editor-body">
      <div class="section-label">买入信号（全部满足才买入）</div>
      <div class="chips">${buyChips}</div>
      <div class="chip-params" id="buy-params">${paramsHtml('buy', s.config.buy)}</div>
      <div class="section-label">卖出信号（任一满足即卖出）</div>
      <div class="chips">${sellChips}</div>
      <div class="chip-params" id="sell-params">${paramsHtml('sell', s.config.sell)}</div>
      <div class="section-label">风控参数</div>
      <div class="signal" style="display:flex;flex-wrap:wrap;gap:10px">${riskSection}</div>
    </div>
    <div class="editor-foot">
      <button class="btn btn-ghost" id="editor-cancel" style="flex:1">取消</button>
      <button class="btn" id="editor-save" style="flex:1">保存策略</button>
    </div>
  `;
}

function chipHtml(type, def, on) {
  return `<span class="chip ${on ? 'on' : ''}" data-sig="${type}.${def.key}">${esc(def.name)}</span>`;
}

function paramsHtml(type, stateMap) {
  const defs = type === 'buy' ? SIGNAL_DEFS.buy : SIGNAL_DEFS.sell;
  return defs.filter(d => stateMap[d.key].enabled && d.params.length).map(d => `
    <div class="chip-param-block">
      <div class="chip-param-title">${esc(d.name)}</div>
      <div class="chip-param-fields">
        ${d.params.map(p => `
          <div class="field">
            <label>${esc(p.label)}</label>
            <input type="number" data-type="${type}" data-key="${d.key}" data-param="${p.key}" value="${stateMap[d.key][p.key]}" step="0.1" />
          </div>
        `).join('')}
      </div>
    </div>
  `).join('');
}

function saveEditor(s) {
  openNameDialog(s);
}

function openNameDialog(s) {
  $('#dialog-name').value = s.name === '新策略' ? '' : s.name;
  $('#name-dialog').classList.add('show');
  setTimeout(() => $('#dialog-name').focus(), 150);

  const confirm = async () => {
    const name = $('#dialog-name').value.trim();
    if (!name) { toast('请输入策略名称'); $('#dialog-name').focus(); return; }
    s.name = name;
    try {
      const payload = { name: s.name, enabled: s.enabled, config: s.config };
      if (s.id) await api('/api/strategies/' + s.id, { method: 'PUT', body: payload });
      else await api('/api/strategies', { method: 'POST', body: payload });
      await refreshData();
      $('#name-dialog').classList.remove('show');
      closeEditor();
      renderStrategy();
      toast('策略已保存');
    } catch (err) { toast(err.message); }
  };

  $('#dialog-ok').onclick = confirm;
  $('#dialog-cancel').onclick = () => $('#name-dialog').classList.remove('show');
  $('#dialog-name').onkeydown = e => { if (e.key === 'Enter') confirm(); };
}

function closeEditor() {
  $('#editor').classList.remove('open');
}

// ===== 回测 =====
async function runBacktest(id) {
  const s = strategies.find(x => x.id === id);
  if (!s) return;
  toast('回测运行中，请稍候...');
  try {
    const data = await api('/api/strategies/' + id + '/backtest', { method: 'POST', body: {} });
    showBacktestResult(s, data);
  } catch (err) { toast(err.message); }
}

function showBacktestResult(s, data) {
  const m = data.metrics;
  if (!m || Object.keys(m).length === 0) { toast('回测无结果'); return; }
  const rows = [
    ['累计收益率', m.total_return_pct + '%'],
    ['年化收益率', m.annual_return_pct + '%'],
    ['最大回撤', m.max_drawdown_pct + '%'],
    ['胜率', m.win_rate_pct + '%'],
    ['盈亏比', m.profit_loss_ratio],
    ['交易次数', m.trade_count],
  ];
  const trades = data.trades || [];
  const recentTrades = trades.slice(-10).reverse();
  const tradeHtml = recentTrades.length ? `
    <div class="bt-trades-title">最近成交</div>
    <div class="bt-trades">
      ${recentTrades.map(t => `
        <div class="bt-trade">
          <span class="bt-trade-name">${esc(t.name)}</span>
          <span class="badge-${t.direction === 'buy' ? 'buy' : 'sell'}">${t.direction === 'buy' ? '买入' : '卖出'}</span>
          <span class="bt-trade-meta">${t.qty}股 · ${t.price}</span>
          <span class="${t.pnl > 0 ? 'up' : t.pnl < 0 ? 'down' : ''}">${t.direction === 'sell' ? (t.pnl > 0 ? '+' : '') + t.pnl.toFixed(0) : ''}</span>
        </div>
      `).join('')}
    </div>
  ` : '<div class="bt-trades-title">最近成交</div><div class="empty">暂无成交记录</div>';
  const mask = document.createElement('div');
  mask.className = 'dialog-mask show';
  mask.id = 'backtest-dialog';
  mask.innerHTML = `
    <div class="dialog" style="width:88%">
      <div class="dialog-title">回测结果 · ${esc(s.name)}</div>
      <div class="dialog-desc">${data.start_date} ~ ${data.end_date}</div>
      <canvas id="bt-chart" width="300" height="120"></canvas>
      <div class="bt-metrics">
        ${rows.map(r => `
          <div class="bt-metric"><div class="bt-metric-val">${esc(String(r[1]))}</div><div class="bt-metric-label">${esc(r[0])}</div></div>
        `).join('')}
      </div>
      ${tradeHtml}
      <div class="dialog-actions">
        <button class="dialog-btn primary" id="bt-close">关闭</button>
      </div>
    </div>
  `;
  document.body.appendChild(mask);
  mask.addEventListener('click', e => { if (e.target === mask) mask.remove(); });
  $('#bt-close').addEventListener('click', () => mask.remove());
  drawEquityCurve($('#bt-chart'), data.equity_curve);
}

async function showHistory(id) {
  const s = strategies.find(x => x.id === id);
  if (!s) return;
  let items;
  try { items = await api('/api/strategies/' + id + '/backtests'); }
  catch (err) { toast(err.message); return; }
  const mask = document.createElement('div');
  mask.className = 'dialog-mask show';
  mask.id = 'history-dialog';
  mask.innerHTML = `
    <div class="dialog" style="width:88%">
      <div class="dialog-title">回测历史 · ${esc(s.name)}</div>
      <div class="bt-history">
        ${items.length ? items.map(it => `
          <div class="bt-history-item" data-bid="${it.id}">
            <div class="bt-history-top">
              <span class="bt-history-range">${it.start_date} ~ ${it.end_date}</span>
              <span class="${(it.metrics.total_return_pct ?? 0) >= 0 ? 'up' : 'down'}">${(it.metrics.total_return_pct ?? 0).toFixed(2)}%</span>
            </div>
            <div class="bt-history-sub">胜率 ${(it.metrics.win_rate_pct ?? 0).toFixed(0)}% · 交易 ${it.metrics.trade_count ?? 0} 次 · 回撤 ${(it.metrics.max_drawdown_pct ?? 0).toFixed(1)}%</div>
          </div>
        `).join('') : '<div class="empty">暂无回测记录，先运行一次回测</div>'}
      </div>
      <div class="dialog-actions">
        <button class="dialog-btn" id="his-close">关闭</button>
      </div>
    </div>
  `;
  document.body.appendChild(mask);
  mask.addEventListener('click', e => { if (e.target === mask) mask.remove(); });
  $('#his-close').addEventListener('click', () => mask.remove());
  mask.querySelectorAll('.bt-history-item').forEach(el => {
    el.addEventListener('click', async () => {
      const bid = Number(el.dataset.bid);
      mask.remove();
      try {
        const data = await api('/api/strategies/' + id + '/backtests/' + bid);
        showBacktestResult(s, data);
      } catch (err) { toast(err.message); }
    });
  });
}

function drawEquityCurve(canvas, curve) {
  if (!curve || curve.length < 2) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;
  const pad = 6;
  const values = curve.map(p => p.equity);
  const min = Math.min(...values), max = Math.max(...values);
  const range = (max - min) || 1;
  ctx.clearRect(0, 0, w, h);
  ctx.strokeStyle = '#1976d2';
  ctx.lineWidth = 2;
  ctx.beginPath();
  curve.forEach((p, i) => {
    const x = pad + i / (curve.length - 1) * (w - pad * 2);
    const y = h - pad - (p.equity - min) / range * (h - pad * 2);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.stroke();
}

// ===== K 线图 =====
async function showKline(code, name) {
  toast('加载 K 线...');
  let bars;
  try { bars = await api('/api/stocks/' + code + '/bars?days=90'); }
  catch (err) { toast(err.message); return; }
  if (!bars || bars.length < 2) { toast('无行情数据'); return; }
  const last = bars[bars.length - 1];
  const mask = document.createElement('div');
  mask.className = 'dialog-mask show';
  mask.id = 'kline-dialog';
  mask.innerHTML = `
    <div class="dialog" style="width:92%">
      <div class="dialog-title">${esc(name)} <span style="color:var(--text-sub);font-size:12px">${esc(code)}</span></div>
      <div class="dialog-desc">最新价 ${last.close} · ${bars[0].date} ~ ${last.date}</div>
      <canvas id="kline-chart" width="320" height="220"></canvas>
      <div class="kline-legend">
        <span><i style="background:#e53935"></i>阳线</span>
        <span><i style="background:#1e9e5a"></i>阴线</span>
        <span><i style="background:#f0a020"></i>MA5</span>
        <span><i style="background:#1976d2"></i>MA20</span>
      </div>
      <div class="dialog-actions">
        <button class="dialog-btn primary" id="kline-close">关闭</button>
      </div>
    </div>
  `;
  document.body.appendChild(mask);
  mask.addEventListener('click', e => { if (e.target === mask) mask.remove(); });
  $('#kline-close').addEventListener('click', () => mask.remove());
  drawKline($('#kline-chart'), bars);
}

function drawKline(canvas, bars) {
  if (!bars || bars.length < 2) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;
  const padL = 6, padR = 8, padT = 8, padB = 16;
  const plotW = w - padL - padR, plotH = h - padT - padB;
  const n = bars.length;

  const closes = bars.map(b => b.close);
  const ma = (arr, p) => arr.map((_, i) => i < p - 1 ? null : arr.slice(i - p + 1, i + 1).reduce((a, b) => a + b, 0) / p);
  const ma5 = ma(closes, 5), ma20 = ma(closes, 20);
  const allVals = [...bars.flatMap(b => [b.high, b.low]), ...ma20.filter(v => v !== null)];
  const min = Math.min(...allVals), max = Math.max(...allVals);
  const range = (max - min) || 1;
  const x = i => padL + i / (n - 1) * plotW;
  const y = v => padT + (max - v) / range * plotH;
  const cw = Math.max(1, plotW / n * 0.65);

  ctx.clearRect(0, 0, w, h);
  bars.forEach((b, i) => {
    const up = b.close >= b.open;
    const color = up ? '#e53935' : '#1e9e5a';
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.moveTo(x(i), y(b.high));
    ctx.lineTo(x(i), y(b.low));
    ctx.stroke();
    const bodyTop = y(Math.max(b.open, b.close));
    const bodyBot = y(Math.min(b.open, b.close));
    ctx.fillRect(x(i) - cw / 2, bodyTop, cw, Math.max(1, bodyBot - bodyTop));
  });

  const drawLine = (arr, color) => {
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ctx.beginPath();
    let started = false;
    arr.forEach((v, i) => {
      if (v === null) return;
      if (!started) { ctx.moveTo(x(i), y(v)); started = true; }
      else ctx.lineTo(x(i), y(v));
    });
    ctx.stroke();
  };
  drawLine(ma5, '#f0a020');
  drawLine(ma20, '#1976d2');
}

// ===== 底部导航 =====
function switchTab(tab) {
  currentTab = tab;
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
  if (tab === 'home') renderHome();
  else if (tab === 'strategy') renderStrategy();
  else if (tab === 'trade') renderTrade();
  else renderMine();
}

document.querySelectorAll('.tab').forEach(t => {
  t.addEventListener('click', () => switchTab(t.dataset.tab));
});

// ===== 数据刷新 =====
async function refreshData() {
  try {
    const [s, acct, pos, trd] = await Promise.all([
      api('/api/strategies'),
      api('/api/account'),
      api('/api/positions'),
      api('/api/trades'),
    ]);
    strategies = s;
    accountData = acct;
    positionsData = pos;
    tradesData = trd;
  } catch (e) {
    toast('无法连接后端服务');
  }
}

// ===== 初始化 =====
updateClock();
setInterval(updateClock, 10000);
(async () => {
  await refreshData();
  switchTab('home');
})();
