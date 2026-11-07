const $=s=>document.querySelector(s);
const initial=new URL(location.href).searchParams;
let coverage;
function node(tag,text){const el=document.createElement(tag);if(text!==undefined)el.textContent=text;return el;}
function reviewLink(value,filter,document=''){
 if(!value)return node('span','0');
 const link=node('a',String(value));link.href='/Epstein_Files/emails.html?'+new URLSearchParams({filter,...(document?{document}:{})});
 link.setAttribute('aria-label',`${value} ${filter} candidate occurrences${document?' in '+document:''}; open review groups`);return link;
}
function cell(row,value){const td=node('td');td.append(value instanceof Node?value:document.createTextNode(String(value)));row.append(td);}
function briefLink(value,row,dateOnly=false){
 if(!value)return node('span','0');
 const params=new URLSearchParams({date_from:row.primary_date,date_to:row.primary_date,dataset:row.dataset});if(dateOnly)params.set('date_only','1');
 const link=node('a',String(value));link.href='/Epstein_Files/timeframes.html?'+params+'#brief-'+row.id;
 link.setAttribute('aria-label',`${row.id}: open ${dateOnly?'date evidence':'prepared brief and editorial check details'}`);return link;
}
function renderDocuments(){
 const dataset=$('#coverage-dataset').value,includeEmpty=$('#coverage-empty').checked;
 const all=coverage.documents.filter(r=>!dataset||String(r.dataset)===dataset),rows=all.filter(r=>includeEmpty||r.candidates||r.eligible_dated_documents);
 const url=new URL(location.href);url.search='';if(dataset)url.searchParams.set('dataset',dataset);if(includeEmpty)url.searchParams.set('empty','1');history.replaceState(null,'',url);
 $('#coverage-document-status').textContent=`${rows.length} of ${all.length} pilot PDFs shown${includeEmpty?'':' · PDFs without email candidates or usable reviewed dates hidden'}. Pilot totals above remain unchanged.`;
 $('#document-coverage').replaceChildren(...rows.map(r=>{
  const row=node('tr'),title=node('th'),link=node('a',r.id);title.scope='row';link.href='/Epstein_Files/?doc='+encodeURIComponent(r.id)+'&pdfpage=1';title.append(link);row.append(title);cell(row,r.dataset);
  for(const [field,filter] of [['candidates','all'],['reviewed','reviewed'],['unreviewed','unreviewed'],['boundary','boundary']])cell(row,reviewLink(r[field],filter,r.id));
  cell(row,briefLink(r.prepared_briefs,r));cell(row,briefLink(r.source_checked_briefs,r));cell(row,briefLink(r.date_evidence_only,r,true));
  for(const [field,filter] of [['sender_unresolved','sender'],['recipient_unresolved','recipient'],['date_unresolved','date']])cell(row,reviewLink(r[field],filter,r.id));
  return row;
 }));
 if(!rows.length){const row=node('tr'),cell=node('td','No PDFs match these display settings.');cell.colSpan=12;row.append(cell);$('#document-coverage').append(row);}
}
async function init(){
 try{
  const response=await fetch('/api/coverage',{cache:'no-store'});if(!response.ok)throw new Error('Could not load review coverage.');coverage=await response.json();const t=coverage.totals;
  const stats=[['candidates','all','CANDIDATE OCCURRENCES'],['reviewed','reviewed','SOURCE-REVIEWED'],['unreviewed','unreviewed','UNREVIEWED'],['boundary','boundary','FLAGGED BOUNDARIES']];
  $('#coverage-totals').replaceChildren(...stats.map(([field,filter,label])=>{const item=node('div'),strong=node('strong');strong.append(reviewLink(t[field],filter));item.append(strong,node('span',label));return item;}));
  $('#review-progress').max=Math.max(1,t.candidates);$('#review-progress').value=t.reviewed;
  $('#coverage-ratio').textContent=`${t.reviewed} of ${t.candidates} candidate occurrences reviewed (${t.candidates?Math.round(100*t.reviewed/t.candidates):0}%). ${t.documents_with_reviews} of ${t.documents_with_candidates} PDFs with candidates have at least one review; coverage within each PDF is partial.`;
  $('#coverage-status').textContent=`Pilot totals: ${t.documents} PDFs · ${t.documents_with_candidates} with detected email candidates · ${t.breakdowns} body breakdowns · ${t.adjacent_checks} adjacent-page checks.`;
  $('#brief-coverage-totals').replaceChildren(...[['eligible_dated_documents','DATED DOCUMENTS'],['prepared_briefs','PREPARED PAGE BRIEFS'],['source_checked_briefs','EDITORIAL SOURCE CHECKS'],['date_evidence_only','DATE EVIDENCE ONLY']].map(([field,label])=>{const item=node('div');item.append(node('strong',t[field]),node('span',label));return item;}));
  $('#brief-coverage-status').textContent=`${t.prepared_briefs} of ${t.eligible_dated_documents} dated PDFs have a prepared, limited-page brief. ${t.source_checked_briefs} briefs have a recorded Codex editorial check; ${t.prepared_briefs-t.source_checked_briefs} await that separate pass. ${t.excluded_without_reviewed_date} PDFs lack a usable reviewed date and are excluded from timeframe analysis. A source check is not independent or human verification.`;
  const gaps=$('#coverage-gaps');gaps.append(document.createTextNode('Parser gaps: '));
  for(const [field,filter,label] of [['sender_unresolved','sender','From addresses'],['recipient_unresolved','recipient','To addresses'],['date_unresolved','date','dates']]){gaps.append(reviewLink(t[field],filter),document.createTextNode(` unresolved ${label} · `));}
  gaps.append(document.createTextNode('overlapping categories.'));
  for(const r of coverage.datasets){
   const option=node('option',`Dataset ${r.dataset}`);option.value=r.dataset;$('#coverage-dataset').append(option);
   const row=node('tr'),th=node('th'),button=node('button',`Dataset ${r.dataset}`);th.scope='row';button.className='text-button';button.type='button';button.addEventListener('click',()=>{$('#coverage-dataset').value=String(r.dataset);renderDocuments();$('#coverage-dataset').focus();});th.append(button);row.append(th);
   for(const field of ['documents','documents_with_candidates','candidates','reviewed','unreviewed','boundary','eligible_dated_documents','prepared_briefs','source_checked_briefs','date_evidence_only'])cell(row,r[field]);$('#dataset-coverage').append(row);
  }
  if(coverage.datasets.some(r=>String(r.dataset)===initial.get('dataset')))$('#coverage-dataset').value=initial.get('dataset');
  $('#coverage-empty').checked=initial.get('empty')==='1';$('#coverage-dataset').addEventListener('change',renderDocuments);$('#coverage-empty').addEventListener('change',renderDocuments);renderDocuments();
 }catch(error){$('#coverage-status').textContent=error.message;}
}
init();
