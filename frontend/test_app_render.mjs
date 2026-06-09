// Dependency-free deep render tests for frontend/app.js.
// Executes app.js in a vm sandbox with a stubbed DOM + fetch, across multiple
// scenarios, asserting rendering, escaping, fallbacks, budget warnings, the
// decision-graph tri-state, and live filtering. Run: node frontend/test_app_render.mjs
import fs from 'node:fs';
import vm from 'node:vm';

const here = new URL('.', import.meta.url);
const appCode = fs.readFileSync(new URL('./app.js', here), 'utf8');
const realData = JSON.parse(fs.readFileSync(new URL('./data.json', here), 'utf8'));

const failures = [];
const ok = (cond, msg) => { if (!cond) failures.push(msg); };

const tick = () => new Promise((r) => setTimeout(r, 30));

// Build a fresh app instance (own vm context + DOM stub) per scenario.
function runApp(data) {
  const elements = new Map();
  const make = (id) => ({
    id,
    value: '',
    _l: {},
    innerHTML: '',
    addEventListener(ev, fn) { (this._l[ev] || (this._l[ev] = [])).push(fn); },
  });
  const document = {
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, make(id));
      return elements.get(id);
    },
  };
  const fetch = async () => ({ ok: true, status: 200, json: async () => data });
  const sandbox = { document, fetch, console, setTimeout, clearTimeout, URL };
  vm.createContext(sandbox);
  vm.runInContext(appCode, sandbox);
  const html = (id) => (elements.get(id) ? elements.get(id).innerHTML : '');
  const set = (id, v) => { document.getElementById(id).value = v; };
  const fire = (id, ev) => { (document.getElementById(id)._l[ev] || []).forEach((fn) => fn()); };
  return { html, set, fire };
}

// --- Scenario 1: contract — real data renders all 7 panels ---
{
  const app = runApp(realData);
  await tick();
  ok(app.html('summaryCards').includes('Tasks'), 'S1 summary missing Tasks');
  ok(app.html('overviewPanel').includes('Task 狀態分佈'), 'S1 overview missing distribution');
  ok(app.html('budgetPanel').includes('CLAUDE.md') && app.html('budgetPanel').includes('tokens'), 'S1 budget missing');
  ok(/20\d{6}|2026/.test(app.html('taskList')), 'S1 taskList empty');
  ok(app.html('timeline').includes('D00'), 'S1 timeline missing decisions');
  const g = app.html('decisionGraph');
  ok(g.includes('<svg') && g.includes('<rect') && g.includes('<line') && g.includes('決策'), 'S1 graph incomplete');
  ok(app.html('logBoard').length > 0, 'S1 logBoard empty');
}

// --- Scenario 2: XSS — user-controlled fields must be escaped ---
{
  const xss = {
    tasks: [{ task_id: '20260101-001', goal: '<img src=x onerror=alert(1)>', date: '2026-01-01', status: 'done', skill_type: 'ops' }],
    logs: [{ run_id: '<b>RUN</b>', task_id: 't', status: 'completed' }],
    decisions: [{ decision_id: 'D1', date: '2026-01-01', decision: '"><script>alert(1)</script>', related_task: '20260101-001' }],
    overview: {}, budget: {},
  };
  const app = runApp(xss);
  await tick();
  const all = ['taskList', 'logBoard', 'timeline', 'decisionGraph'].map(app.html).join('\n');
  ok(!all.includes('<img src=x onerror'), 'S2 raw <img> not escaped');
  ok(!all.includes('<script>alert(1)'), 'S2 raw <script> not escaped');
  ok(!all.includes('<b>RUN</b>'), 'S2 raw <b> not escaped');
  ok(app.html('taskList').includes('&lt;img'), 'S2 expected escaped &lt;img');
  ok(app.html('summaryCards').includes('Tasks'), 'S2 unexpected error path');
}

// --- Scenario 3: empty data — fallbacks shown, no crash ---
{
  const empty = {
    tasks: [], logs: [], decisions: [], overview: {},
    budget: { context: { budget: 3000, total: 0, files: [] }, skills: { budget: 1500, items: [] } },
  };
  const app = runApp(empty);
  await tick();
  ok(app.html('taskList').includes('無符合條件資料'), 'S3 taskList fallback missing');
  ok(app.html('timeline').includes('無符合條件資料'), 'S3 timeline fallback missing');
  ok(app.html('logBoard').includes('找不到 log 資料'), 'S3 logBoard fallback missing');
  ok(app.html('decisionGraph').includes('無符合條件資料'), 'S3 graph fallback missing');
  ok(app.html('budgetPanel').includes('0 / 3000 tokens'), 'S3 budget zero state missing');
  ok(app.html('overviewPanel').includes('—'), 'S3 overview empty dash missing');
}

// --- Scenario 4: over-budget — warning marker rendered ---
{
  const over = {
    tasks: [], logs: [], decisions: [], overview: {},
    budget: {
      context: { budget: 1000, total: 1500, files: [{ path: 'CLAUDE.md', tokens: 1500 }] },
      skills: { budget: 100, items: [{ path: 'skills/ops/SKILL.md', tokens: 300 }] },
    },
  };
  const app = runApp(over);
  await tick();
  ok(app.html('budgetPanel').includes('⚠'), 'S4 over-budget warning missing');
  ok(app.html('budgetPanel').includes('1500 / 1000 tokens'), 'S4 context over value missing');
}

// --- Scenario 5: decision graph tri-state (matched / external / orphan) ---
{
  const data = {
    tasks: [{ task_id: 'T-MATCH', goal: 'matched task', date: '2026-01-02', status: 'done' }],
    logs: [],
    decisions: [
      { decision_id: 'D-MATCH', date: '2026-01-01', decision: 'links existing', related_task: 'T-MATCH' },
      { decision_id: 'D-EXT', date: '2026-01-02', decision: 'links archived', related_task: 'T-GONE' },
      { decision_id: 'D-ORPH', date: '2026-01-03', decision: 'no link', related_task: '' },
    ],
    overview: {}, budget: {},
  };
  const app = runApp(data);
  await tick();
  const g = app.html('decisionGraph');
  ok(g.includes('決策 3'), 'S5 legend decisions count');
  ok(g.includes('關聯任務 2'), 'S5 legend related tasks count');
  ok(g.includes('外部引用 1'), 'S5 legend external count');
  ok(g.includes('無關聯 1'), 'S5 legend orphan count');
  ok(g.includes('stroke-dasharray'), 'S5 external dashed edge missing');
  ok(g.includes('外部'), 'S5 external label missing');
  ok((g.match(/<line/g) || []).length === 2, 'S5 expected exactly 2 edges (matched + external)');
}

// --- Scenario 6: live filtering (keyword + date) + reset ---
{
  const data = {
    tasks: [
      { task_id: 'AAA-1', goal: 'alpha thing', date: '2026-01-01', status: 'done', skill_type: 'ops' },
      { task_id: 'BBB-2', goal: 'beta thing', date: '2026-02-01', status: 'done', skill_type: 'review' },
    ],
    logs: [], decisions: [], overview: {}, budget: {},
  };
  const app = runApp(data);
  await tick();
  ok(app.html('taskList').includes('AAA-1') && app.html('taskList').includes('BBB-2'), 'S6 both tasks initially');

  app.set('keyword', 'alpha'); app.fire('keyword', 'input');
  ok(app.html('taskList').includes('AAA-1') && !app.html('taskList').includes('BBB-2'), 'S6 keyword filter failed');

  app.fire('resetFilters', 'click');
  ok(app.html('taskList').includes('AAA-1') && app.html('taskList').includes('BBB-2'), 'S6 reset failed');

  app.set('dateFrom', '2026-01-15'); app.fire('dateFrom', 'input');
  ok(!app.html('taskList').includes('AAA-1') && app.html('taskList').includes('BBB-2'), 'S6 date filter failed');
}

if (failures.length) {
  console.error(`FAILED frontend deep render tests (${failures.length}):`);
  failures.forEach((f) => console.error(`  - ${f}`));
  process.exit(1);
}
console.log('OK: frontend deep render tests passed (6 scenarios)');
