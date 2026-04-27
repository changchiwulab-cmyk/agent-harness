import { TASK_FILES, LOG_FILES, DECISION_FILES } from './manifest.js';

const state = { tasks: [], logs: [], decisions: [] };

const $ = (id) => document.getElementById(id);

function pick(text, key) {
  const m = text.match(new RegExp(`^${key}:\\s*(.*)$`, 'm'));
  return m ? m[1].replace(/^"|"$/g, '').trim() : '';
}

function parseTask(path, text) {
  return {
    path,
    task_id: pick(text, 'task_id') || path.split('/').pop().replace('.yaml', ''),
    status: pick(text, 'status') || 'unknown',
    date: pick(text, 'date') || path.match(/(\\d{4}-\\d{2}-\\d{2})/)?.[1] || '',
    title: pick(text, 'title') || pick(text, 'goal') || '(no title)',
    skill_type: pick(text, 'skill_type') || ''
  };
}

function parseLog(path, text) {
  return {
    path,
    run_id: pick(text, 'run_id') || path.split('/').pop().replace('.yaml', ''),
    status: pick(text, 'status') || 'unknown',
    task_id: pick(text, 'task_id') || '',
    completion_time: pick(text, 'completion_time') || ''
  };
}

function parseDecision(path, text) {
  const file = path.split('/').pop();
  const date = `${file.slice(0,4)}-${file.slice(4,6)}-${file.slice(6,8)}`;
  return {
    path,
    decision_id: pick(text, 'decision_id') || file.replace('.yaml',''),
    date,
    summary: pick(text, 'decision_summary') || pick(text, 'title') || file,
    rationale: pick(text, 'rationale') || ''
  };
}

async function loadOne(path, parser) {
  try {
    const text = await (await fetch(path)).text();
    return parser(path, text);
  } catch {
    return null;
  }
}

async function loadData() {
  const tasks = await Promise.all(TASK_FILES.map((p) => loadOne(p, parseTask)));
  const logs = await Promise.all(LOG_FILES.map((p) => loadOne(p, parseLog)));
  const decisions = await Promise.all(DECISION_FILES.map((p) => loadOne(p, parseDecision)));
  state.tasks = tasks.filter(Boolean);
  state.logs = logs.filter(Boolean);
  state.decisions = decisions.filter(Boolean).sort((a, b) => a.date.localeCompare(b.date));
}

function inDateRange(value, from, to) {
  if (!value) return true;
  if (from && value < from) return false;
  if (to && value > to) return false;
  return true;
}

function applyFilters() {
  const keyword = $('keyword').value.toLowerCase().trim();
  const from = $('dateFrom').value;
  const to = $('dateTo').value;

  const tasks = state.tasks.filter((t) => {
    const blob = `${t.task_id} ${t.title} ${t.status} ${t.skill_type}`.toLowerCase();
    return (!keyword || blob.includes(keyword)) && inDateRange(t.date, from, to);
  });

  const decisions = state.decisions.filter((d) => {
    const blob = `${d.decision_id} ${d.summary}`.toLowerCase();
    return (!keyword || blob.includes(keyword)) && inDateRange(d.date, from, to);
  });

  render(tasks, decisions);
}

function renderSummary(filteredTasks, filteredDecisions) {
  const done = filteredTasks.filter((x) => x.status === 'done').length;
  const failed = filteredTasks.filter((x) => x.status === 'failed').length;
  const html = [
    ['Tasks', filteredTasks.length],
    ['Done', done],
    ['Failed', failed],
    ['Logs', state.logs.length],
    ['Decisions', filteredDecisions.length]
  ].map(([label, value]) => `<article class="card"><div class="label">${label}</div><div class="value">${value}</div></article>`).join('');
  $('summaryCards').innerHTML = html;
}

function renderTasks(tasks) {
  $('taskList').innerHTML = tasks
    .sort((a, b) => b.date.localeCompare(a.date))
    .map((t) => `
      <article class="item">
        <strong>${t.task_id}</strong><br />
        ${t.title}<br />
        <small>${t.date || 'N/A'} · ${t.status} · ${t.skill_type || 'N/A'}</small>
      </article>`)
    .join('') || '<small>無符合條件資料</small>';
}

function renderTimeline(decisions) {
  $('timeline').innerHTML = decisions
    .map((d) => `
      <article class="item timeline-item">
        <details>
          <summary>${d.date}｜${d.decision_id}</summary>
          <div>${d.summary}</div>
          <small>${d.rationale || '無補充說明'}</small>
        </details>
      </article>`)
    .join('') || '<small>無符合條件資料</small>';
}

function renderLogs() {
  $('logBoard').innerHTML = state.logs
    .map((l) => `
      <article class="item">
        <strong>${l.run_id}</strong><br />
        task: ${l.task_id || 'N/A'}<br />
        <small>${l.status} · ${l.completion_time || 'N/A'}</small>
      </article>`)
    .join('') || '<small>找不到 log 資料</small>';
}

function render(tasks, decisions) {
  renderSummary(tasks, decisions);
  renderTasks(tasks);
  renderTimeline(decisions);
  renderLogs();
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
  await loadData();
  bindEvents();
  applyFilters();
})();
