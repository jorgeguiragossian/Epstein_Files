const $=s=>document.querySelector(s);
const params=new URL(location.href).searchParams;
let currentPage=Number(params.get('page'))||1,version=0;
const kinds={single_occurrence:'Single source occurrence',exact_visible_copies:'Exact visible copies · unverified',possible_repeat_incomplete:'Possible repeat · incomplete headers'};
const spanKinds={uncertain_header_continuation:'Uncertain header continuation',authored_text_candidate:'Authored text candidate',signature:'Signature / device footer',inline_quote:'Inline quotation',forwarded_quote:'Forwarded quotation',inline_quote_header_only:'Quoted header · body not established',forwarding_wrapper:'Forwarding wrapper · no authored body established',disclaimer:'Disclaimer / boilerplate · attribution uncertain'};
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
 card.append(head,title,headers,flags,sources);
 if(r.source_review){
  const review=r.source_review,panel=node('section','email-notice');
  panel.append(node('h4','','Source-assisted editorial review by Codex'),node('p','',review.boundary_status.replaceAll('_',' ')),node('p','',review.notes));
  if(review.source_day_reading)panel.append(node('p','',`Source date reading: ${review.source_day_reading}`));
  if(review.parsed_clock_conflict)panel.append(node('p','email-flags',`Timestamp discrepancy: the PDF reads ${review.source_clock_reading}; the parsed candidate above lost the PM marker. Use the source reading pending parser correction. Timezone is not inferred.`));
  else if(review.source_clock_matches_candidate)panel.append(node('p','evidence-note',`Clock check: parsed candidate now matches the PDF reading of ${review.source_clock_reading}. Timezone is not inferred.`));
  for(const pair of r.reviewed_address_associations||[]){
   panel.append(node('p','',`${pair.field.toUpperCase()} header reading: ${pair.display_name} <${pair.address}>${pair.visual_correction?' · extraction correction from PDF':''}`));
  }
  panel.append(node('p','evidence-note','Observed header associations do not establish account ownership. Raw extraction is preserved below. This review does not verify a unique message or enable contact counts.'));
  card.append(panel);
 }
 if(r.continuation_review){
  const check=r.continuation_review,section=node('section','email-notice');
  section.append(node('h4','','Adjacent-page source check'),node('p','',check.notes),link(`Inspect PDF page ${check.next_page} · lines ${check.line_start}–${check.line_end}`,`/Epstein_Files/?doc=${encodeURIComponent(r.file_id)}&pdfpage=${check.next_page}`),node('p','evidence-note','Editorial review by Codex. No text is joined across these pages. The original body remains incomplete; no missing content is reconstructed.'));
  card.append(section);
 }
 if(r.body_partition){
  const breakdown=node('section','body-partition');
  breakdown.append(node('h4','','Source-linked body breakdown'),node('p','evidence-note','Editorial boundaries by Codex. These spans preserve the detected body; they are not independently verified messages. Contact counts and original grouping remain unchanged.'));
  for(const span of r.body_partition.spans){
   const section=node('div','body-span');
   section.append(node('h4','',spanKinds[span.kind]),link(`PDF page ${span.page} · lines ${span.line_start}–${span.line_end}`,`/Epstein_Files/?doc=${encodeURIComponent(r.file_id)}&pdfpage=${span.page}`),node('pre','email-raw',span.text));
   breakdown.append(section);
  }
  const child=r.body_partition.following_quoted_source;
  if(child){
   const continuation=node('p','evidence-note','Following quoted/forwarded candidate already indexed: ');
   continuation.append(link(`${child.file_id} · PDF page ${child.source_page} · line ${child.source_line}`,`/Epstein_Files/?doc=${encodeURIComponent(child.file_id)}&pdfpage=${child.source_page}`));
   breakdown.append(continuation);
  }
  card.append(breakdown);
 }
 card.append(raw);return card;
}
async function refresh(reset=true){
 if(reset)currentPage=1;const token=++version;
 const filter=$('#email-filter').value,doc=$('#email-document').value;
 const url=new URL(location.href);url.search='';if(filter!=='all')url.searchParams.set('filter',filter);if(doc)url.searchParams.set('document',doc);if(currentPage>1)url.searchParams.set('page',currentPage);history.replaceState(null,'',url);
 $('#email-status').textContent='Loading published review groups…';$('#email-prev').disabled=true;$('#email-next').disabled=true;
 try{
  const response=await fetch(`/api/emails?${new URLSearchParams({filter,document:doc,page:currentPage})}`,{cache:'no-store'});const data=await response.json();if(!response.ok)throw new Error(data.error||'Could not read the published email cache.');if(token!==version)return;
  const summary=data.summary;$('#email-occurrences').textContent=summary.candidate_occurrences;$('#email-documents').textContent=summary.documents_with_candidates;$('#email-repeats').textContent=summary.repeat_groups;
  const reviewed=summary.source_review;
  const partitions=summary.body_partitions;
  $('#email-review-coverage').textContent=reviewed?`${reviewed.reviewed_candidates} candidates source-reviewed · ${reviewed.boundary_attention} flagged boundary cases${partitions?`, ${partitions.annotated_candidates} with source-linked breakdowns and ${partitions.adjacent_page_checks||0} adjacent-page checks`:''} · ${reviewed.observed_address_associations} observed name/address associations. This purposive sample is not an accuracy estimate.`:'Source review pending.';
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
 $('#email-filter').value=['all','unresolved','repeats','reviewed','boundary'].includes(params.get('filter'))?params.get('filter'):'all';
 if(params.get('document')){const option=node('option','',params.get('document'));option.value=params.get('document');$('#email-document').append(option);$('#email-document').value=option.value;}
 $('#email-filters').addEventListener('submit',e=>{e.preventDefault();refresh();});$('#email-prev').addEventListener('click',()=>{currentPage--;refresh(false);});$('#email-next').addEventListener('click',()=>{currentPage++;refresh(false);});await refresh(false);
}
init();
