// Workflow 視覺化：人看圖、agent 讀結構。
// 視覺圖完全由 #workflow-spec（單一真實來源）渲染，與 JSON 永不脫鉤。

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

function readSpec() {
  const node = $('workflow-spec');
  if (!node) throw new Error('找不到 #workflow-spec（單一真實來源遺失）');
  return JSON.parse(node.textContent);
}

function section(id, title, hint, bodyHtml) {
  return `
    <section class="wf-section" id="sec-${escapeHtml(id)}">
      <h2>${escapeHtml(title)}${hint ? ` <small>${escapeHtml(hint)}</small>` : ''}</h2>
      ${bodyHtml}
    </section>`;
}

function list(items) {
  return `<ul class="wf-ul">${(items || []).map((x) => `<li>${escapeHtml(x)}</li>`).join('')}</ul>`;
}

function chips(items, cls) {
  return `<div class="chips">${(items || [])
    .map((x) => `<span class="chip${cls ? ` ${cls}` : ''}">${escapeHtml(x)}</span>`)
    .join('')}</div>`;
}

function renderHeader(spec) {
  $('wfTitle').textContent = spec.title || 'Agent Harness 工作流程';
  $('wfSubtitle').textContent = spec.subtitle || '';
  const bits = [];
  if (spec.principle) bits.push(`原則：${spec.principle}`);
  if (spec.source) bits.push(`來源：${spec.source}`);
  $('wfSource').textContent = bits.join('｜');
}

function renderHardRules(spec) {
  const body = `<div class="rule-list">${(spec.hard_rules || [])
    .map((r) => `
      <article class="rule-banner">
        <span class="rule-no">${escapeHtml(r.id)}</span>
        <div>
          <strong>${escapeHtml(r.rule)}</strong>
          <div><small>${escapeHtml(r.detail)}</small></div>
        </div>
      </article>`)
    .join('')}</div>`;
  return section('rules', '三條硬規則', '不可違反的護欄', body);
}

function renderIntake(spec) {
  const intake = spec.intake || {};
  const fp = intake.fast_path || {};
  const im = intake.intake_mode || {};
  const body = `
    ${intake.note ? `<p class="wf-note"><small>${escapeHtml(intake.note)}</small></p>` : ''}
    <div class="intake-grid">
      <article class="intake-col fast">
        <h3>${escapeHtml(fp.label || 'Fast-path')}</h3>
        <div><small>三條件同時滿足：</small></div>
        ${chips(fp.conditions)}
        <ol class="mini-flow">${(fp.flow || []).map((s) => `<li>${escapeHtml(s)}</li>`).join('')}</ol>
      </article>
      <article class="intake-col fallback">
        <h3>${escapeHtml(im.label || 'Intake 模式')}</h3>
        <div><small>${escapeHtml(im.trigger || '')}</small></div>
        <div><small>只允許：</small></div>
        ${chips(im.allowed)}
        <div><small>不允許：</small></div>
        ${chips(im.not_allowed, 'no')}
        <ol class="mini-flow">${(im.flow || []).map((s) => `<li>${escapeHtml(s)}</li>`).join('')}</ol>
      </article>
    </div>`;
  return section('intake', 'Intake 分流', '需求 → Task Card 的入口', body);
}

function renderFlow(spec) {
  const body = `<div class="flow">${(spec.execution_flow || [])
    .map((s) => `
      <article class="flow-step${s.ref === 'gates' ? ' is-gate' : ''}">
        <span class="step-no">${escapeHtml(s.step)}</span>
        <div class="step-label">${escapeHtml(s.label)}</div>
        ${s.io ? `<div class="step-io">${escapeHtml(s.io)}</div>` : ''}
      </article>`)
    .join('')}</div>`;
  return section('flow', '9 步執行流程', '第 6 步展開為下方四層 Gate', body);
}

function renderGates(spec) {
  const body = `<div class="gate-list">${(spec.gates || [])
    .map((g) => `
      <article class="gate">
        <div class="gate-head">
          <span class="layer-no">${escapeHtml(g.layer)}</span>
          <strong>${escapeHtml(g.label)}</strong>
          <span class="gate-name">${escapeHtml(g.name)}</span>
        </div>
        <div class="gate-desc">${escapeHtml(g.description)}</div>
        <div class="gate-row"><span class="tag fail">fail ✗</span>${escapeHtml(g.on_fail)}</div>
        <div class="gate-row"><span class="tag rollback">rollback ↺</span>${escapeHtml(g.rollback)}</div>
      </article>`)
    .join('')}</div>`;
  return section('gates', '四層 Gate 驗證', '依序執行，任一層 fail 即依 on_fail / rollback 處理', body);
}

function renderPermissions(spec) {
  const p = spec.permissions || {};
  const col = (cls, title, items) => `
    <article class="perm-col ${cls}">
      <h3><span class="dot ${cls}"></span>${escapeHtml(title)}</h3>
      ${chips(items, cls)}
    </article>`;
  const body = `
    <div class="perm-grid">
      ${col('allow', 'allow（直接執行）', p.allow)}
      ${col('ask', 'ask（需人工確認）', p.ask)}
      ${col('deny', 'deny（禁止）', p.deny)}
    </div>`;
  return section('permissions', '權限三級', 'allow / ask / deny', body);
}

function renderRiskLevels(spec) {
  const body = `<div class="risk-list">${(spec.risk_levels || [])
    .map((r) => {
      const auto = r.auto_execute
        ? '<span class="auto-yes">自動執行</span>'
        : '<span class="auto-no">需批准</span>';
      return `
      <div class="risk-row ${escapeHtml(r.level)}">
        <span class="lvl">${escapeHtml(r.level)}</span>
        <span class="meta">${auto}｜批准：${escapeHtml(r.approval)}｜${escapeHtml(r.desc)}</span>
      </div>`;
    })
    .join('')}</div>`;
  return section('risk', '風險等級', 'low → critical', body);
}

function renderApproval(spec) {
  const a = spec.approval || {};
  const body = `
    <div class="grid">
      <div>
        <h3>觸發批准</h3>
        ${list(a.triggers)}
      </div>
      <div>
        <h3>升級條件</h3>
        ${list(a.escalation)}
      </div>
    </div>`;
  return section('approval', '審核與升級', 'system/APPROVAL_POLICY.yaml + system/AGENT_CONTEXT.yaml', body);
}

function renderFailure(spec) {
  const rows = (spec.validation_failure_handling || [])
    .map((f) => `<tr><td>${escapeHtml(f.gate)}</td><td>${escapeHtml(f.action)}</td></tr>`)
    .join('');
  const body = `
    <table class="wf-table">
      <thead><tr><th>驗證失敗</th><th>處理</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
  return section('failure', '驗證失敗處理', '逐情境對照', body);
}

function renderRawSpec(spec) {
  const body = `
    <details>
      <summary>顯示原始 JSON（agent 可直接讀取的單一真實來源）</summary>
      <pre class="raw-json">${escapeHtml(JSON.stringify(spec, null, 2))}</pre>
    </details>`;
  return section('raw', '原始結構（JSON）', '人看上方的圖、agent 讀這份結構', body);
}

function showError(err) {
  const msg = err && err.message ? err.message : String(err);
  $('workflow').innerHTML = `<section class="wf-section"><div class="card"><div class="label">Error</div><div class="value">⚠</div><small>${escapeHtml(msg)}</small></div></section>`;
}

(function init() {
  try {
    const spec = readSpec();
    renderHeader(spec);
    $('workflow').innerHTML = [
      renderHardRules(spec),
      renderIntake(spec),
      renderFlow(spec),
      renderGates(spec),
      renderPermissions(spec),
      renderRiskLevels(spec),
      renderApproval(spec),
      renderFailure(spec),
      renderRawSpec(spec),
    ].join('');
  } catch (err) {
    showError(err);
  }
})();
