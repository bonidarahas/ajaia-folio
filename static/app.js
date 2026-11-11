const $ = (id) => document.getElementById(id);
const state = {users:[], userId:Number(localStorage.getItem('demoUserId')||1), tab:'owned', active:null, docs:{owned:[],shared:[]}, timer:null, dirty:false, saving:false, revision:0};
let toastTimer;
function toast(message){const el=$('toast'); el.textContent=message;el.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove('show'),3500)}
async function request(path, options={}){
  const headers={...options.headers,'X-User-ID':String(state.userId)};
  if(options.body && !(options.body instanceof FormData)) headers['Content-Type']='application/json';
  const res=await fetch('/api'+path,{...options,headers});
  if(!res.ok){let body={};try{body=await res.json()}catch{};throw new Error(typeof body.detail==='string'?body.detail:`Request failed (${res.status})`)}
  return res.status===204?null:res.json();
}
const prettyDate = s=>new Intl.DateTimeFormat('en-US',{month:'short',day:'numeric',year:'numeric'}).format(new Date(s));
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function loadList(){state.docs=await request('/documents');$('ownedCount').textContent=state.docs.owned.length;$('sharedCount').textContent=state.docs.shared.length;renderList()}
function renderList(){
 const shared=state.tab==='shared',items=state.docs[state.tab];
 $('pageTitle').textContent=shared?'Shared with me':'My documents';$('pageSubtitle').textContent=shared?'Documents your teammates invited you to edit.':'Your ideas, all in one place.';
 $('breadcrumbs').textContent='Workspace / '+$('pageTitle').textContent;
 $('listHeading').textContent=shared?'Shared documents':'All documents';
 document.querySelectorAll('.nav').forEach(el=>el.classList.toggle('active',el.dataset.tab===state.tab));
 $('empty').hidden=items.length!==0;$('docList').hidden=items.length===0;
 $('docList').innerHTML=items.map(d=>`<div class="doc-card" data-id="${d.id}" tabindex="0" role="button" aria-label="Open ${esc(d.title)}"><div class="doc-icon">▤</div><div class="doc-info"><strong>${esc(d.title)}</strong><p>${shared?'Shared by '+esc(d.owner_name)+' · ':''}Edited ${prettyDate(d.updated_at)}</p></div><div class="doc-end">›</div></div>`).join('');
 document.querySelectorAll('.doc-card').forEach(el=>{el.addEventListener('click',()=>openDoc(Number(el.dataset.id)));el.addEventListener('keydown',e=>{if(e.key==='Enter')openDoc(Number(el.dataset.id))})});
}
async function showLibrary(){await flushSave();state.active=null;$('editorView').hidden=true;$('library').hidden=false;await loadList()}
async function openDoc(id){try{await flushSave();state.active=await request('/documents/'+id);state.dirty=false;state.revision=0;$('docTitle').value=state.active.title;$('editor').innerHTML=state.active.content;$('ownerLabel').textContent=state.active.is_owner?'Owned by you':'Shared by '+state.active.owner_name;$('saveStatus').textContent='All changes saved';$('library').hidden=true;$('editorView').hidden=false;countWords();$('docTitle').focus()}catch(e){toast(e.message)}}
async function createDoc(){try{await flushSave();const doc=await request('/documents',{method:'POST',body:JSON.stringify({title:'Untitled document'})});await openDoc(doc.id)}catch(e){toast(e.message)}}
function markDirty(){if(!state.active)return;state.dirty=true;state.revision++;$('saveStatus').textContent='Unsaved changes…';clearTimeout(state.timer);state.timer=setTimeout(saveDoc,650)}
async function saveDoc(){if(!state.active||!state.dirty||state.saving)return;
  state.saving=true;const id=state.active.id, rev=state.revision, title=$('docTitle').value.trim()||'Untitled document',content=$('editor').innerHTML;
  $('saveStatus').textContent='Saving…';
  try{await request('/documents/'+id,{method:'PATCH',body:JSON.stringify({title,content})});if(state.active?.id===id && rev===state.revision){state.dirty=false;$('saveStatus').textContent='All changes saved'}}
  catch(e){$('saveStatus').textContent='Save failed — retrying';toast(e.message)}
  finally{state.saving=false;if(state.dirty&&state.active?.id===id){clearTimeout(state.timer);state.timer=setTimeout(saveDoc,1200)}}
}
async function flushSave(){clearTimeout(state.timer);if(state.saving){while(state.saving)await new Promise(r=>setTimeout(r,50))}if(state.dirty)await saveDoc()}
function countWords(){const s=$('editor').innerText.trim();$('wordCount').textContent=(s?s.split(/\s+/).length:0)+' words'}
async function importFile(file){if(!file)return;const data=new FormData();data.append('file',file);try{const doc=await request('/import',{method:'POST',body:data});await openDoc(doc.id);toast('Document imported successfully')}catch(e){toast(e.message)}finally{$('fileUpload').value=''}}
function avatar(name){return name.trim().split(/\s+/).map(p=>p[0]).slice(0,2).join('').toUpperCase()}
function renderMembers(){const doc=state.active,owner=state.users.find(u=>u.id===doc.owner_id);let members=[{id:owner.id,name:owner.name,role:'Owner'},...doc.shares.map(s=>({id:s.user_id,name:s.name,role:'Editor'}))];$('memberList').innerHTML=members.map(m=>`<div class="member"><div class="avatar">${esc(avatar(m.name))}</div><div class="member-info"><strong>${esc(m.name)}</strong><small>${esc(m.role)}</small></div>${m.role==='Owner'?'':`<button class="revoke" data-id="${m.id}">Remove</button>`}</div>`).join('');document.querySelectorAll('.revoke').forEach(el=>el.addEventListener('click',async()=>{try{await request('/documents/'+doc.id+'/share/'+el.dataset.id,{method:'DELETE'});state.active=await request('/documents/'+doc.id);renderMembers();renderEligible();toast('Access removed')}catch(e){toast(e.message)}}))}
function renderEligible(){const ids=new Set([state.active.owner_id,...state.active.shares.map(s=>s.user_id)]);const other=state.users.filter(u=>!ids.has(u.id));$('shareUser').innerHTML=other.map(u=>`<option value="${u.id}">${esc(u.name)} (${esc(u.email)})</option>`).join('');$('addShare').disabled=!other.length}
async function showShare(){await flushSave();if(!state.active)return;if(!state.active.is_owner){toast('Only the owner can manage sharing');return}renderMembers();renderEligible();$('overlay').hidden=false}
function hideShare(){$('overlay').hidden=true}
async function switchUser(next){await flushSave();state.userId=Number(next);localStorage.setItem('demoUserId',next);state.active=null;$('editorView').hidden=true;$('library').hidden=false;state.tab='owned';await loadList();toast('Switched demo user')}
async function boot(){
 try{state.users=await request('/users');if(!state.users.some(u=>u.id===state.userId))state.userId=state.users[0].id;$('userSelect').innerHTML=state.users.map(u=>`<option value="${u.id}">${esc(u.name)}</option>`).join('');$('userSelect').value=state.userId;await loadList()}catch(e){toast('Unable to load workspace: '+e.message)}
 $('userSelect').addEventListener('change',e=>switchUser(e.target.value).catch(err=>toast(err.message)));
 $('newDoc').addEventListener('click',createDoc);$('topNew').addEventListener('click',createDoc);
 document.querySelectorAll('.nav').forEach(n=>n.addEventListener('click',()=>{state.tab=n.dataset.tab;renderList()}));
 $('back').addEventListener('click',()=>showLibrary().catch(e=>toast(e.message)));
 $('docTitle').addEventListener('input',markDirty);$('editor').addEventListener('input',()=>{markDirty();countWords()});
 document.querySelectorAll('.toolbar button').forEach(b=>b.addEventListener('mousedown',e=>e.preventDefault()));
 document.querySelectorAll('.toolbar button').forEach(b=>b.addEventListener('click',()=>{if(b.dataset.block)document.execCommand('formatBlock',false,b.dataset.block);else document.execCommand(b.dataset.cmd,false,null);markDirty();$('editor').focus();countWords()}));
 $('fileUpload').addEventListener('change',e=>importFile(e.target.files?.[0]));
 $('shareBtn').addEventListener('click',showShare);$('closeModal').addEventListener('click',hideShare);$('done').addEventListener('click',hideShare);$('overlay').addEventListener('click',e=>{if(e.target===$('overlay'))hideShare()});
 $('addShare').addEventListener('click',async()=>{try{state.active=await request('/documents/'+state.active.id+'/share',{method:'POST',body:JSON.stringify({user_id:Number($('shareUser').value)})});renderMembers();renderEligible();toast('Collaborator added')}catch(e){toast(e.message)}});
 document.addEventListener('keydown',e=>{if(e.key==='Escape')hideShare();if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='s'){e.preventDefault();flushSave()}});
 window.addEventListener('beforeunload',e=>{if(state.dirty){e.preventDefault();e.returnValue=''}});
}
boot();
