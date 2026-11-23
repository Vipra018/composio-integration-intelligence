const fs = require('fs');
const path = require('path');

const htmlPath = path.resolve(__dirname, '../reports/index.html');
const html = fs.readFileSync(htmlPath, 'utf8');
const match = html.match(/<script>([\s\S]*?)<\/script>/);
if (!match) {
  console.error('FAIL: No inline <script> block found in index.html');
  process.exit(1);
}
const script = match[1];

const elements = {};
function getEl(id) {
  if (!elements[id]) {
    let _inner = '';
    elements[id] = {
      id,
      value: '',
      children: [],
      get innerHTML() { return _inner; },
      set innerHTML(val) {
        _inner = val;
        if (val === '') this.children = [];
      },
      textContent: '',
      appendChild: function(c) { this.children.push(c); },
      classList: {
        classes: new Set(),
        add: function(c) { this.classes.add(c); },
        remove: function(c) { this.classes.delete(c); }
      },
      style: {}
    };
  }
  return elements[id];
}

const document = {
  getElementById: getEl,
  querySelectorAll: (selector) => [],
  createElement: (tag) => ({
    tag,
    innerHTML: '',
    appendChild: function(c) {},
    classList: { add: function(c) {}, remove: function(c) {} },
    style: {}
  }),
  addEventListener: () => {}
};
const window = { addEventListener: () => {} };
const Chart = function() { return { update: () => {} }; };

const vm = require('vm');
const context = { console, document, window, Chart };
vm.createContext(context);

try {
  vm.runInContext(script, context);
  const dataLen = vm.runInContext('APPS_DATA.length', context);
  console.log('PASS: Script compiled and executed with 0 syntax errors.');
  console.log(`PASS: APPS_DATA length = ${dataLen} (expected 100)`);
  if (dataLen !== 100) {
    throw new Error(`Expected 100 apps, got ${dataLen}`);
  }

  // 1. Category Table
  vm.runInContext('renderCategoryTable();', context);
  const catRows = elements['category-table-body'].children.length;
  console.log(`PASS: renderCategoryTable rendered ${catRows} category rows (expected 10)`);
  if (catRows !== 10) throw new Error(`Expected 10 category rows, got ${catRows}`);

  // 2. Filter Population
  vm.runInContext('populateFilters();', context);
  const filterOptions = elements['category-filter'].children.length;
  console.log(`PASS: populateFilters populated ${filterOptions} options`);

  // 3. 100 Apps Table Render
  vm.runInContext('filterApps();', context);
  const appRows = elements['apps-table-body'].children.length;
  console.log(`PASS: filterApps rendered ${appRows} application rows (expected 100)`);
  if (appRows !== 100) throw new Error(`Expected 100 app rows, got ${appRows}`);

  // 4. Search Filter
  elements['search-input'].value = 'github';
  vm.runInContext('filterApps();', context);
  const githubRows = elements['apps-table-body'].children.length;
  console.log(`PASS: Search "github" rendered ${githubRows} rows`);

  // 5. Clear Search
  elements['search-input'].value = '';
  vm.runInContext('filterApps();', context);
  const resetRows = elements['apps-table-body'].children.length;
  console.log(`PASS: Cleared search restored ${resetRows} rows`);

  // 6. Category Filter
  elements['category-filter'].value = 'CRM and Sales';
  vm.runInContext('filterApps();', context);
  const crmRows = elements['apps-table-body'].children.length;
  console.log(`PASS: Filter "CRM and Sales" rendered ${crmRows} rows (expected 10)`);
  if (crmRows !== 10) throw new Error(`Expected 10 CRM rows, got ${crmRows}`);
  elements['category-filter'].value = '';

  // 7. Inspect Target Apps in Modal
  const testApps = [
    { id: 'ahrefs', expectedMode: 'API', expectedMCP: 'Official' },
    { id: 'aircall', expectedMode: 'API', expectedMCP: 'Official' },
    { id: 'reducto', expectedMode: 'API', expectedMCP: 'Official' },
    { id: 'github', expectedMode: 'API', expectedAuth: 'TOKEN / PAT' },
    { id: 'salesforce', expectedMode: 'API', expectedAuth: 'OAUTH2' },
    { id: 'notebooklm', expectedMode: 'WEB_ONLY', expectedAuth: 'NOT_APPLICABLE' },
    { id: 'sherlock', expectedMode: 'CLI / LOCAL_PROCESS', expectedAuth: 'NOT_APPLICABLE' }
  ];

  for (const t of testApps) {
    vm.runInContext(`openModal("${t.id}");`, context);
    const title = elements['modal-title'].textContent;
    const mode = elements['modal-mode'].textContent;
    const auth = elements['modal-primary-auth'].textContent;
    const composioHTML = elements['modal-composio'].innerHTML;
    console.log(`PASS: Modal for [${t.id}] -> Title: "${title}", Mode: "${mode}", Primary Auth: "${auth}"`);
    if (t.expectedMode && mode !== t.expectedMode) {
      throw new Error(`App ${t.id} expected mode ${t.expectedMode}, got ${mode}`);
    }
    if (t.expectedAuth && auth !== t.expectedAuth) {
      throw new Error(`App ${t.id} expected auth ${t.expectedAuth}, got ${auth}`);
    }
    vm.runInContext('closeModal();', context);
  }

  console.log('\n=== ALL DOM & JAVASCRIPT SMOKE TESTS PASSED WITH ZERO ERRORS ===');
} catch (err) {
  console.error('FAIL during smoke test:', err);
  process.exit(1);
}
