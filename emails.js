const $=s=>document.querySelector(s);
const params=new URL(location.href).searchParams;
let currentPage=Number(params.get('page'))||1,version=0;
const kinds={single_occurrence:'Single source occurrence',exact_visible_copies:'Exact visible copies · unverified',possible_repeat_incomplete:'Possible repeat · incomplete headers'};
function node(tag,cls,text){const x=document.createElement(tag);if(cls)x.className=cls;if(text!==undefined)x.textContent=text;return x;}
function link(text,url){const a=node('a','',text);a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a;}
function fieldValue(value){return value&&value.replace(/[\s'"<>]/g,'')?value:'Blank / redacted / unreadable';}
function detail(dl,key,value){dl.append(node('dt','',key),node('dd','',value));}
function render(group){
 const r=group.representative,card=node('article','email-card');
 const head=node('div','email-card-head');head.append(node('span','eyebrow',`${r.file_id} / PDF PAGE ${r.source_page} / LINE ${r.source_line}`),node('span','badge',kinds[group.kind]));
 const title=node('h3','',r.headers.subject||'Subject unresolved');
 const headers=node('dl','email-headers');detail(headers,'From',fieldValue(r.headers.from));detail(headers,'To',fieldValue(r.headers.to));detail(headers,'Source date',r.raw_date||'Not extracted');detail(headers,'Parsed candidate',r.parsed_timestamp_candidate||'Unresolved / ambiguous');
 const flags=node('p','email-flags',r.flags.filter(x=>!['candidate_not_verified_message','body_boundary_unverified'].includes(x)).map(x=>x.replaceAll('_',' ')).join(' · ')||'Header fields present; still requires source review.');
 const sources=node('div','email-sources');
 for(const source of group.sources){const row=node('div','');row.append(link(`${source.file_id} · PDF page ${source.source_page}`,`/Epstein_Files/?doc=${encodeURIComponent(source.file_id)}&pdfpage=${source.source_page}`),document.createTextNode(` · extracted line ${source.source_line} · `),link('DOJ PDF ↗',window.PilotStatic.pdfUrl(source.file_id,source.source_page)));sources.append(row);}
 const raw=node('details','evidence');raw.append(node('summary','',`Inspect raw headers & detected body · ${group.occurrences} source ${group.occurrences===1?'occurrence':'occurrences'}`));
 const rawHeaders=node('pre','email-raw',r.header_evidence.map(h=>`PDF p${h.page}, line ${h.line} · ${h.field}: ${h.value}`).join('\n'));
 const body=node('pre','email-raw',r.body||'No body text detected.');
 raw.append(node('p','evidence-note','Header values are raw extracted text. Address-like strings are not verified identities. This body segment can contain signatures, quotes, attachments, or extraction artifacts.'),rawHeaders,node('h4','',`Detected body segment · PDF ${r.body_pages.length===1?'page':'pages'} ${r.body_pages.join(', ')||'not established'}`),body);
 card.append(head,title,headers,flags,sources,raw);return card;
}
async function refresh(reset=true){
 if(reset)currentPage=1;const token=++version;
 const filter=$('#email-filter').value,doc=$('#email-document').value;
 const url=new URL(location.href);url.search='';if(filter!=='all')url.searchParams.set('filter',filter);if(doc)url.searchParams.set('document',doc);if(currentPage>1)url.searchParams.set('page',currentPage);history.replaceState(null,'',url);
 $('#email-status').textContent='Loading published review groups…';$('#email-prev').disabled=true;$('#email-next').disabled=true;
 try{
  const response=await fetch(`/api/emails?${new URLSearchParams({filter,document:doc,page:currentPage})}`,{cache:'no-store'});const data=await response.json();if(!response.ok)throw new Error(data.error||'Could not read the published email cache.');if(token!==version)return;
  const summary=data.summary;$('#email-occurrences').textContent=summary.candidate_occurrences;$('#email-documents').textContent=summary.documents_with_candidates;$('#email-repeats').textContent=summary.repeat_groups;
  const allOption=node('option','','All source documents');allOption.value='';$('#email-document').replaceChildren(allOption);
  for(const id of data.documents){const option=node('option','',id);option.value=id;$('#email-document').append(option);}
  if(doc&&!data.documents.includes(doc)){const option=node('option','',`${doc} (no candidates)`);option.value=doc;$('#email-document').append(option);}
  $('#email-document').value=doc;
  $('#email-status').textContent=`${data.total_groups} visible ${data.total_groups===1?'group':'groups'} · ${summary.candidate_occurrences} source occurrences in the pilot · unique-message count not established`;
  $('#email-results').replaceChildren(...data.results.map(render));
  if(!data.results.length){const empty=node('div','empty-results');empty.append(node('h3','','No groups match these filters.'),node('p','',filter==='repeats'?'No exact visible repeat groups were found under the current rules. OCR differences or partial copies may still conceal duplication.':'Try a different source document or review focus.'));$('#email-results').append(empty);}
  const pages=Math.max(1,Math.ceil(data.total_groups/data.page_size));$('#email-page').textContent=`Page ${currentPage} of ${pages}`;$('#email-prev').disabled=currentPage<=1;$('#email-next').disabled=currentPage>=pages;
 }catch(error){if(token===version){$('#email-status').textContent=error.message;$('#email-results').replaceChildren();$('#email-page').textContent='';}}
}
async function init(){
 $('#email-filter').value=['all','unresolved','repeats'].includes(params.get('filter'))?params.get('filter'):'all';
 if(params.get('document')){const option=node('option','',params.get('document'));option.value=params.get('document');$('#email-document').append(option);$('#email-document').value=option.value;}
 $('#email-filters').addEventListener('submit',e=>{e.preventDefault();refresh();});$('#email-prev').addEventListener('click',()=>{currentPage--;refresh(false);});$('#email-next').addEventListener('click',()=>{currentPage++;refresh(false);});await refresh(false);
}
init();
