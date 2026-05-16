const state = { tasks: [], logs: [], decisions: [] };

const $ = (id) => document.getElementById(id);

function escapeHtml(value) {
  if (value === null || value === undefined) return '';
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function decisionDate(item) {
  if (item.date) return item.date;
  const file = (item.path || '').split('/').pop() || '';
  if (/^\d{8}/.test(file)) {
    return `${file.slice(0, 4)}-${file.slice(4, 6)}-${file.slice(6, 8)}`;
  }
  return '';
}

async function loadData() {
  const res = await fetch('./data.json');
  if (!res.ok) {
    throw new Error(`Failed to load data.json: HTTP ${res.status}`);
  }
  const payload = await res.json();
  state.tasks = (payload.tasks || []).map((t) => ({ ...t, title: t.goal || t.task_id || '(no title)' }));
  state.logs = payload.logs || [];
  state.decisions = (payload.decisions || [])
    .map((d) => ({ ...d, _date: decisionDate(d) }))
    .sort((a, b) => a._date.localeCompare(b._date));
}

function inDateRange(value, from, to) {
  if (!value) return true;
  if (from && value < from) return false;
  if (to && value > to) return false;
  return true;
}

function logDate(item) {
  return String(item.ended_at || item.started_at || '').slice(0, 10);
}

function applyFilters() {
  const keyword = $('keyword').value.toLowerCase().trim();
  const from = $('dateFrom').value;
  const to = $('dateTo').value;

  const tasks = state.tasks.filter((t) => {
    const blob = `${t.task_id || ''} ${t.title || ''} ${t.status || ''} ${t.skill_type || ''}`.toLowerCase();
    return (!keyword || blob.includes(keyword)) && inDateRange(t.date, from, to);
  });

  const decisions = state.decisions.filter((d) => {
    const blob = `${d.decision_id || ''} ${d.decision || ''} ${d.reasoning || ''}`.toLowerCase();
    return (!keyword || blob.includes(keyword)) && inDateRange(d._date, from, to);
  });

  const logs = state.logs.filter((l) => {
    const blob = `${l.run_id || ''} ${l.task_id || ''} ${l.status || ''} ${l.skill_type || ''}`.toLowerCase();
    return (!keyword || blob.includes(keyword)) && inDateRange(logDate(l), from, to);
  });

  render(tasks, decisions, logs);
}

function renderSummary(filteredTasks, filteredDecisions, filteredLogs) {
  const done = filteredTasks.filter((x) => x.status === 'done').length;
  const failed = filteredTasks.filter((x) => x.status === 'failed').length;
  const cards = [
    ['Tasks', filteredTasks.length],
    ['Done', done],
    ['Failed', failed],
    ['Logs', filteredLogs.length],
    ['Decisions', filteredDecisions.length],
  ];
  $('summaryCards').innerHTML = cards
    .map(([label, value]) => `<article class="card"><div class="label">${escapeHtml(label)}</div><div class="value">${escapeHtml(value)}</div></article>`)
    .join('');
}

function renderTasks(tasks) {
  $('taskList').innerHTML = tasks
    .slice()
    .sort((a, b) => (b.date || '').localeCompare(a.date || ''))
    .map((t) => `
      <article class="item">
        <strong>${escapeHtml(t.task_id || '')}</strong><br />
        ${escapeHtml(t.title || '')}<br />
        <small>${escapeHtml(t.date || 'N/A')} · ${escapeHtml(t.status || 'unknown')} · ${escapeHtml(t.skill_type || 'N/A')}</small>
      </article>`)
    .join('') || '<small>無符合條件資料</small>';
}

function renderTimeline(decisions) {
  $('timeline').innerHTML = decisions
    .map((d) => `
      <article class="item timeline-item">
        <details>
          <summary>${escapeHtml(d._date || '')}｜${escapeHtml(d.decision_id || '')}</summary>
          <div>${escapeHtml(d.decision || '(no decision recorded)')}</div>
          <small>${escapeHtml(d.reasoning || '無補充說明')}</small>
        </details>
      </article>`)
    .join('') || '<small>無符合條件資料</small>';
}

const GATE_KEYS = ['schema_check', 'rule_check', 'completion_check', 'risk_check'];

function renderGates(gate) {
  if (!gate || typeof gate !== 'object') return '';
  const chips = GATE_KEYS
    .filter((k) => k in gate)
    .map((k) => {
      const val = String(gate[k]);
      const cls = val === 'pass' ? 'gate-pass' : 'gate-fail';
      return `<span class="gate ${cls}">${escapeHtml(k.replace('_check', ''))}: ${escapeHtml(val)}</span>`;
    })
    .join(' ');
  return chips ? `<div class="gates">${chips}</div>` : '';
}

function renderLogs(logs) {
  $('logBoard').innerHTML = logs
    .map((l) => `
      <article class="item">
        <strong>${escapeHtml(l.run_id || '')}</strong><br />
        task: ${escapeHtml(l.task_id || 'N/A')}<br />
        <small>${escapeHtml(l.status || 'unknown')} · ${escapeHtml(l.ended_at || l.started_at || 'N/A')}</small>
        ${renderGates(l.gate_results)}
      </article>`)
    .join('') || '<small>找不到 log 資料</small>';
}

function render(tasks, decisions, logs) {
  renderSummary(tasks, decisions, logs);
  renderTasks(tasks);
  renderTimeline(decisions);
  renderLogs(logs);
}

function showError(err) {
  const msg = err && err.message ? err.message : String(err);
  $('summaryCards').innerHTML = `<article class="card"><div class="label">Error</div><div class="value">⚠</div><small>${escapeHtml(msg)}</small></article>`;
}

function bindEvents() {
  ['keyword', 'dateFrom', 'dateTo'].forEach((id) => $(id).addEventListener('input', applyFilters));
  $('resetFilters').addEventListener('click', () => {
    $('keyword').value = '';
    $('dateFrom').value = '';
    $('dateTo').value = '';
    applyFilters();
  });
}

(async function init() {
  try {
    await loadData();
    bindEvents();
    applyFilters();
  } catch (err) {
    showError(err);
  }
})();
