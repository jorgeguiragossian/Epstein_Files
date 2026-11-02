import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
const data=JSON.parse(fs.readFileSync('site-dist/data/pilot.json','utf8'));
const golden=JSON.parse(fs.readFileSync('tmp/pages-golden.json','utf8'));
const context={window:{fetch:async()=>new Response(JSON.stringify(data))},document:{currentScript:{src:'http://localhost/Epstein_Files/static-api.js'}},URL,Response,console};
vm.createContext(context);
vm.runInContext(fs.readFileSync('viewer/static/static-api.js','utf8'),context);
const api=context.window.PilotStatic;
for(const item of golden){
 const actual=JSON.parse(JSON.stringify(api.dispatch(data,item.path)));
 if(item.path.startsWith('/api/search')){
  const clean=x=>({total_documents:x.total_documents,total_matching_pages:x.total_matching_pages,results:x.results.map(r=>({id:r.id,matching_pages:r.matching_pages,first_page:r.first_page,date_status:r.date_status,primary_date:r.primary_date}))});
  assert.deepEqual(clean(actual),clean(item.result),item.path);
 }else assert.deepEqual(actual,item.result,item.path);
}
for(const path of ['/api/search?date_from=2021-02-29','/api/search?person=unknown','/api/search?q=***','/api/emails?filter=bad','/api/documents/EFTA00008529?page=0'])assert.throws(()=>api.dispatch(data,path),path);
await api.load();
assert.equal(api.pdfUrl('EFTA00008529',2),data.documents.EFTA00008529.url+'#page=2');
for(const name of ['index.html','emails.html']){
 const html=fs.readFileSync('site-dist/'+name,'utf8');
 const digest=createHash('sha256').update(fs.readFileSync('site-dist/static-api.js')).digest('hex').slice(0,12);
 assert(html.includes(`src="/Epstein_Files/static-api.js?v=${digest}"`));
 assert(!/\b(?:href|src)="\/(?!Epstein_Files\/)/.test(html),name+' has a broken project-root link');
}
assert(!fs.readFileSync('site-dist/app.js','utf8').includes('`/pdf/'));
assert(!fs.readFileSync('site-dist/emails.js','utf8').includes('`/?doc='));
assert(!fs.readFileSync('site-dist/emails.js','utf8').includes('`/pdf/'));
console.log(`Static Pages checks passed: ${golden.length} Python/browser-adapter comparisons, invalid inputs, DOJ PDF links, and project subpaths.`);
