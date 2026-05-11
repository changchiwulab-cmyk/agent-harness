const state = { tasks: [], logs: [], decisions: [], errors: [] };

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
  state.errors = payload.errors || [];
  return payload;
}

// ---- Error Dashboard helpers ----

async function loadChartJs() {
  try {
    // Return the full module namespace so render functions can read both
    // `Chart` (the class) and `registerables` (the controllers/elements/scales array).
    // Collapsing to mod.default would lose `registerables`, breaking pie/bar registration.
    return await import('https://cdn.jsdelivr.net/npm/chart.js@4.4.4/+esm');
  } catch (_e) {
    return null;
  }
}

function unifyErrors(payload) {
  const unified = [];

  // Kind: error — from logs/errors/*.md
  for (const e of (payload.errors || [])) {
    unified.push({
      kind: 'error',
      date: e.date || '',
      title: e.error_summary || e.error_id || '(unknown)',
      detail: JSON.stringify(e, null, 2),
      source_path: e.path || '',
      taxonomy: e.taxonomy_codes || [],
      error_type: e.error_type || '',
      failed_gates: [],
    });
  }

  // Kind: gate — from logs with has_gate_failure
  for (const l of (payload.logs || [])) {
    if (l.has_gate_failure) {
      unified.push({
        kind: 'gate',
        date: l.started_at ? String(l.started_at).slice(0, 10) : '',
        title: `Gate 失敗: ${(l.failed_gates || []).join(', ')} (${escapeHtml(l.run_id || 'unknown')})`,
        detail: JSON.stringify(l, null, 2),
        source_path: l.path || '',
        taxonomy: [],
        error_type: '',
        failed_gates: l.failed_gates || [],
      });
    }
  }

  // Kind: schema — from tasks with schema_issues
  for (const t of (payload.tasks || [])) {
    if ((t.schema_issues || []).length > 0) {
      unified.push({
        kind: 'schema',
        date: t.date || '',
        title: `Schema 缺漏: ${(t.schema_issues || []).join(', ')} (${escapeHtml(t.task_id || 'unknown')})`,
        detail: JSON.stringify(t, null, 2),
        source_path: t.path || '',
        taxonomy: [],
        error_type: '',
        failed_gates: [],
        schema_issues: t.schema_issues || [],
      });
    }
  }

  return unified;
}

function renderErrorKpis(unified) {
  const totalErrors = unified.filter((u) => u.kind === 'error').length;
  const totalGate = unified.filter((u) => u.kind === 'gate').length;
  const totalFailed = state.tasks.filter((t) => t.status === 'failed' || t.status === 'blocked').length;
  const totalSchema = unified.filter((u) => u.kind === 'schema').length;

  const kpiMap = {
    kpiErrors: totalErrors,
    kpiGateFails: totalGate,
    kpiFailedTasks: totalFailed,
    kpiSchemaIssues: totalSchema,
  };

  for (const [id, value] of Object.entries(kpiMap)) {
    const el = $(id);
    if (el) {
      el.textContent = String(value);
    }
  }

  // Apply has-issue modifier
  for (const [kpi, value] of [
    ['errors', totalErrors],
    ['gate-fails', totalGate],
    ['failed-tasks', totalFailed],
    ['schema-issues', totalSchema],
  ]) {
    const card = document.querySelector(`[data-kpi="${kpi}"]`);
    if (card) {
      if (value > 0) {
        card.classList.add('has-issue');
      } else {
        card.classList.remove('has-issue');
      }
    }
  }
}

function renderChartFallback(unified) {
  // Replace taxonomy canvas
  const txBox = document.getElementById('taxonomyChart');
  if (txBox && txBox.parentNode) {
    const taxCounts = {};
    for (const u of unified) {
      for (const code of (u.taxonomy || [])) {
        taxCounts[code] = (taxCounts[code] || 0) + 1;
      }
    }
    const taxItems = Object.entries(taxCounts).map(([k, v]) => `<li>${escapeHtml(k)}: ${escapeHtml(v)}</li>`).join('');
    txBox.parentNode.innerHTML = `<p class="chart-fallback">未能載入 Chart.js（離線環境）。改顯示文字摘要：</p><ul>${taxItems || '<li>無分類資料</li>'}</ul>`;
  }

  // Replace timeline canvas
  const tlBox = document.getElementById('timelineChart');
  if (tlBox && tlBox.parentNode) {
    const monthCounts = {};
    for (const u of unified) {
      const month = (u.date || '').slice(0, 7);
      if (month) {
        monthCounts[month] = (monthCounts[month] || 0) + 1;
      }
    }
    const tlItems = Object.entries(monthCounts).sort().map(([k, v]) => `<li>${escapeHtml(k)}: ${escapeHtml(v)} 件</li>`).join('');
    tlBox.parentNode.innerHTML = `<p class="chart-fallback">未能載入 Chart.js（離線環境）。改顯示文字摘要：</p><ul>${tlItems || '<li>無時間軸資料</li>'}</ul>`;
  }
}

function renderTaxonomyChart(ChartModule, unified) {
  const canvas = document.getElementById('taxonomyChart');
  if (!canvas) return;
  const taxCounts = {};
  for (const u of unified) {
    for (const code of (u.taxonomy || [])) {
      taxCounts[code] = (taxCounts[code] || 0) + 1;
    }
  }
  const labels = Object.keys(taxCounts);
  const data = Object.values(taxCounts);
  if (labels.length === 0) {
    canvas.parentNode.innerHTML = '<p class="chart-fallback">無 taxonomy 資料</p>';
    return;
  }
  const Chart = ChartModule.Chart || ChartModule.default;
  if (!Chart) {
    canvas.parentNode.innerHTML = '<p class="chart-fallback">Chart.js 模組結構非預期</p>';
    return;
  }
  Chart.register(...(ChartModule.registerables || []));
  new Chart(canvas, {
    type: 'pie',
    data: {
      labels,
      datasets: [{ data, backgroundColor: ['#3b82f6', '#ef4444', '#f59e0b', '#10b981', '#8b5cf6'] }],
    },
    options: { responsive: true, plugins: { legend: { position: 'bottom' } } },
  });
}

function renderTimelineChart(ChartModule, unified) {
  const canvas = document.getElementById('timelineChart');
  if (!canvas) return;
  const monthCounts = {};
  for (const u of unified) {
    const month = (u.date || '').slice(0, 7);
    if (month) {
      monthCounts[month] = (monthCounts[month] || 0) + 1;
    }
  }
  const sortedMonths = Object.keys(monthCounts).sort();
  if (sortedMonths.length === 0) {
    canvas.parentNode.innerHTML = '<p class="chart-fallback">無時間軸資料</p>';
    return;
  }
  const Chart = ChartModule.Chart || ChartModule.default;
  if (!Chart) {
    canvas.parentNode.innerHTML = '<p class="chart-fallback">Chart.js 模組結構非預期</p>';
    return;
  }
  Chart.register(...(ChartModule.registerables || []));
  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: sortedMonths,
      datasets: [{ label: '錯誤/問題數', data: sortedMonths.map((m) => monthCounts[m]), backgroundColor: '#3b82f6' }],
    },
    options: { responsive: true, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } },
  });
}

function renderErrorList(unified) {
  const container = $('errorList');
  if (!container) return;
  if (unified.length === 0) {
    container.innerHTML = '<small>無錯誤紀錄</small>';
    return;
  }
  container.innerHTML = unified
    .map((u) => {
      const kindLabel = u.kind === 'error' ? '錯誤' : u.kind === 'gate' ? 'Gate' : 'Schema';
      const pathLink = u.source_path
        ? `<a href="vscode://file/${escapeHtml(u.source_path)}" title="Open in editor">${escapeHtml(u.source_path)}</a>`
        : '';
      return `<article class="item">
        <details>
          <summary>[${escapeHtml(kindLabel)}] ${escapeHtml(u.date || 'N/A')} — ${escapeHtml(u.title)}</summary>
          <div class="error-detail">
            ${pathLink ? `<div class="error-path">${pathLink}</div>` : ''}
            <pre>${escapeHtml(u.detail)}</pre>
          </div>
        </details>
      </article>`;
    })
    .join('');
}

function bindErrorControls(unified) {
  const typeFilter = $('errorTypeFilter');
  const gateFilter = $('gateFilter');
  const sortEl = $('errorSort');

  // Populate type filter options
  if (typeFilter) {
    const types = [...new Set(unified.filter((u) => u.error_type).map((u) => u.error_type))].sort();
    for (const t of types) {
      const opt = document.createElement('option');
      opt.value = escapeHtml(t);
      opt.textContent = t;
      typeFilter.appendChild(opt);
    }
  }

  // Populate gate filter options
  if (gateFilter) {
    const gates = [...new Set(unified.flatMap((u) => u.failed_gates || []))].sort();
    for (const g of gates) {
      const opt = document.createElement('option');
      opt.value = escapeHtml(g);
      opt.textContent = g;
      gateFilter.appendChild(opt);
    }
  }

  function applyErrorFilters() {
    const typeVal = typeFilter ? typeFilter.value : '';
    const gateVal = gateFilter ? gateFilter.value : '';
    const sortVal = sortEl ? sortEl.value : 'date_desc';

    let filtered = unified.slice();
    if (typeVal) {
      filtered = filtered.filter((u) => u.error_type === typeVal);
    }
    if (gateVal) {
      filtered = filtered.filter((u) => (u.failed_gates || []).includes(gateVal));
    }
    filtered.sort((a, b) => {
      const cmp = a.date.localeCompare(b.date);
      return sortVal === 'date_asc' ? cmp : -cmp;
    });
    renderErrorList(filtered);
  }

  if (typeFilter) typeFilter.addEventListener('change', applyErrorFilters);
  if (gateFilter) gateFilter.addEventListener('change', applyErrorFilters);
  if (sortEl) sortEl.addEventListener('change', applyErrorFilters);

  // Apply default state on first load so the initial render honors the
  // default `date_desc` sort (and any preselected filter values), instead
  // of showing the raw unsorted `unified` order.
  applyErrorFilters();
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
    const blob = `${t.task_id || ''} ${t.title || ''} ${t.status || ''} ${t.skill_type || ''}`.toLowerCase();
    return (!keyword || blob.includes(keyword)) && inDateRange(t.date, from, to);
  });

  const decisions = state.decisions.filter((d) => {
    const blob = `${d.decision_id || ''} ${d.decision || ''} ${d.reasoning || ''}`.toLowerCase();
    return (!keyword || blob.includes(keyword)) && inDateRange(d._date, from, to);
  });

  render(tasks, decisions);
}

function renderSummary(filteredTasks, filteredDecisions) {
  const done = filteredTasks.filter((x) => x.status === 'done').length;
  const failed = filteredTasks.filter((x) => x.status === 'failed').length;
  const cards = [
    ['Tasks', filteredTasks.length],
    ['Done', done],
    ['Failed', failed],
    ['Logs', state.logs.length],
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

function renderLogs() {
  $('logBoard').innerHTML = state.logs
    .map((l) => `
      <article class="item">
        <strong>${escapeHtml(l.run_id || '')}</strong><br />
        task: ${escapeHtml(l.task_id || 'N/A')}<br />
        <small>${escapeHtml(l.status || 'unknown')} · ${escapeHtml(l.ended_at || l.started_at || 'N/A')}</small>
      </article>`)
    .join('') || '<small>找不到 log 資料</small>';
}

function render(tasks, decisions) {
  renderSummary(tasks, decisions);
  renderTasks(tasks);
  renderTimeline(decisions);
  renderLogs();
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
    const payload = await loadData();
    bindEvents();
    applyFilters();

    // Error dashboard
    const ChartModule = await loadChartJs();
    const unified = unifyErrors(payload);
    renderErrorKpis(unified);
    if (ChartModule) {
      renderTaxonomyChart(ChartModule, unified);
      renderTimelineChart(ChartModule, unified);
    } else {
      renderChartFallback(unified);
    }
    // bindErrorControls runs applyErrorFilters() once internally to apply
    // default sort/filter state, which calls renderErrorList. No need to
    // pre-render here.
    bindErrorControls(unified);
  } catch (err) {
    showError(err);
  }
})();
