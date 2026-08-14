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
    <button class="btn gen-entry" id="gen-entry">✦ 策略生成引擎</button>
    ${strategies.length ? strategies.map(s => strategyCard(s)).join('') : '<div class="empty">暂无策略，点击右下角 + 新建，或使用策略生成引擎</div>'}
    <button class="fab" id="fab-add">+</button>
  `;
  $('#gen-entry').addEventListener('click', openGenerator);
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
      <div class="row"><div class="row-left"><div class="row-title">行情数据源</div><div class="row-sub">腾讯/新浪公开行情 API（真实数据）</div></div></div>
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
  ctx.strokeStyle = '#2563eb';
  ctx.lineWidth = 2;
  ctx.beginPath();
  curve.forEach((p, i) => {
    const x = pad + i / (curve.length - 1) * (w - pad * 2);
    const y = h - pad - (p.equity - min) / range * (h - pad * 2);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.stroke();
}

// ===== 策略生成引擎 =====
const GEN_COLORS = ['#2563eb', '#ef4444', '#10b981', '#f59e0b', '#8e44ad', '#14b8a6', '#e0245e', '#3b82f6', '#d97706', '#059669'];

function toYMD(d) {
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
}

function openGenerator() {
  $('#generator').classList.add('open');
  renderGeneratorForm();
}

function closeGenerator() {
  $('#generator').classList.remove('open');
}

function renderGeneratorForm() {
  const today = new Date();
  const endDef = toYMD(today);
  const startDef = toYMD(new Date(today.getFullYear() - 1, today.getMonth(), today.getDate()));
  let scope = 'single';
  let risk = 'balanced';
  $('#generator').innerHTML = `
    <div class="editor-head">
      <span class="editor-back" id="gen-back">‹</span>
      <span class="editor-title">策略生成引擎</span>
    </div>
    <div class="editor-body">
      <div class="section-label">标的范围</div>
      <div class="chips" id="gen-scope-chips">
        <span class="chip on" data-scope="single">单只股票</span>
        <span class="chip" data-scope="custom">自定义组合</span>
        <span class="chip" data-scope="market">全市场</span>
      </div>
      <div class="chip-params" id="gen-codes-wrap">
        <div class="field">
          <label>股票代码（逗号分隔）</label>
          <input type="text" id="gen-codes" placeholder="如 600519,000001" />
        </div>
      </div>
      <div class="section-label">回测区间</div>
      <div class="gen-dates">
        <div class="field"><label>开始日期</label><input type="date" id="gen-start" value="${startDef}" /></div>
        <div class="field"><label>结束日期</label><input type="date" id="gen-end" value="${endDef}" /></div>
      </div>
      <div class="section-label">风险偏好</div>
      <div class="chips" id="gen-risk-chips">
        <span class="chip" data-risk="conservative">保守</span>
        <span class="chip on" data-risk="balanced">稳健</span>
        <span class="chip" data-risk="aggressive">激进</span>
      </div>
      <div class="section-label">生成数量（1-10）</div>
      <div class="chip-params"><div class="field"><input type="number" id="gen-count" min="1" max="10" value="3" /></div></div>
      <div class="section-label">目标年化收益率 %（0 表示不限）</div>
      <div class="chip-params"><div class="field"><input type="number" id="gen-target" min="0" step="1" value="15" /></div></div>
      <div class="section-label">数据源</div>
      <div class="gen-datasource">腾讯公开行情接口（前复权真实日线），不可用时返回错误</div>
    </div>
    <div class="editor-foot">
      <button class="btn btn-ghost" id="gen-cancel" style="flex:1">取消</button>
      <button class="btn" id="gen-run" style="flex:1">开始生成</button>
    </div>
  `;

  $('#gen-back').addEventListener('click', closeGenerator);
  $('#gen-cancel').addEventListener('click', closeGenerator);
  $('#gen-scope-chips').addEventListener('click', e => {
    const chip = e.target.closest('.chip');
    if (!chip) return;
    scope = chip.dataset.scope;
    $('#gen-scope-chips').querySelectorAll('.chip').forEach(c => c.classList.toggle('on', c === chip));
    $('#gen-codes-wrap').style.display = scope === 'market' ? 'none' : '';
  });
  $('#gen-risk-chips').addEventListener('click', e => {
    const chip = e.target.closest('.chip');
    if (!chip) return;
    risk = chip.dataset.risk;
    $('#gen-risk-chips').querySelectorAll('.chip').forEach(c => c.classList.toggle('on', c === chip));
  });
  $('#gen-run').addEventListener('click', () => runGenerator(scope, risk));
}

async function runGenerator(scope, risk) {
  const codesStr = $('#gen-codes').value.trim();
  const startDate = $('#gen-start').value;
  const endDate = $('#gen-end').value;
  const count = parseInt($('#gen-count').value, 10);
  const target = parseFloat($('#gen-target').value) || 0;

  const codes = codesStr ? codesStr.split(/[,，\s]+/).filter(Boolean) : [];
  if (scope !== 'market' && codes.length === 0) { toast('请填写股票代码'); return; }
  if (!startDate || !endDate) { toast('请选择回测区间'); return; }
  if (!count || count < 1 || count > 10) { toast('生成数量需在 1~10 之间'); return; }

  const payload = {
    targets: { scope, codes },
    start_date: startDate,
    end_date: endDate,
    risk_profile: risk,
    count,
    target_annual_return: target,
  };

  $('#generator').innerHTML = `
    <div class="editor-head">
      <span class="editor-back" id="gen-back2">‹</span>
      <span class="editor-title">策略生成中</span>
    </div>
    <div class="editor-body" style="display:flex;align-items:center;justify-content:center;flex-direction:column;gap:12px">
      <div class="gen-loading"></div>
      <div style="color:var(--text-sub);font-size:13px">正在获取真实行情并回测 ${count} 个候选策略，请稍候...</div>
    </div>
  `;
  $('#gen-back2').addEventListener('click', () => renderGeneratorForm());

  try {
    const report = await api('/api/generator/run', { method: 'POST', body: payload });
    renderGeneratorResult(report);
  } catch (err) {
    toast(err.message);
    renderGeneratorForm();
  }
}

function sigNames(signals) {
  const buyNames = (signals.buy || []).map(k => { const d = SIGNAL_DEFS.buy.find(x => x.key === k); return d ? d.name : k; });
  const sellNames = (signals.sell || []).map(k => { const d = SIGNAL_DEFS.sell.find(x => x.key === k); return d ? d.name : k; });
  return buyNames.join('+') + ' / ' + sellNames.join('+');
}

function renderGeneratorResult(report) {
  const req = report.request;
  const strategies = report.strategies.slice().sort((a, b) => a.index - b.index);
  const rec = report.recommended_index;
  const legend = strategies.map(s => `
    <span class="gen-legend-item"><i style="background:${GEN_COLORS[s.index % GEN_COLORS.length]}"></i>#${s.index + 1}${s.index === rec ? ' ★推荐' : ''}</span>
  `).join('');

  $('#generator').innerHTML = `
    <div class="editor-head">
      <span class="editor-back" id="gen-back3">‹</span>
      <span class="editor-title">生成结果对比</span>
    </div>
    <div class="editor-body">
      <div class="gen-datasource" style="margin-bottom:10px">
        ${req.targets.scope === 'market' ? '全市场' : req.targets.scope === 'single' ? '单只 ' + (req.targets.codes[0] || '') : '自定义 ' + (req.targets.codes || []).join(',')}
        · ${req.start_date} ~ ${req.end_date} · ${req.risk_profile === 'conservative' ? '保守' : req.risk_profile === 'aggressive' ? '激进' : '稳健'} · 目标年化 ${req.target_annual_return}%
      </div>

      ${strategies[rec] ? `
        <div class="gen-recommend">
          <div class="gen-recommend-title">推荐策略 #${rec + 1}</div>
          <div class="gen-recommend-sig">${esc(sigNames(strategies[rec].signals))}</div>
          <div class="gen-recommend-metrics">
            <span>年化 <b class="${(strategies[rec].metrics.annual_return_pct ?? 0) >= 0 ? 'up' : 'down'}">${strategies[rec].metrics.annual_return_pct}%</b></span>
            <span>回撤 <b class="down">${strategies[rec].metrics.max_drawdown_pct}%</b></span>
            <span>胜率 <b>${strategies[rec].metrics.win_rate_pct}%</b></span>
          </div>
          <button class="btn" id="gen-save-rec" style="width:100%">保存为策略</button>
        </div>
      ` : ''}

      <div class="card">
        <div class="card-title">权益曲线对比</div>
        <canvas id="gen-chart" width="300" height="170"></canvas>
        <div class="gen-legend">${legend}</div>
      </div>

      <div class="card">
        <div class="card-title">策略对比</div>
        <table class="gen-table">
          <thead><tr>
            <th>#</th><th>信号</th><th>年化%</th><th>累计%</th><th>回撤%</th><th>胜率%</th><th>操作</th>
          </tr></thead>
          <tbody>
            ${strategies.map(s => `
              <tr>
                <td>${s.index + 1}${s.index === rec ? ' ★' : ''}</td>
                <td class="gen-sig-cell">${esc(sigNames(s.signals))}</td>
                <td class="${(s.metrics.annual_return_pct ?? 0) >= 0 ? 'up' : 'down'}">${s.metrics.annual_return_pct ?? '-'}</td>
                <td class="${(s.metrics.total_return_pct ?? 0) >= 0 ? 'up' : 'down'}">${s.metrics.total_return_pct ?? '-'}</td>
                <td class="down">${s.metrics.max_drawdown_pct ?? '-'}</td>
                <td>${s.metrics.win_rate_pct ?? '-'}</td>
                <td><button class="gen-save-btn" data-idx="${s.index}">保存</button></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;

  $('#gen-back3').addEventListener('click', () => renderGeneratorForm());
  $('#gen-save-rec').addEventListener('click', () => saveGeneratedStrategy(strategies[rec]));
  $('#generator').querySelectorAll('.gen-save-btn').forEach(el => {
    el.addEventListener('click', () => saveGeneratedStrategy(strategies[Number(el.dataset.idx)]));
  });
  drawMultiEquity($('#gen-chart'), strategies.map(s => s.equity_curve));
}

async function saveGeneratedStrategy(s) {
  if (!s) return;
  try {
    await api('/api/strategies', { method: 'POST', body: {
      name: 'AI生成策略 #' + (s.index + 1) + ' ' + sigNames(s.signals).split('/')[0],
      enabled: true,
      config: s.config,
    }});
    await refreshData();
    toast('已保存到策略列表');
  } catch (err) { toast(err.message); }
}

function drawMultiEquity(canvas, curves) {
  if (!canvas || !curves || curves.length === 0) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;
  const pad = 8;
  let all = [];
  curves.forEach(c => { if (c) all = all.concat(c.map(p => p.equity)); });
  if (all.length === 0) return;
  const min = Math.min(...all), max = Math.max(...all);
  const range = (max - min) || 1;
  ctx.clearRect(0, 0, w, h);
  const axisY = v => h - pad - (v - min) / range * (h - pad * 2);
  curves.forEach((curve, idx) => {
    if (!curve || curve.length < 2) return;
    ctx.strokeStyle = GEN_COLORS[idx % GEN_COLORS.length];
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    curve.forEach((p, i) => {
      const x = pad + i / (curve.length - 1) * (w - pad * 2);
      const y = axisY(p.equity);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.stroke();
  });
  ctx.strokeStyle = '#ddd';
  ctx.lineWidth = 1;
  ctx.setLineDash([4, 4]);
  ctx.beginPath();
  ctx.moveTo(pad, axisY(max));
  ctx.lineTo(w - pad, axisY(max));
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle = '#909399';
  ctx.font = '10px sans-serif';
  ctx.textAlign = 'right';
  ctx.fillText(max.toFixed(0), w - pad - 2, axisY(max) - 3);
  ctx.fillText(min.toFixed(0), w - pad - 2, axisY(min) + 10);
}

// ===== K 线图 =====
const KLINE_PERIODS = [
  { k: 'day', label: '日K', days: 90 },
  { k: 'week', label: '周K', days: 120 },
  { k: 'month', label: '月K', days: 120 },
  { k: 'year', label: '年K', days: 50 },
];

async function showKline(code, name) {
  toast('加载 K 线...');
  const cache = {};
  const mask = document.createElement('div');
  mask.className = 'dialog-mask show';
  mask.id = 'kline-dialog';
  mask.innerHTML = `
    <div class="dialog" style="width:94%">
      <div class="dialog-title">${esc(name)}
        <span style="color:var(--text-sub);font-size:12px">${esc(code)}</span>
      </div>
      <div class="dialog-desc" id="kline-desc"></div>
      <div class="filter-tabs" id="kline-periods" style="margin-top:8px">
        ${KLINE_PERIODS.map(p => `<span class="filter-tab${p.k === 'day' ? ' active' : ''}" data-p="${p.k}">${p.label}</span>`).join('')}
      </div>
      <div class="kline-wrap">
        <canvas id="kline-chart" style="width:100%;height:300px"></canvas>
        <div class="kline-info" id="kline-info"></div>
      </div>
      <div class="kline-legend">
        <span><i style="background:#ef4444"></i>阳线</span>
        <span><i style="background:#10b981"></i>阴线</span>
        <span><i style="background:#f59e0b"></i>MA5</span>
        <span><i style="background:#2563eb"></i>MA10</span>
        <span><i style="background:#a855f7"></i>MA20</span>
      </div>
      <div class="dialog-actions">
        <button class="dialog-btn primary" id="kline-close">关闭</button>
      </div>
    </div>
  `;
  document.body.appendChild(mask);
  mask.addEventListener('click', e => { if (e.target === mask) mask.remove(); });
  $('#kline-close').addEventListener('click', () => mask.remove());
  $('#kline-periods').addEventListener('click', e => {
    const tab = e.target.closest('.filter-tab');
    if (tab) loadPeriod(tab.dataset.p);
  });
  async function loadPeriod(p) {
    const meta = KLINE_PERIODS.find(x => x.k === p);
    if (!cache[p]) {
      toast('加载 ' + meta.label + '...');
      try { cache[p] = await api(`/api/stocks/${code}/bars?days=${meta.days}&period=${p}`); }
      catch (err) { cache[p] = null; toast(err.message); }
    }
    const bars = cache[p];
    if (!bars || bars.length < 2) { toast('无' + meta.label + '数据'); return; }
    document.querySelectorAll('#kline-periods .filter-tab').forEach(t => t.classList.toggle('active', t.dataset.p === p));
    const last = bars[bars.length - 1];
    const prev = bars[bars.length - 2];
    const chg = prev ? (last.close - prev.close) / prev.close * 100 : 0;
    const cls = chg >= 0 ? 'up' : 'down';
    $('#kline-desc').innerHTML =
      `${bars[0].date} ~ ${last.date} · 最新价 ${last.close} ` +
      `<span class="${cls}">${chg >= 0 ? '+' : ''}${chg.toFixed(2)}%</span>`;
    drawKline($('#kline-chart'), bars);
  }
  await loadPeriod('day');
}

function drawKline(canvas, bars) {
  if (!bars || bars.length < 2) return;
  const dpr = window.devicePixelRatio || 1;
  const cssW = Math.max(200, Math.round(canvas.getBoundingClientRect().width));
  const cssH = canvas.getBoundingClientRect().height || 300;
  canvas.width = Math.round(cssW * dpr);
  canvas.height = Math.round(cssH * dpr);
  const ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const w = cssW, h = cssH;
  const padL = 10, padR = 48, padT = 12, padB = 22;
  const plotW = w - padL - padR;
  const mainH = Math.round((h - padT - padB) * 0.7);
  const volH = Math.round((h - padT - padB) * 0.3) - 14;
  const volBase = padT + mainH + 10;
  const n = bars.length;
  const cw = plotW / n;
  const bw = Math.max(2.5, Math.min(cw * 0.8, 14));
  const x = i => padL + i * cw + cw / 2;
  const fmtPrice = v => v.toFixed(2);
  const fmtVol = v => v >= 1e8 ? (v / 1e8).toFixed(2) + '亿'
    : v >= 1e4 ? (v / 1e4).toFixed(0) + '万' : String(v);

  const closes = bars.map(b => b.close);
  const ma = (arr, p) => arr.map((_, i) => i < p - 1 ? null : arr.slice(i - p + 1, i + 1).reduce((a, b) => a + b, 0) / p);
  const ma5 = ma(closes, 5), ma10 = ma(closes, 10), ma20 = ma(closes, 20);
  const allVals = [...bars.flatMap(b => [b.high, b.low]), ...ma20.filter(v => v !== null)];
  const min = Math.min(...allVals), max = Math.max(...allVals);
  const range = (max - min) || 1;
  const maxVol = Math.max(...bars.map(b => b.volume));
  const y = v => padT + (max - v) / range * mainH;

  const UP = '#ef4444', DOWN = '#10b981';

  function render(crossIdx) {
    ctx.clearRect(0, 0, w, h);
    ctx.font = '10px -apple-system, "PingFang SC", "Helvetica Neue", sans-serif';
    // 主图网格 + 价格轴
    ctx.strokeStyle = '#e6eaf0';
    ctx.lineWidth = 1;
    ctx.fillStyle = '#9aa3b2';
    for (let g = 0; g <= 4; g++) {
      const gy = padT + g / 4 * mainH;
      ctx.beginPath();
      ctx.moveTo(padL, gy);
      ctx.lineTo(padL + plotW, gy);
      ctx.stroke();
      ctx.fillText(fmtPrice(max - (max - min) * g / 4), padL + plotW + 6, gy + 3);
    }
    // 成交量网格
    ctx.strokeStyle = '#eef0f4';
    for (let g = 0; g <= 2; g++) {
      const gy = volBase + g / 2 * volH;
      ctx.beginPath();
      ctx.moveTo(padL, gy);
      ctx.lineTo(padL + plotW, gy);
      ctx.stroke();
    }
    // 蜡烛 + 量柱
    ctx.lineWidth = 1;
    bars.forEach((b, i) => {
      const up = b.close >= b.open;
      const color = up ? UP : DOWN;
      ctx.strokeStyle = color;
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.moveTo(x(i), y(b.high));
      ctx.lineTo(x(i), y(b.low));
      ctx.stroke();
      const bt = y(Math.max(b.open, b.close));
      const bb = y(Math.min(b.open, b.close));
      ctx.fillRect(x(i) - bw / 2, bt, bw, Math.max(1, bb - bt));
      const vh = Math.max(1, b.volume / maxVol * volH);
      ctx.globalAlpha = 0.6;
      ctx.fillRect(x(i) - bw / 2, volBase + volH - vh, bw, vh);
      ctx.globalAlpha = 1;
    });
    // 均线
    const drawLine = (arr, color) => {
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.6;
      ctx.lineJoin = 'round';
      ctx.beginPath();
      let started = false;
      arr.forEach((v, i) => {
        if (v === null) { started = false; return; }
        if (!started) { ctx.moveTo(x(i), y(v)); started = true; }
        else ctx.lineTo(x(i), y(v));
      });
      ctx.stroke();
    };
    drawLine(ma5, '#f59e0b');
    drawLine(ma10, '#2563eb');
    drawLine(ma20, '#a855f7');
    // 十字光标
    if (crossIdx !== null && crossIdx >= 0 && crossIdx < n) {
      const b = bars[crossIdx];
      const cx = x(crossIdx), cy = y(b.close);
      ctx.strokeStyle = 'rgba(60,70,90,0.5)';
      ctx.setLineDash([4, 3]);
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(cx, padT);
      ctx.lineTo(cx, volBase + volH);
      ctx.moveTo(padL, cy);
      ctx.lineTo(padL + plotW, cy);
      ctx.stroke();
      ctx.setLineDash([]);
      const color = b.close >= b.open ? UP : DOWN;
      const label = fmtPrice(b.close);
      ctx.font = '10px -apple-system, "PingFang SC", sans-serif';
      const lw = ctx.measureText(label).width + 8;
      ctx.fillStyle = color;
      ctx.fillRect(padL + plotW - lw, cy - 8, lw, 15);
      ctx.fillStyle = '#fff';
      ctx.fillText(label, padL + plotW - lw + 4, cy + 4);
    }
  }

  function canvasPos(e) {
    const rect = canvas.getBoundingClientRect();
    return {
      px: (e.clientX - rect.left) * (canvas.width / rect.width),
      py: (e.clientY - rect.top) * (canvas.height / rect.height),
    };
  }
  function idxFromX(px) {
    const i = Math.floor((px - padL) / cw);
    return i >= 0 && i < n ? i : null;
  }

  const infoEl = document.getElementById('kline-info');
  function updateInfo(i) {
    if (!infoEl || i === null) return;
    const b = bars[i];
    const prev = bars[i - 1] ? bars[i - 1].close : b.open;
    const chg = prev ? (b.close - prev) / prev * 100 : 0;
    const cls = chg >= 0 ? 'up' : 'down';
    const mv = (arr, i) => arr[i] ? fmtPrice(arr[i]) : '-';
    infoEl.innerHTML =
      `<span><b>${b.date}</b></span>` +
      `<span>开 <b>${fmtPrice(b.open)}</b></span>` +
      `<span>高 <b class="up">${fmtPrice(b.high)}</b></span>` +
      `<span>低 <b class="down">${fmtPrice(b.low)}</b></span>` +
      `<span>收 <b>${fmtPrice(b.close)}</b></span>` +
      `<span class="${cls}">${chg >= 0 ? '+' : ''}${chg.toFixed(2)}%</span>` +
      `<span>量 <b>${fmtVol(b.volume)}</b></span>` +
      `<span>MA5 <b>${mv(ma5, i)}</b></span>` +
      `<span>MA10 <b>${mv(ma10, i)}</b></span>` +
      `<span>MA20 <b>${mv(ma20, i)}</b></span>`;
  }

  render(null);
  if (infoEl) infoEl.innerHTML = '';
  canvas.style.touchAction = 'none';
  canvas.addEventListener('pointermove', e => {
    const i = idxFromX(canvasPos(e).px);
    render(i);
    updateInfo(i);
  });
  canvas.addEventListener('pointerleave', () => {
    render(null);
    if (infoEl) infoEl.innerHTML = '';
  });
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
