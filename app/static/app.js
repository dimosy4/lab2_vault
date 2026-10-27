let token = localStorage.getItem('vault_token');
const el = id => document.getElementById(id);
const message = text => el('message').textContent = text || '';
async function api(path, body) {
  const res = await fetch(path, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
  const data = await res.json();
  if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'HTTP ' + res.status);
  return data;
}
async function gql(query, variables = {}) {
  const res = await fetch('/graphql/', {method: 'POST', headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${token}`}, body: JSON.stringify({query, variables})});
  const data = await res.json();
  if (!res.ok || data.errors?.length) throw new Error(data.errors?.[0]?.message || 'GraphQL request failed');
  return data.data;
}
function showDashboard(visible) {el('login').style.display = visible ? 'none' : 'block'; el('dashboard').style.display = visible ? 'block' : 'none';}
function logout() {token = null; localStorage.removeItem('vault_token'); showDashboard(false); message('');}
async function refresh() {
  try {
    const data = await gql('{ me { email isAdmin } clients { id clientId name isConfidential createdAt } }');
    if (!data.me.isAdmin) throw new Error('Admin only: назначьте права администратора через CLI');
    el('whoami').textContent = data.me.email;
    const tbody = el('clientRows'); tbody.replaceChildren();
    data.clients.forEach(c => {
      const tr = document.createElement('tr');
      [c.name, c.clientId, c.isConfidential ? 'Confidential' : 'Public', new Date(c.createdAt).toLocaleDateString('ru-RU')].forEach(value => {
        const td = document.createElement('td'); td.textContent = value; tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    if (!data.clients.length) {const tr = document.createElement('tr'); const td = document.createElement('td'); td.colSpan=4; td.textContent='Клиентов пока нет'; tr.appendChild(td); tbody.appendChild(tr);}
    message('');
  } catch (err) {message(err.message);}
}
el('loginForm').addEventListener('submit', async event => {
  event.preventDefault();
  try {
    const result = await api('/auth/login', {email: el('email').value, password: el('password').value});
    token = result.access_token; localStorage.setItem('vault_token', token); showDashboard(true); await refresh();
    el('password').value = '';
  } catch(err) {message(err.message);}
});
el('create').addEventListener('click', async () => {
  const name = prompt('Название клиента:'); if (!name?.trim()) return;
  const isConfidential = confirm('Конфиденциальный клиент? ОК = да, Отмена = публичный');
  try {await gql('mutation($name:String!,$conf:Boolean!){ createClient(name:$name,isConfidential:$conf){ id } }', {name: name.trim(), conf:isConfidential}); await refresh();}
  catch(err) {message(err.message);}
});
el('logout').addEventListener('click', logout);
el('refresh').addEventListener('click', refresh);
if (token) {showDashboard(true); refresh();}
