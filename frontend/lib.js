// Pure helpers for the dashboard. No DOM access here so they can be unit tested.

export function escapeHtml(value) {
  if (value === null || value === undefined) return '';
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

export function decisionDate(item) {
  if (!item) return '';
  if (item.date) return item.date;
  const file = (item.path || '').split('/').pop() || '';
  if (/^\d{8}/.test(file)) {
    return `${file.slice(0, 4)}-${file.slice(4, 6)}-${file.slice(6, 8)}`;
  }
  return '';
}

export function inDateRange(value, from, to) {
  if (!value) return true;
  if (from && value < from) return false;
  if (to && value > to) return false;
  return true;
}

export const TASK_FACET_KEYS = ['status', 'skill_type', 'risk_level', 'approval_needed'];

function matchFacet(task, key, want) {
  if (want === '' || want === null || want === undefined) return true;
  const have = task[key];
  if (key === 'approval_needed') {
    const wantBool = want === 'true';
    return Boolean(have) === wantBool;
  }
  return String(have ?? '') === String(want);
}

export function filterTasks(tasks, { keyword = '', from = '', to = '', facets = {} } = {}) {
  const kw = (keyword || '').toLowerCase().trim();
  return tasks.filter((t) => {
    const blob = `${t.task_id || ''} ${t.title || t.goal || ''} ${t.status || ''} ${t.skill_type || ''}`.toLowerCase();
    if (kw && !blob.includes(kw)) return false;
    if (!inDateRange(t.date, from, to)) return false;
    return TASK_FACET_KEYS.every((k) => matchFacet(t, k, facets[k]));
  });
}

export function filterDecisions(decisions, { keyword = '', from = '', to = '' } = {}) {
  const kw = (keyword || '').toLowerCase().trim();
  return decisions.filter((d) => {
    const blob = `${d.decision_id || ''} ${d.decision || ''} ${d.reasoning || ''} ${d.related_task || ''}`.toLowerCase();
    if (kw && !blob.includes(kw)) return false;
    return inDateRange(d._date, from, to);
  });
}

export function aggregateTasks(tasks) {
  const byStatus = {};
  const byRisk = {};
  const bySkill = {};
  for (const t of tasks) {
    byStatus[t.status || 'unknown'] = (byStatus[t.status || 'unknown'] || 0) + 1;
    byRisk[t.risk_level || 'unknown'] = (byRisk[t.risk_level || 'unknown'] || 0) + 1;
    bySkill[t.skill_type || 'unknown'] = (bySkill[t.skill_type || 'unknown'] || 0) + 1;
  }
  return { byStatus, byRisk, bySkill, total: tasks.length };
}

export const GATE_KEYS = ['schema_check', 'rule_check', 'completion_check', 'risk_check'];

export function gateState(value) {
  if (value === undefined || value === null || value === '') return 'na';
  const v = String(value).toLowerCase();
  if (v === 'pass' || v === 'passed' || v === 'ok') return 'pass';
  if (v === 'fail' || v === 'failed' || v === 'error') return 'fail';
  return 'na';
}

export function uniqueValues(items, key) {
  const seen = new Set();
  for (const it of items) {
    const v = it && it[key];
    if (v !== undefined && v !== null && v !== '') seen.add(String(v));
  }
  return Array.from(seen).sort();
}
