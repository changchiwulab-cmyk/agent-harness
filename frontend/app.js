import {
  escapeHtml,
  decisionDate,
  filterTasks,
  filterDecisions,
  aggregateTasks,
  gateState,
  uniqueValues,
  GATE_KEYS,
  TASK_FACET_KEYS,
} from './lib.js';

const REPO_URL = 'https://github.com/changchiwulab-cmyk/agent-harness';
const SOURCE_REF = 'main';

const state = { tasks: [], logs: [], decisions: [], loaded: false };
const $ = (id) => document.getElementById(id);

const FACET_IDS = {
  status: 'facet-status',
  skill_type: 'facet-skill_type',
  risk_level: 'facet-risk_level',
  approval_needed: 'facet-approval_needed',
};

const GATE_LABEL = {
  schema_check: 'schema',
  rule_check: 'rule',
  completion_check: 'completion',
  risk_check: 'risk',
};

function readFacets() {
  const out = {};
  for (const key of TASK_FACET_KEYS) {
    const el = $(FACET_IDS[key]);
    out[key] = el ? el.value : '';
  }
  return out;
}

function setLoading() {
  for (const id of ['taskList', 'timeline', 'logBoard']) {
    $(id).innerHTML = '<small>載入中…</small>';
  }
  $('summaryCards').innerHTML = '';
  $('statusPipeline').innerHTML = '';
  $('riskPipeline').innerHTML = '';
}

async function loadData() {
  const res = await fetch('./data.json');
  if (!res.ok) {
    throw new Error(`Failed to load data.json: HTTP ${res.status}`);
  }
  const payload = await res.json();
  state.tasks = (payload.tasks || []).map((t) => ({
    ...t,
    title: t.goal || t.task_id || '(no title)',
  }));
  state.logs = payload.logs || [];
  state.decisions = (payload.decisions || [])
    .map((d) => ({ ...d, _date: decisionDate(d) }))
    .sort((a, b) => a._date.localeCompare(b._date));
  state.loaded = true;
}

function populateFacetOptions() {
  const fillers = {
    status: uniqueValues(state.tasks, 'status'),
    skill_type: uniqueValues(state.tasks, 'skill_type'),
    risk_level: uniqueValues(state.tasks, 'risk_level'),
  };
  for (const [key, values] of Object.entries(fillers)) {
    const sel = $(FACET_IDS[key]);
    if (!sel) continue;
    const current = sel.value;
    sel.innerHTML = '<option value="">全部</option>' + values
      .map((v) => `<option value="${escapeHtml(v)}">${escapeHtml(v)}</option>`)
      .join('');
    if (current && values.includes(current)) sel.value = current;
  }
}

function applyFilters() {
  const keyword = $('keyword').value;
  const from = $('dateFrom').value;
  const to = $('dateTo').value;
  const facets = readFacets();

  const tasks = filterTasks(state.tasks, { keyword, from, to, facets });
  const decisions = filterDecisions(state.decisions, { keyword, from, to });
  render(tasks, decisions);
}

function renderSummary(filteredTasks, filteredDecisions) {
  const agg = aggregateTasks(filteredTasks);
  const cards = [
    ['Tasks', agg.total],
    ['Done', agg.byStatus.done || 0],
    ['Review', agg.byStatus.review || 0],
    ['Failed', agg.byStatus.failed || 0],
    ['Logs', state.logs.length],
    ['Decisions', filteredDecisions.length],
  ];
  $('summaryCards').innerHTML = cards
    .map(([label, value]) => `<article class="card"><div class="label">${escapeHtml(label)}</div><div class="value">${escapeHtml(value)}</div></article>`)
    .join('');
}

function renderPipeline(targetId, counts, order) {
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  const keys = order.filter((k) => counts[k]).concat(
    Object.keys(counts).filter((k) => !order.includes(k)),
  );
  if (total === 0) {
    $(targetId).innerHTML = '<small>無資料</small>';
    return;
  }
  $(targetId).innerHTML = keys
    .map((k) => {
      const n = counts[k] || 0;
      const pct = total ? Math.round((n / total) * 100) : 0;
      return `<div class="bar bar-${escapeHtml(k)}">
        <span class="bar-label">${escapeHtml(k)}</span>
        <span class="bar-fill" style="width:${pct}%"></span>
        <span class="bar-count">${escapeHtml(n)}</span>
      </div>`;
    })
    .join('');
}

function renderPipelines(filteredTasks) {
  const agg = aggregateTasks(filteredTasks);
  renderPipeline('statusPipeline', agg.byStatus, ['pending', 'in_progress', 'review', 'done', 'partial', 'failed']);
  renderPipeline('riskPipeline', agg.byRisk, ['low', 'medium', 'high', 'critical']);
}

function chipBtn(facet, value, label, extraClass = '') {
  return `<button type="button" class="chip ${extraClass}" data-facet="${escapeHtml(facet)}" data-value="${escapeHtml(value)}" title="點擊以此篩選">${escapeHtml(label)}</button>`;
}

function sourceLink(path, label) {
  if (!path) return `<strong>${escapeHtml(label)}</strong>`;
  const href = `${REPO_URL}/blob/${SOURCE_REF}/${path}`;
  return `<a class="source-link" href="${escapeHtml(href)}" target="_blank" rel="noopener" title="開啟 GitHub 原始檔（${escapeHtml(path)}）">${escapeHtml(label)}</a>`;
}

function renderTasks(tasks) {
  if (!tasks.length) {
    $('taskList').innerHTML = '<small>無符合條件資料</small>';
    return;
  }
  $('taskList').innerHTML = tasks
    .slice()
    .sort((a, b) => (b.date || '').localeCompare(a.date || ''))
    .map((t) => {
      const badges = [
        t.status && chipBtn('status', t.status, t.status, `chip-status-${escapeHtml(t.status)}`),
        t.skill_type && chipBtn('skill_type', t.skill_type, t.skill_type),
        t.risk_level && chipBtn('risk_level', t.risk_level, t.risk_level, `chip-risk-${escapeHtml(t.risk_level)}`),
        t.approval_needed ? chipBtn('approval_needed', 'true', '需審核', 'chip-approval') : '',
      ].filter(Boolean).join(' ');
      return `<article class="item" data-task-id="${escapeHtml(t.task_id || '')}">
        ${sourceLink(t.path, t.task_id || '')}<br />
        ${escapeHtml(t.title || '')}<br />
        <small>${escapeHtml(t.date || 'N/A')}</small>
        <div class="chips">${badges}</div>
      </article>`;
    })
    .join('');
}

function renderTimeline(decisions) {
  if (!decisions.length) {
    $('timeline').innerHTML = '<small>無符合條件資料</small>';
    return;
  }
  $('timeline').innerHTML = decisions
    .map((d) => {
      const related = d.related_task
        ? `<button type="button" class="link related-task" data-task-id="${escapeHtml(d.related_task)}">${escapeHtml(d.related_task)}</button>`
        : '<span class="muted">無</span>';
      const revisit = d.revisit_trigger ? escapeHtml(d.revisit_trigger) : '無';
      return `<article class="item timeline-item">
        <details>
          <summary>${escapeHtml(d._date || '')}｜${escapeHtml(d.decision_id || '')}</summary>
          <div class="decision-body">${escapeHtml(d.decision || '(no decision recorded)')}</div>
          <div class="kv"><span class="kv-key">理由</span><span>${escapeHtml(d.reasoning || '無補充說明')}</span></div>
          <div class="kv"><span class="kv-key">re-visit 觸發</span><span>${revisit}</span></div>
          <div class="kv"><span class="kv-key">關聯 task</span><span>${related}</span></div>
        </details>
      </article>`;
    })
    .join('');
}

function renderGateMatrix(log) {
  return GATE_KEYS.map((k) => {
    const v = log.gate_results ? log.gate_results[k] : undefined;
    const s = gateState(v);
    const display = v ?? 'N/A';
    return `<span class="gate gate-${s}" title="${escapeHtml(k)}: ${escapeHtml(display)}">
      <span class="gate-dot"></span>${escapeHtml(GATE_LABEL[k])}
    </span>`;
  }).join('');
}

function renderLogs() {
  if (!state.logs.length) {
    $('logBoard').innerHTML = '<small>找不到 log 資料</small>';
    return;
  }
  $('logBoard').innerHTML = state.logs
    .map((l) => `<article class="item">
      <strong>${escapeHtml(l.run_id || '')}</strong>
      <span class="chip">${escapeHtml(l.status || 'unknown')}</span><br />
      <small>task: ${escapeHtml(l.task_id || 'N/A')} · ${escapeHtml(l.ended_at || l.started_at || 'N/A')}</small>
      <div class="gates">${renderGateMatrix(l)}</div>
    </article>`)
    .join('');
}

function render(tasks, decisions) {
  renderSummary(tasks, decisions);
  renderPipelines(tasks);
  renderTasks(tasks);
  renderTimeline(decisions);
  renderLogs();
}

function showError(err) {
  const msg = err && err.message ? err.message : String(err);
  $('summaryCards').innerHTML = `<article class="card error"><div class="label">Error</div><div class="value">!</div><small>${escapeHtml(msg)}</small></article>`;
  for (const id of ['taskList', 'timeline', 'logBoard']) {
    $(id).innerHTML = '<small>載入失敗</small>';
  }
}

function bindEvents() {
  ['keyword', 'dateFrom', 'dateTo'].forEach((id) => $(id).addEventListener('input', applyFilters));
  for (const key of TASK_FACET_KEYS) {
    $(FACET_IDS[key]).addEventListener('change', applyFilters);
  }
  $('resetFilters').addEventListener('click', () => {
    $('keyword').value = '';
    $('dateFrom').value = '';
    $('dateTo').value = '';
    for (const key of TASK_FACET_KEYS) $(FACET_IDS[key]).value = '';
    applyFilters();
  });
  $('timeline').addEventListener('click', (e) => {
    const btn = e.target.closest('.related-task');
    if (!btn) return;
    const id = btn.dataset.taskId || '';
    $('keyword').value = id;
    applyFilters();
    $('taskList').scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
  $('taskList').addEventListener('click', (e) => {
    const btn = e.target.closest('button.chip[data-facet]');
    if (!btn) return;
    e.preventDefault();
    const { facet, value } = btn.dataset;
    if (!facet) return;
    const sel = $(FACET_IDS[facet]);
    if (!sel) return;
    if (facet === 'skill_type' && !Array.from(sel.options).some((o) => o.value === value)) {
      const opt = document.createElement('option');
      opt.value = value;
      opt.textContent = value;
      sel.appendChild(opt);
    }
    sel.value = sel.value === value ? '' : value;
    applyFilters();
  });
}

(async function init() {
  setLoading();
  try {
    await loadData();
    populateFacetOptions();
    bindEvents();
    applyFilters();
  } catch (err) {
    showError(err);
  }
})();
