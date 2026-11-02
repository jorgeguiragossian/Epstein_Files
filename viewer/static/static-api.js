/* GitHub Pages adapter. This file is included only in the public static build. */
(function(root){
 'use strict';
 const nativeFetch=root.fetch.bind(root);
 const base=new URL('.',document.currentScript.src);
 let bundle;
 const ready=()=>bundle?Promise.resolve(bundle):nativeFetch(new URL('data/pilot.json',base),{cache:'no-cache'}).then(r=>{if(!r.ok)throw new Error('Could not load the published pilot data.');return r.json();}).then(data=>(bundle=data));
 let pending;
 const load=()=>pending||(pending=ready());
 const integer=(value,min,max,label)=>{if(!/^\d+$/.test(String(value)))throw new Error(`${label} must be a whole number.`);const n=Number(value);if(n<min||n>max)throw new Error(`${label} is out of range.`);return n;};
 const day=(value)=>{if(!/^\d{4}-\d{2}-\d{2}$/.test(value)||!Number.isFinite(Date.parse(value+'T00:00:00Z'))||new Date(value+'T00:00:00Z').toISOString().slice(0,10)!==value)throw new Error('Use a real date in YYYY-MM-DD format.');return value;};
 const tokens=text=>(text.normalize('NFD').replace(/\p{M}/gu,'').toLowerCase().match(/[\p{L}\p{N}]+/gu)||[]);
 const words=q=>q.match(/[\p{L}\p{N}_]+/gu)||[];
 function snippet(text,terms){let start=-1;for(const term of terms){const re=new RegExp('(?<![\\p{L}\\p{N}_])'+term.replace(/[.*+?^${}()|[\]\\]/g,'\\$&').replace(/\s+/g,'\\s+')+'(?![\\p{L}\\p{N}_])','iu');const hit=re.exec(text);if(hit&&(start<0||hit.index<start))start=hit.index;}start=Math.max(0,start-75);return(start?'…':'')+text.slice(start,start+300).replace(/\s+/g,' ').trim()+(start+300<text.length?'…':'');}
 function search(data,p){
  const q=(p.get('q')||'').trim(),dataset=p.get('dataset')||'',quality=p.get('quality')||'all',person=p.get('person')||'',status=p.get('date_status')||'all';
  const from=p.get('date_from')||'',to=p.get('date_to')||'',page=integer(p.get('page')||1,1,10000,'Result page');
  if(q.length>200)throw new Error('Keep search text to 200 characters or fewer.');
  if(!['all','review','substantial'].includes(quality))throw new Error('Unknown quality filter.');
  if(!['all','dated','uncertain','undated','unreviewed'].includes(status))throw new Error('Unknown date status.');
  if(from)day(from);if(to)day(to);if(from&&to&&from>to)throw new Error('Start date must be on or before end date.');
  if((from||to)&&!['all','dated'].includes(status))throw new Error('Date ranges apply only to reviewed dates.');
  const set=dataset?integer(dataset,1,12,'Dataset'):null,entry=data.people.people.find(x=>x.id===person);
  if(person&&!entry)throw new Error('Unknown person-name filter.');
  const queryWords=words(q);if(q&&!queryWords.length)throw new Error('Enter at least one word or document ID.');
  const isId=/^EFTA\d{8}$/i.test(q),queryParts=isId?[]:queryWords.map(tokens),rows=[];let totalPages=0;
  for(const doc of Object.values(data.documents).sort((a,b)=>a.dataset-b.dataset||a.id.localeCompare(b.id))){
   if(set&&doc.dataset!==set)continue;if(isId&&doc.id!==q.toUpperCase())continue;
   if(quality==='review'&&!doc.low_text_pages)continue;if(quality==='substantial'&&doc.low_text_pages>=doc.page_count)continue;
   const review=doc.date_review;if(status!=='all'&&review.status!==status)continue;
   if((from||to)&&(review.status!=='dated'||(from&&review.primary_date<from)||(to&&review.primary_date>to)))continue;
   const matches=doc.pages.filter(item=>{
    if(person&&!item.name_mentions.some(x=>x.id===person))return false;
    if(!queryParts.length)return true;
    const list=tokens(item.text),set=new Set(list),sequence='\0'+list.join('\0')+'\0';
    return queryParts.every(part=>part.length===1?set.has(part[0]):sequence.includes('\0'+part.join('\0')+'\0'));
   });
   if(!matches.length)continue;totalPages+=matches.length;
   const row={};for(const key of ['id','dataset','page_count','low_text_pages','bytes','date_count','email_headers'])row[key]=doc[key];
   Object.assign(row,{date_status:review.status,primary_date:review.primary_date,date_type:review.date_type,first_page:matches[0].number,matching_pages:matches.map(x=>x.number),snippet:snippet(matches[0].text,[...(entry?.forms||[]),...(isId?[]:queryWords)])});rows.push(row);
  }
  return{query:q,total_documents:rows.length,total_matching_pages:totalPages,page,page_size:15,results:rows.slice((page-1)*15,page*15)};
 }
 function emails(data,p){
  const filter=p.get('filter')||'all',doc=p.get('document')||'',page=integer(p.get('page')||1,1,10000,'Email result page');
  if(!['all','unresolved','repeats'].includes(filter))throw new Error('Unknown email review filter.');
  if(doc&&!/^EFTA\d{8}$/.test(doc))throw new Error('Invalid email source document ID.');
  const catalog=data.emails,records=new Map(catalog.records.map(r=>[r.id,r])),unresolved=new Set(['sender_address_unresolved','recipient_address_unresolved','date_missing','date_unparsed','date_ambiguous_numeric']);
  const rows=[];
  for(const group of catalog.groups){
   const members=group.record_ids.map(id=>records.get(id));if(doc&&!members.some(r=>r.file_id===doc))continue;
   if(filter==='repeats'&&group.occurrences<2)continue;if(filter==='unresolved'&&!members.some(r=>r.flags.some(f=>unresolved.has(f))))continue;
   rows.push({...group,representative:members.find(r=>r.file_id===doc)||members[0],sources:members.map(r=>({id:r.id,file_id:r.file_id,source_page:r.source_page,source_line:r.source_line,flags:r.flags}))});
  }
  return{summary:catalog.summary,documents:[...new Set(catalog.records.map(r=>r.file_id))].sort(),total_groups:rows.length,page,page_size:12,results:rows.slice((page-1)*12,page*12)};
 }
 function dispatch(data,input){
  const url=new URL(input,'https://static.invalid'),p=url.searchParams;
  if(url.pathname==='/api/overview')return data.overview;
  if(url.pathname==='/api/people')return data.people;
  if(url.pathname==='/api/search')return search(data,p);
  if(url.pathname==='/api/emails')return emails(data,p);
  const match=url.pathname.match(/^\/api\/documents\/(EFTA\d{8})$/);
  if(match){const record=data.documents[match[1]];if(!record){const error=new Error('Document not found.');error.status=404;throw error;}const page=integer(p.get('page')||1,1,record.page_count,'PDF page');const {pages,...meta}=record;return{...meta,page:pages[page-1]};}
  const error=new Error('Not found.');error.status=404;throw error;
 }
 root.PilotStatic={dispatch,search,emails,load,pdfUrl:(id,page)=>{if(!bundle?.documents[id])throw new Error('Unknown source document.');return bundle.documents[id].url+'#page='+page;}};
 root.fetch=async(input,options)=>{
  if(typeof input==='string'&&input.startsWith('/api/')){
   try{return new Response(JSON.stringify(dispatch(await load(),input)),{status:200,headers:{'Content-Type':'application/json'}});}
   catch(error){return new Response(JSON.stringify({error:error.message}),{status:error.status||400,headers:{'Content-Type':'application/json'}});}
  }
  return nativeFetch(input,options);
 };
})(window);
