const labels = { pass: 'Passed', fail: 'Needs attention', missing: 'Missing', unknown: 'Not checked', idle: 'Not started', info: 'For your setup' };
const $ = id => document.getElementById(id);
const el = (tag, text, className) => {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
};
function badge(check, module = false) {
  return el('span', module && check.status === 'pass' ? 'Shared checks passed' : labels[check.status], `badge ${check.status}`);
}
function renderRows(id, checks) {
  $(id).replaceChildren(...checks.map(check => {
    const node = el('div', undefined, 'check-row');
    const title = el('div');
    title.append(el('strong', check.label));
    if (check.model) title.append(el('code', check.model, 'model-id'));
    node.append(title, badge(check), el('p', check.detail));
    return node;
  }));
}
async function openTile(title, category) {
  if (!window.parent.jupyterapp) {
    $('message').textContent = `Open “${title}” from the JupyterLab launcher.`;
    return;
  }
  try { await launch(title, category); }
  catch { $('message').textContent = `Could not open “${title}”. Try its JupyterLab launcher tile.`; }
}
function render(data) {
  renderRows('environment', data.environment);
  renderRows('keys', [...data.keys, data.search]);
  renderRows('endpoints', data.endpoints);
  renderRows('services', data.services);
  const passing = data.endpoints.filter(c => c.status === 'pass').length;
  const local = data.services.filter(c => c.status === 'pass').length;
  const setup = [...data.environment.slice(0, 2), ...data.keys.slice(0, 2)];
  const gaps = setup.filter(c => ['fail', 'missing'].includes(c.status)).length;
  const stats = [
    ['Setup', gaps ? `${gaps} to check` : 'Ready', 'Environment & required keys'],
    ['Endpoints', `${passing} of ${data.endpoints.length} passed`, data.checked_at ? 'Latest capability checks' : 'Run checks to test your models'],
    ['Local services', `${local} of ${data.services.length} running`, 'Start these as you reach each lesson'],
  ];
  $('overview').replaceChildren(...stats.map(([label, value, note]) => {
    const card = el('div', undefined, 'stat');
    card.append(el('span', label), el('strong', value), el('small', note));
    return card;
  }));
  $('modules').replaceChildren(...data.modules.map(module => {
    const card = el('article', undefined, 'module');
    const title = el('h3');
    title.append(el('span', String(module.number).padStart(2, '0')), document.createTextNode(module.label));
    const button = el('button', 'Open lesson ↗');
    button.type = 'button';
    button.setAttribute('aria-label', `Open Module ${module.number}: ${module.label}`);
    button.onclick = () => openTile(module.tile, 'NVIDIA DevX Learning Path');
    card.append(badge(module, true), title, el('p', module.detail), button);
    return card;
  }));
  $('endpoint-summary').textContent = `${passing} / ${data.endpoints.length} passed`;
  $('checked-at').textContent = data.checked_at
    ? `Last checked ${new Date(data.checked_at).toLocaleString()}. Results can change as services change.`
    : 'No endpoint checks yet.';
}
async function refresh(network = false) {
  $('check').disabled = $('refresh').disabled = true;
  $('message').textContent = network ? 'Testing model responses, tool calls, retrieval, and web search…' : 'Checking your environment…';
  try {
    const response = await fetch(network ? 'api/check' : 'api/health', network
      ? { method: 'POST', headers: { 'X-Workshop-Check': '1' } } : {});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    render(data);
    const failed = [...data.endpoints, data.search].filter(c => ['fail', 'missing'].includes(c.status)).length;
    $('message').textContent = network
      ? failed ? 'Checks finished. Review the items that need attention below.' : 'Endpoint checks passed. Follow each lesson for its local setup.'
      : 'Setup refreshed. Local services can stay stopped until their lessons.';
  } catch {
    $('message').textContent = 'Could not finish the checks. Refresh this page and try again.';
  } finally { $('check').disabled = $('refresh').disabled = false; }
}
$('check').onclick = () => refresh(true);
$('refresh').onclick = () => refresh();
$('secrets').onclick = () => openTile('Secrets Manager', 'Workshop Utilities');
refresh();
