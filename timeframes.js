const $=s=>document.querySelector(s),initial=new URL(location.href).searchParams;let version=0;
const roles={email_sent:'Email sent date',report:'Report date',court_order:'Court order date',evidence_received:'Evidence received date',communication:'Communication date',transcript_session:'Transcript session date',letter:'Letter date',presentation:'Presentation date'};
function node(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
function sourceLink(id,page,label){const a=node('a',label);a.href='/Epstein_Files/?doc='+encodeURIComponent(id)+'&pdfpage='+page;a.target='_blank';a.rel='noopener noreferrer';return a;}
function card(item){
 const article=node('article',undefined,'email-card'),review=item.date_review;article.id='brief-'+item.id;
 article.append(node('p',`${item.primary_date} · ${roles[review.date_type]} · Dataset ${item.dataset}`,'eyebrow'),node('h3',item.brief?.title||item.id),node('p',item.id,'evidence-note'));
 if(item.brief){const brief=item.brief;article.append(node('p',`AI-assisted editorial draft · ${brief.scope}`,'badge'));
  if(brief.editorial_review){const check=brief.editorial_review,details=node('details',undefined,'evidence');details.append(node('summary',`Editorial source check · Codex · ${check.reviewed_on}`),node('p',check.notes),node('p','Statement support, attribution, page scope and limitations checked against the cited source. This is a same-assistant editorial check, not independent or human verification.','evidence-note'));article.append(details);}
  else article.append(node('p','Draft awaiting a separate editorial source-check pass.','evidence-note'));
  for(const point of brief.points){const section=node('section',undefined,'timeframe-point');section.append(node('p',point.statement),node('p',point.limitation,'timeframe-limitation'));
   for(const [i,cite] of point.citations.entries()){const evidence=node('details',undefined,'evidence');evidence.append(node('summary',`Inspect citation [${i+1}] · PDF page ${cite.page}`),sourceLink(item.id,cite.page,`[${i+1}] ${item.id} · PDF page ${cite.page} ↗`),node('blockquote',cite.quote));section.append(evidence);}
   article.append(section);
  }
 }else article.append(node('p','Date evidence only — no content brief prepared. This card does not summarize the document.','email-notice'));
 const date=node('details',undefined,'evidence');date.append(node('summary','Primary document date: evidence and rationale'),node('p',review.notes),sourceLink(item.id,review.evidence_page,`Date evidence · PDF page ${review.evidence_page} ↗`),node('blockquote',review.evidence_quote));article.append(date);return article;
}
async function refresh(){
 const token=++version,query=new URLSearchParams();for(const [key,id] of [['date_from','timeframe-from'],['date_to','timeframe-to'],['dataset','timeframe-dataset'],['person','timeframe-person']])if($('#'+id).value)query.set(key,$('#'+id).value);
 const includeDates=$('#timeframe-date-only').checked,url=new URL(location.href);url.search=query.toString();if(includeDates)url.searchParams.set('date_only','1');history.replaceState(null,'',url);
 $('#timeframe-status').textContent='Selecting prepared briefs…';$('#timeframe-results').replaceChildren();$('#timeframe-stats').replaceChildren();$('#timeframe-scope').textContent='';
 try{const response=await fetch('/api/timeframes?'+query,{cache:'no-store'}),data=await response.json();if(!response.ok)throw new Error(data.error||'Could not load timeframe briefs.');if(token!==version)return;
 const rows=data.results.filter(r=>includeDates||r.brief);
 $('#timeframe-status').textContent=`${rows.length} source cards shown · ${data.prepared_briefs} prepared briefs, ${data.source_checked_briefs} with a recorded editorial source check. Date-evidence-only cards ${includeDates?'included':'hidden'}.`;
 $('#timeframe-scope').textContent=`${data.eligible_dated_documents} of ${data.scope_documents} pilot PDFs in the dataset scope have usable reviewed dates; ${data.excluded_without_reviewed_date} are excluded without one. ${data.documents_in_date_range} dated documents fall in range, and ${data.selected_documents} match the document/name selection. This is partial coverage, not a complete history of the period.`;
 for(const [value,label] of [[data.selected_documents,'SELECTED DATED DOCUMENTS'],[data.prepared_briefs,'PREPARED CONTENT BRIEFS'],[data.date_evidence_only,'DATE EVIDENCE ONLY'],[data.excluded_without_reviewed_date,'EXCLUDED WITHOUT REVIEWED DATE']]){const d=node('div');d.append(node('strong',value),node('span',label));$('#timeframe-stats').append(d);}
 $('#timeframe-results').replaceChildren(...rows.map(card));if(!rows.length)$('#timeframe-results').append(node('p',data.selected_documents?'No prepared content briefs match. Enable “Include documents with date evidence only” to inspect the dated source records.':'No reviewed dated documents match these filters. Try another range, dataset or name.','empty-results'));
 if(location.hash.startsWith('#brief-EFTA'))document.getElementById(location.hash.slice(1))?.scrollIntoView({block:'start'});
 }catch(error){if(token===version)$('#timeframe-status').textContent=error.message;}
}
async function init(){try{const response=await fetch('/api/people'),people=await response.json();if(!response.ok)throw new Error('Could not load name filters.');for(let i=1;i<=12;i++){const option=node('option',`Dataset ${i}`);option.value=i;$('#timeframe-dataset').append(option);}for(const p of people.people){const option=node('option',p.label);option.value=p.id;$('#timeframe-person').append(option);}
 for(const [key,id] of [['date_from','timeframe-from'],['date_to','timeframe-to'],['dataset','timeframe-dataset'],['person','timeframe-person']])if(initial.has(key)){const value=initial.get(key);$('#'+id).value=value;if($('#'+id).value!==value)throw new Error('Invalid timeframe filter in the URL. Check dates, dataset and name.');}
 $('#timeframe-date-only').checked=initial.get('date_only')==='1';$('#timeframe-date-only').addEventListener('change',refresh);$('#timeframe-filters').addEventListener('submit',e=>{e.preventDefault();refresh();});await refresh();
 }catch(error){$('#timeframe-status').textContent=error.message;}}
init();
