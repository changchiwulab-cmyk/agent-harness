const state = {
  tasks: [],
  logs: [],
  decisions: [],
  systemMeta: { gate_policy: null, approval_policy: null, failure_taxonomy: null },
  filterFailures: false,
};

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
  state.systemMeta = payload.system_meta || {};
}

function inDateRange(value, from, to) {
  if (!value) return true;
  if (from && value < from) return false;
  if (to && value > to) return false;
  return true;
}

function logHasFailure(log) {
  if (!log) return false;
  if (log.status && /^(failed|partial)$/.test(log.status)) return true;
  const gates = log.gate_results || {};
  return Object.values(gates).some((v) => v === 'fail');
}

function taskHasFailure(task) {
  if (!task) return false;
  if (task.status && /^(failed|partial)$/.test(task.status)) return true;
  // fallback: any related run with failure?
  return state.logs.some((l) => l.task_id === task.task_id && logHasFailure(l));
}

function applyFilters() {
  const keyword = $('keyword').value.toLowerCase().trim();
  const from = $('dateFrom').value;
  const to = $('dateTo').value;
  const onlyFailures = state.filterFailures;

  const tasks = state.tasks.filter((t) => {
    const blob = `${t.task_id || ''} ${t.title || ''} ${t.status || ''} ${t.skill_type || ''}`.toLowerCase();
    if (keyword && !blob.includes(keyword)) return false;
    if (!inDateRange(t.date, from, to)) return false;
    if (onlyFailures && !taskHasFailure(t)) return false;
    return true;
  });

  const decisions = state.decisions.filter((d) => {
    const blob = `${d.decision_id || ''} ${d.decision || ''} ${d.reasoning || ''}`.toLowerCase();
    return (!keyword || blob.includes(keyword)) && inDateRange(d._date, from, to);
  });

  const logs = state.logs.filter((l) => {
    if (onlyFailures && !logHasFailure(l)) return false;
    return true;
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

function renderLogs(logs) {
  $('logBoard').innerHTML = logs
    .map((l) => `
      <article class="item">
        <strong>${escapeHtml(l.run_id || '')}</strong><br />
        task: ${escapeHtml(l.task_id || 'N/A')}<br />
        <small>${escapeHtml(l.status || 'unknown')} · ${escapeHtml(l.ended_at || l.started_at || 'N/A')}</small>
      </article>`)
    .join('') || '<small>找不到 log 資料</small>';
}

// ---------- Phase 1 panels ----------

const GATE_LAYERS = [
  { key: 'schema_check', label: 'Schema' },
  { key: 'rule_check', label: 'Rule' },
  { key: 'completion_check', label: 'Completion' },
  { key: 'risk_check', label: 'Risk' },
];

function lampClass(value) {
  if (value === 'pass') return 'lamp lamp-pass';
  if (value === 'fail') return 'lamp lamp-fail';
  return 'lamp lamp-empty';
}

function lampLabel(layerLabel, value) {
  const status = value === 'pass' ? '通過' : value === 'fail' ? '失敗' : '未紀錄';
  return `${layerLabel} gate ${status}`;
}

function gateDescription(key) {
  const policy = state.systemMeta.gate_policy;
  if (!policy || !policy.gates || !policy.gates[key]) return '（GATE_POLICY 未載入）';
  const node = policy.gates[key];
  const checks = Array.isArray(node.checks) ? node.checks.map((c) => `• ${c}`).join('\n') : '';
  return `${node.description || ''}\n\n${checks}\n\non_fail: ${node.on_fail || ''}\nrollback: ${node.rollback || ''}`.trim();
}

function renderGateMatrix(logs) {
  if (!logs.length) {
    $('gateMatrix').innerHTML = '<small>無 run 紀錄</small>';
    return;
  }
  const rows = logs.map((log) => {
    const cells = GATE_LAYERS.map(({ key, label }) => {
      const value = (log.gate_results || {})[key] || '';
      const aria = lampLabel(label, value);
      const desc = escapeHtml(gateDescription(key));
      return `
        <td>
          <details class="lamp-cell">
            <summary>
              <span class="${lampClass(value)}" role="img" aria-label="${escapeHtml(aria)}"></span>
              <span class="lamp-text">${escapeHtml(label)}</span>
            </summary>
            <pre class="gate-desc">${desc}</pre>
          </details>
        </td>`;
    }).join('');
    return `
      <tr>
        <th scope="row">
          <strong>${escapeHtml(log.run_id || '')}</strong><br />
          <small>${escapeHtml(log.task_id || '')} · ${escapeHtml(log.status || '')}</small>
        </th>
        ${cells}
      </tr>`;
  }).join('');

  $('gateMatrix').innerHTML = `
    <table class="gate-matrix">
      <thead>
        <tr>
          <th scope="col">Run</th>
          ${GATE_LAYERS.map((l) => `<th scope="col">${escapeHtml(l.label)}</th>`).join('')}
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>`;
}

function renderApprovalTrail(logs) {
  const events = [];
  logs.forEach((log) => {
    (log.approvals || []).forEach((a) => {
      events.push({
        run_id: log.run_id || '',
        task_id: log.task_id || '',
        action: a.action || '',
        status: a.status || '',
        approved_by: a.approved_by || '',
        timestamp: a.timestamp || '',
      });
    });
  });
  events.sort((a, b) => (a.timestamp || '').localeCompare(b.timestamp || ''));

  if (!events.length) {
    $('approvalTrail').innerHTML = '<small>尚無 approval 紀錄</small>';
    return;
  }

  $('approvalTrail').innerHTML = events.map((e) => {
    const badgeClass = e.status === 'approved' ? 'badge badge-approved'
      : e.status === 'rejected' ? 'badge badge-rejected'
      : 'badge badge-pending';
    return `
      <article class="item approval-item">
        <div class="approval-row">
          <span class="${badgeClass}">${escapeHtml(e.status || 'pending')}</span>
          <strong>${escapeHtml(e.action)}</strong>
        </div>
        <small>${escapeHtml(e.timestamp || 'N/A')} · ${escapeHtml(e.approved_by || 'human')} · ${escapeHtml(e.run_id)} → ${escapeHtml(e.task_id)}</small>
      </article>`;
  }).join('');
}

function renderFailureMap(logs, tasks) {
  const taxonomy = state.systemMeta.failure_taxonomy && state.systemMeta.failure_taxonomy.categories;
  const groupOrder = ['spec', 'coordination', 'validation', 'security'];

  const gridHtml = !taxonomy ? '<small>FAILURE_TAXONOMY 未載入</small>' : groupOrder.map((groupKey) => {
    const items = taxonomy[groupKey] || [];
    const cells = items.map((item) => {
      const tooltip = `${item.name || ''}\n\n${item.description || ''}\n\n緩解：${item.mitigation || ''}`;
      return `
        <li class="failure-cell" title="${escapeHtml(tooltip)}">
          <strong>${escapeHtml(item.id || '')}</strong>
          <span>${escapeHtml(item.name || '')}</span>
        </li>`;
    }).join('');
    return `
      <section class="failure-group">
        <h4>${escapeHtml(groupKey)}</h4>
        <ul class="failure-grid">${cells}</ul>
      </section>`;
  }).join('');

  const errorItems = [];
  logs.forEach((l) => {
    if (l.error_summary) {
      errorItems.push({
        kind: 'log',
        id: l.run_id || '',
        task_id: l.task_id || '',
        status: l.status || '',
        summary: l.error_summary || '',
      });
    }
  });
  tasks.forEach((t) => {
    if (t.status && t.status !== 'done') {
      errorItems.push({
        kind: 'task',
        id: t.task_id || '',
        task_id: t.task_id || '',
        status: t.status,
        summary: t.title || '',
      });
    }
  });

  const errorListHtml = errorItems.length
    ? errorItems.map((e) => `
        <article class="item">
          <strong>${escapeHtml(e.id)}</strong>
          <span class="badge badge-${escapeHtml(e.status)}">${escapeHtml(e.status)}</span><br />
          <small>${escapeHtml(e.summary || '(no summary)')}</small>
        </article>`).join('')
    : '<small>無錯誤紀錄</small>';

  $('failureMap').innerHTML = `
    <div class="failure-layout">
      <div class="failure-grid-wrap">
        <p class="hint">滑鼠移到格子可看 mitigation；分類僅展示，不自動推論失敗類別。</p>
        ${gridHtml}
      </div>
      <aside class="failure-side">
        <h4>有錯誤摘要 / 非 done 任務</h4>
        ${errorListHtml}
      </aside>
    </div>`;
}

const HEX7 = /^[0-9a-f]{7,40}$/i;

function renderCheckpointChain(logs) {
  if (!logs.length) {
    $('checkpointChain').innerHTML = '<small>無 run 紀錄</small>';
    return;
  }
  const html = logs.map((log) => {
    const cps = (log.checkpoints || []);
    const items = cps.length ? cps.map((c, idx) => {
      const commit = c.commit || '';
      const stage = c.stage || '';
      const isHash = HEX7.test(commit);
      const commitHtml = isHash
        ? `<code class="commit-hash">${escapeHtml(commit)}</code>`
        : `<span class="commit-placeholder">${escapeHtml(commit || '(no commit)')}</span>`;
      const arrow = idx < cps.length - 1 ? '<span class="chain-arrow" aria-hidden="true">→</span>' : '';
      return `<li class="chain-step">${commitHtml}<small>${escapeHtml(stage)}</small>${arrow}</li>`;
    }).join('') : '<li><small>未紀錄 checkpoint</small></li>';
    return `
      <article class="item chain-run">
        <header><strong>${escapeHtml(log.run_id || '')}</strong> · ${escapeHtml(log.task_id || '')} · ${escapeHtml(log.status || '')}</header>
        <ol class="chain">${items}</ol>
      </article>`;
  }).join('');
  $('checkpointChain').innerHTML = html;
}

function render(tasks, decisions, logs) {
  renderSummary(tasks, decisions, logs);
  renderTasks(tasks);
  renderTimeline(decisions);
  renderLogs(logs);
  renderGateMatrix(logs);
  renderApprovalTrail(logs);
  renderFailureMap(logs, tasks);
  renderCheckpointChain(logs);
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
    state.filterFailures = false;
    $('filterFailures').setAttribute('aria-pressed', 'false');
    $('filterFailures').classList.remove('active');
    applyFilters();
  });
  $('filterFailures').addEventListener('click', () => {
    state.filterFailures = !state.filterFailures;
    $('filterFailures').setAttribute('aria-pressed', state.filterFailures ? 'true' : 'false');
    $('filterFailures').classList.toggle('active', state.filterFailures);
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
