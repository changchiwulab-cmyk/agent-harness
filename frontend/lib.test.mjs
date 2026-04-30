import { test } from 'node:test';
import assert from 'node:assert/strict';

import {
  escapeHtml,
  decisionDate,
  inDateRange,
  filterTasks,
  filterDecisions,
  aggregateTasks,
  gateState,
  uniqueValues,
} from './lib.js';

test('escapeHtml escapes the five XSS-relevant characters', () => {
  assert.equal(escapeHtml(`<a href="x" onclick='y'>&</a>`), '&lt;a href=&quot;x&quot; onclick=&#039;y&#039;&gt;&amp;&lt;/a&gt;');
  assert.equal(escapeHtml(null), '');
  assert.equal(escapeHtml(undefined), '');
  assert.equal(escapeHtml(0), '0');
});

test('decisionDate prefers explicit date, falls back to filename prefix', () => {
  assert.equal(decisionDate({ date: '2026-04-30' }), '2026-04-30');
  assert.equal(decisionDate({ path: 'memory/x/decisions/20260403-D001_foo.yaml' }), '2026-04-03');
  assert.equal(decisionDate({ path: 'no-prefix.yaml' }), '');
  assert.equal(decisionDate(null), '');
  assert.equal(decisionDate({}), '');
});

test('inDateRange handles open-ended bounds', () => {
  assert.equal(inDateRange('2026-04-30', '', ''), true);
  assert.equal(inDateRange('2026-04-30', '2026-04-01', '2026-05-01'), true);
  assert.equal(inDateRange('2026-04-30', '2026-05-01', ''), false);
  assert.equal(inDateRange('2026-04-30', '', '2026-04-01'), false);
  assert.equal(inDateRange('', '2026-04-01', '2026-05-01'), true);
});

test('filterTasks combines keyword, date and facets via AND', () => {
  const tasks = [
    { task_id: 'A1', goal: 'alpha', date: '2026-04-01', status: 'done', skill_type: 'ops', risk_level: 'low', approval_needed: false },
    { task_id: 'A2', goal: 'beta', date: '2026-04-15', status: 'review', skill_type: 'ops', risk_level: 'medium', approval_needed: true },
    { task_id: 'A3', goal: 'gamma', date: '2026-04-20', status: 'done', skill_type: 'review', risk_level: 'low', approval_needed: false },
  ];
  assert.equal(filterTasks(tasks, { keyword: 'beta' }).length, 1);
  assert.equal(filterTasks(tasks, { facets: { status: 'done' } }).length, 2);
  assert.equal(filterTasks(tasks, { facets: { skill_type: 'ops', risk_level: 'medium' } }).length, 1);
  assert.equal(filterTasks(tasks, { facets: { approval_needed: 'true' } }).length, 1);
  assert.equal(filterTasks(tasks, { facets: { approval_needed: 'false' } }).length, 2);
  assert.equal(filterTasks(tasks, { from: '2026-04-10', to: '2026-04-30' }).length, 2);
  assert.equal(filterTasks(tasks, { keyword: 'a', facets: { status: 'review' } }).length, 1);
});

test('filterDecisions matches keyword across decision_id, decision, reasoning, related_task', () => {
  const decisions = [
    { decision_id: 'D001', decision: 'pick A', reasoning: 'because', related_task: 'T1', _date: '2026-04-01' },
    { decision_id: 'D002', decision: 'pick B', reasoning: 'rationale', related_task: '', _date: '2026-04-20' },
  ];
  assert.equal(filterDecisions(decisions, { keyword: 'T1' }).length, 1);
  assert.equal(filterDecisions(decisions, { keyword: 'rationale' }).length, 1);
  assert.equal(filterDecisions(decisions, { from: '2026-04-10' }).length, 1);
});

test('aggregateTasks counts by status, risk, skill', () => {
  const tasks = [
    { status: 'done', risk_level: 'low', skill_type: 'ops' },
    { status: 'done', risk_level: 'medium', skill_type: 'ops' },
    { status: 'review', risk_level: 'medium', skill_type: 'review' },
    { status: 'failed', skill_type: 'ops' },
  ];
  const agg = aggregateTasks(tasks);
  assert.equal(agg.total, 4);
  assert.equal(agg.byStatus.done, 2);
  assert.equal(agg.byStatus.failed, 1);
  assert.equal(agg.byRisk.medium, 2);
  assert.equal(agg.byRisk.unknown, 1);
  assert.equal(agg.bySkill.ops, 3);
});

test('gateState normalises pass/fail/na variants', () => {
  assert.equal(gateState('pass'), 'pass');
  assert.equal(gateState('PASSED'), 'pass');
  assert.equal(gateState('fail'), 'fail');
  assert.equal(gateState('error'), 'fail');
  assert.equal(gateState(''), 'na');
  assert.equal(gateState(undefined), 'na');
  assert.equal(gateState('weird'), 'na');
});

test('uniqueValues returns sorted unique non-empty values', () => {
  const items = [
    { skill_type: 'ops' },
    { skill_type: 'review' },
    { skill_type: 'ops' },
    { skill_type: '' },
    { skill_type: null },
  ];
  assert.deepEqual(uniqueValues(items, 'skill_type'), ['ops', 'review']);
  assert.deepEqual(uniqueValues([], 'skill_type'), []);
});
