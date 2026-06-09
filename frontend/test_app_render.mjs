// Dependency-free render smoke test for frontend/app.js.
// Executes app.js in a vm sandbox with a stubbed DOM + fetch (serving the real
// frontend/data.json), then asserts every panel rendered. Run: node frontend/test_app_render.mjs
import fs from 'node:fs';
import vm from 'node:vm';

const here = new URL('.', import.meta.url);
const appCode = fs.readFileSync(new URL('./app.js', here), 'utf8');
const data = JSON.parse(fs.readFileSync(new URL('./data.json', here), 'utf8'));

const elements = new Map();
function makeEl(id) {
  return {
    id,
    value: '',
    innerHTML: '',
    addEventListener() {},
  };
}
const document = {
  getElementById(id) {
    if (!elements.has(id)) elements.set(id, makeEl(id));
    return elements.get(id);
  },
};
const fetchStub = async () => ({ ok: true, status: 200, json: async () => data });

const sandbox = { document, fetch: fetchStub, console, setTimeout, clearTimeout, URL };
vm.createContext(sandbox);
vm.runInContext(appCode, sandbox);

// init() is async (fetch); let microtasks/timers flush before asserting.
await new Promise((r) => setTimeout(r, 50));

const failures = [];
function check(id, ...needles) {
  const el = elements.get(id);
  const html = el ? el.innerHTML : '';
  if (!html) {
    failures.push(`#${id}: empty innerHTML`);
    return;
  }
  for (const n of needles) {
    if (!html.includes(n)) failures.push(`#${id}: missing ${JSON.stringify(n)}`);
  }
}

check('summaryCards', 'card', 'Tasks');
check('overviewPanel', 'Task 狀態分佈');
check('budgetPanel', 'CLAUDE.md', 'tokens');
check('taskList', '2026');
check('timeline', 'D00');
check('decisionGraph', '<svg', '決策', '<line', '<rect');
check('logBoard');

if (failures.length) {
  console.error('FAILED frontend render smoke test:');
  failures.forEach((f) => console.error(`  - ${f}`));
  process.exit(1);
}
console.log('OK: frontend render smoke test passed (7 panels rendered)');
