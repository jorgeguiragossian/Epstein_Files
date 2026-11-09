const $ = (selector) => document.querySelector(selector);
const params = new URL(location.href).searchParams;
const state = { q: params.get('q') || '', dataset: params.get('dataset') || '', quality: params.get('quality') || 'all', resultPage: Number(params.get('rpage')) || 1, selected: '', pdfPage: 1, results: [], matches: [], searchVersion: 0, documentVersion: 0 };
const initialDocument = params.get('doc');
const initialPage = Number(params.get('pdfpage')) || 1;
state.dateFrom = params.get('date_from') || '';
state.dateTo = params.get('date_to') || '';
state.dateStatus = params.get('date_status') || 'all';
state.person=params.get('person')||'';
state.periodFrom=params.get('period_from')||'';
state.periodTo=params.get('period_to')||'';
state.people=[];
const dateLabels = {dated:'Reviewed date',uncertain:'Uncertain date',undated:'Reviewed · undated',unreviewed:'Date not yet reviewed'};
const dateTypes = {email_sent:'Email sent date',report:'Report date',court_order:'Court order date',transcript_session:'Transcript session date',letter:'Letter date',presentation:'Presentation date'};
const format = (number) => Number(number).toLocaleString('en-US');

function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

async function api(path) {
  const response = await fetch(path, { cache: 'no-store' });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || 'The published data could not complete this request.');
  return body;
}

function highlighted(element, text) {
  element.replaceChildren();
  const words = /^EFTA\d{8}$/i.test(state.q.trim()) ? [] : state.q.match(/[\p{L}\p{N}_]+/gu) || [];
  const forms=state.people.find(p=>p.id===state.person)?.forms||[];
  const terms=[...forms,...words];
  if (!terms.length) {
    element.textContent = text;
    return;
  }
  const alternatives = terms.map((word) => word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/\s+/g,'\\s+')).join('|');
  const pattern = new RegExp(`(?<![\\p{L}\\p{N}_])(?:${alternatives})(?![\\p{L}\\p{N}_])`, 'giu');
  let index = 0;
  for (const match of text.matchAll(pattern)) {
    element.append(document.createTextNode(text.slice(index, match.index)), node('mark', '', match[0]));
    index = match.index + match[0].length;
  }
  element.append(document.createTextNode(text.slice(index)));
}

function updateLocation() {
  const url = new URL(location.href);
  url.search = '';
  if (state.q) url.searchParams.set('q', state.q);
  if (state.dataset) url.searchParams.set('dataset', state.dataset);
  if (state.quality !== 'all') url.searchParams.set('quality', state.quality);
  if (state.dateFrom) url.searchParams.set('date_from',state.dateFrom);
  if (state.dateTo) url.searchParams.set('date_to',state.dateTo);
  if (state.dateStatus !== 'all') url.searchParams.set('date_status',state.dateStatus);
  if(state.person) url.searchParams.set('person',state.person);
  if(state.periodFrom)url.searchParams.set('period_from',state.periodFrom);
  if(state.periodTo)url.searchParams.set('period_to',state.periodTo);
  if (state.resultPage > 1) url.searchParams.set('rpage', state.resultPage);
  if (state.selected) {
    url.searchParams.set('doc', state.selected);
    url.searchParams.set('pdfpage', state.pdfPage);
  }
  history.replaceState(null, '', url);
}

function updateDatasetButtons() {
  for (const button of document.querySelectorAll('[data-dataset]')) {
    const selected = button.dataset.dataset === state.dataset;
    button.classList.toggle('active', selected);
    button.setAttribute('aria-pressed', String(selected));
  }
}

function clearReader() {
  state.selected = '';
  state.matches = [];
  state.documentVersion += 1;
  $('#reader').hidden = true;
  $('#empty-reader').hidden = false;
}

function renderResults() {
  $('#results').replaceChildren();
  for (const result of state.results) {
    const button = node('button', 'result');
    button.type = 'button';
    button.classList.toggle('selected', state.selected === result.id);
    button.setAttribute('aria-pressed', String(state.selected === result.id));
    button.setAttribute('aria-label', `Read ${result.id}, dataset ${result.dataset}, ${result.page_count} PDF pages`);
    const head = node('span', 'result-head');
    head.append(node('span', 'result-id', result.id), node('span', 'result-arrow', '↗'));
    const meta = node('span', 'result-meta');
    meta.append(node('span', '', `DATASET ${String(result.dataset).padStart(2, '0')}`), node('span', '', '·'), node('span', '', `${result.page_count} PDF ${result.page_count === 1 ? 'page' : 'pages'}`));
    const excerpt = node('span', 'result-snippet');
    highlighted(excerpt, result.snippet || 'Little text was extracted. Open the PDF to inspect this document.');
    const badges = node('span', 'badges');
    badges.append(node('span','badge date-badge',result.primary_date ? `${result.primary_date} · ${dateTypes[result.date_type]}` : dateLabels[result.date_status]));
    if (result.low_text_pages) badges.append(node('span', 'badge review', `${result.low_text_pages} low-text ${result.low_text_pages === 1 ? 'page' : 'pages'}`));
    if (result.email_headers) badges.append(node('span', 'badge', `${result.email_headers} email header ${result.email_headers === 1 ? 'candidate' : 'candidates'}`));
    if (state.q||state.person) badges.append(node('span', 'badge', `${result.matching_pages.length} matching ${result.matching_pages.length === 1 ? 'page' : 'pages'}`));
    button.append(head, meta, excerpt, badges);
    button.addEventListener('click', () => {
      state.matches = state.q||state.person ? result.matching_pages : [];
      openDocument(result.id, result.first_page, true);
    });
    $('#results').append(button);
  }
}

async function search({ resetPage = true, keepReader = false } = {}) {
  const version = ++state.searchVersion;
  if (resetPage) state.resultPage = 1;
  if (!keepReader) clearReader();
  state.q = $('#search').value.trim();
  state.quality = $('#quality').value;
  state.dateFrom = $('#date-from').value;
  state.dateTo = $('#date-to').value;
  state.dateStatus = $('#date-status').value;
  state.person=$('#person').value;
  state.periodFrom=$('#period-from').value;
  state.periodTo=$('#period-to').value;
  const selectedPerson=state.people.find(p=>p.id===state.person);
  $('#person-scope').textContent=selectedPerson ? `${selectedPerson.label}: ${selectedPerson.documents} ${selectedPerson.documents===1?'document':'documents'} / ${selectedPerson.pages} ${selectedPerson.pages===1?'page':'pages'} across the full pilot. Text mentions are not verified identities or relationships.` : `${state.people.length} curated names, not a complete person index. Full-name text matches do not establish identity, a relationship, or wrongdoing.`;
  updateDatasetButtons();
  updateLocation();
  $('#results-status').classList.remove('error');
  $('#results-status').textContent = 'Searching the published pilot…';
  $('#results').setAttribute('aria-busy', 'true');
  $('#prev-results').disabled = true;
  $('#next-results').disabled = true;
  try {
    const query = new URLSearchParams({ q: state.q, dataset: state.dataset, quality: state.quality, page: state.resultPage, date_from:state.dateFrom,date_to:state.dateTo,date_status:state.dateStatus,person:state.person,period_from:state.periodFrom,period_to:state.periodTo });
    const result = await api(`/api/search?${query}`);
    if (version !== state.searchVersion) return;
    state.results = result.results;
    renderResults();
    $('#results-title').textContent = selectedPerson ? `Mentions: ${selectedPerson.label}` : state.q ? 'Search results' : state.dataset ? `Dataset ${String(state.dataset).padStart(2, '0')}` : 'Pilot documents';
    $('#results-status').textContent = `${format(result.total_documents)} ${result.total_documents === 1 ? 'document' : 'documents'}${state.q||state.person ? ` · ${format(result.total_matching_pages)} matching ${result.total_matching_pages===1?'page':'pages'}` : ' in the pilot sample'} · ordered by dataset and file ID`;
    if(state.periodFrom||state.periodTo)$('#results-status').textContent+=' · reviewed reporting-period overlap';
    $('#reset').hidden = !state.q && !state.dataset && !state.person && state.quality === 'all' && !state.dateFrom && !state.dateTo && !state.periodFrom && !state.periodTo && state.dateStatus==='all';
    const maxPage = Math.max(1, Math.ceil(result.total_documents / result.page_size));
    $('#result-page').textContent = `Page ${state.resultPage} of ${maxPage}`;
    $('#prev-results').disabled = state.resultPage <= 1;
    $('#next-results').disabled = state.resultPage >= maxPage;
    if (!result.results.length) {
      const empty = node('div', 'empty-results');
      empty.append(node('h3', '', 'No documents found.'), node('p', '', 'Try fewer words or a different dataset. This pilot covers a small sample; missing results do not establish that a person or topic is absent from the full collection.'));
      $('#results').append(empty);
    }
  } catch (error) {
    if (version !== state.searchVersion) return;
    $('#results').replaceChildren();
    $('#results-status').textContent = error.message;
    $('#results-status').classList.add('error');
    $('#result-page').textContent = '';
  } finally {
    if (version === state.searchVersion) $('#results').removeAttribute('aria-busy');
  }
}

function sourceDetail(label, text) {
  $('#source-details').append(node('dt', '', label), node('dd', '', text));
}

async function openDocument(id, page, focus = false) {
  const version = ++state.documentVersion;
  state.selected = id;
  state.pdfPage = page;
  updateLocation();
  renderResults();
  $('#empty-reader').hidden = true;
  $('#reader').hidden = false;
  $('#reader-title').textContent = id;
  $('#reader-dataset').textContent = 'LOADING DOCUMENT';
  $('#page-text').textContent = 'Loading page text…';
  $('#pdf-link').removeAttribute('href');
  $('#doj-link').removeAttribute('href');
  $('#prev-page').disabled = true;
  $('#next-page').disabled = true;
  $('#page-warning').hidden = true;
  $('#matching-pages').hidden = true;
  $('#date-list').replaceChildren();
  $('#source-details').replaceChildren();
  $('#primary-date').replaceChildren();
  $('#source-quality').replaceChildren();
  $('#source-quality').hidden=true;
  $('#page-people').replaceChildren();
  try {
    const record = await api(`/api/documents/${encodeURIComponent(id)}?page=${page}`);
    if (version !== state.documentVersion) return;
    $('#reader-dataset').textContent = `DATASET ${String(record.dataset).padStart(2, '0')} / SOURCE DOCUMENT`;
    $('#pdf-link').href = window.PilotStatic.pdfUrl(id,page);
    $('#pdf-link').textContent = `DOJ PDF · page ${page} ↗`;
    $('#doj-link').href = `${record.url}#page=${page}`;
    $('#page-number').value = page;
    $('#page-number').max = record.page_count;
    $('#page-total').textContent = `of ${record.page_count}`;
    $('#prev-page').disabled = page <= 1;
    $('#next-page').disabled = page >= record.page_count;
    $('#page-warning').hidden = !record.page.low_text;
    highlighted($('#page-text'), record.page.text || 'No text was extracted from this page. Inspect the original PDF.');
    $('#page-text').scrollTop = 0;
    const firstHighlight=$('#page-text mark');
    if(firstHighlight) $('#page-text').scrollTop=Math.max(0,firstHighlight.getBoundingClientRect().top-$('#page-text').getBoundingClientRect().top-60);
    for(const mention of record.page.name_mentions) {
      const item=node('p','name-mention',`${mention.label} · ${mention.occurrences} text ${mention.occurrences===1?'occurrence':'occurrences'}`);
      const entry=state.people.find(p=>p.id===mention.id);
      if(entry) {
        const link=node('button','text-button','View name-list source ↗');
        link.type='button';
        link.addEventListener('click',()=>{state.matches=[];openDocument(entry.evidence.file_id,entry.evidence.pdf_page);});
        item.append(document.createTextNode(' '),link);
      }
      $('#page-people').append(item);
    }
    if(!record.page.name_mentions.length) $('#page-people').append(node('p','evidence-note','No names from the curated list matched this page. This does not establish that no people are named here.'));
    $('#reader-status').textContent = `Loaded ${id}, PDF page ${page} of ${record.page_count}.`;
    const matches = $('#matching-pages');
    matches.replaceChildren(document.createTextNode('Matching PDF pages: '));
    // Render a bounded set of match links, retaining navigation to every PDF page.
    const shown = state.matches.slice(0, 30);
    for (const number of shown) {
      const button = node('button', number === page ? 'current' : '', String(number));
      button.type = 'button';
      button.setAttribute('aria-label', `Read matching PDF page ${number}`);
      button.addEventListener('click', () => openDocument(id, number));
      matches.append(button);
    }
    if (state.matches.length > shown.length) matches.append(document.createTextNode(` + ${state.matches.length - shown.length} more; use page navigation`));
    matches.hidden = !state.matches.length;
    const dateKeys = new Set();
    for (const candidate of record.page.date_candidates) {
      const key = `${candidate.line}:${candidate.raw}`;
      if (dateKeys.has(key)) continue;
      dateKeys.add(key);
      $('#date-list').append(node('li', '', `${candidate.raw} · extracted line ${candidate.line} · unverified mention`));
    }
    if (!dateKeys.size) $('#date-list').append(node('li', '', 'No date strings detected on this page.'));
    const review = record.date_review;
    const primary = $('#primary-date');
    primary.append(node('strong','',review.primary_date ? `${review.primary_date} · ${dateTypes[review.date_type]}` : dateLabels[review.status]));
    primary.append(node('p','',review.notes));
    if (review.evidence_page) {
      const evidence = node('button','text-button',`View date evidence · PDF page ${review.evidence_page} ↗`);
      evidence.type='button';
      evidence.addEventListener('click',()=>openDocument(id,review.evidence_page));
      primary.append(evidence);
      sourceDetail('Date evidence',`PDF page ${review.evidence_page}: ${review.evidence_quote}`);
    }
    sourceDetail('Primary date', review.primary_date ? `${review.primary_date} (${dateTypes[review.date_type]}; reviewed assignment)` : dateLabels[review.status]);
    for (const supporting of review.supporting_evidence || []) {
      const evidence=node('button','text-button',`View supporting date evidence · PDF page ${supporting.pdf_page} ↗`);
      evidence.type='button';
      evidence.addEventListener('click',()=>openDocument(id,supporting.pdf_page));
      primary.append(evidence);
      sourceDetail('Supporting date evidence',`PDF page ${supporting.pdf_page}: ${supporting.quote}`);
    }
    sourceDetail('Text coverage', `${record.page_count} of ${record.page_count} pages processed; ${record.low_text_pages} flagged low-text`);
    if(record.source_quality_review){
      const quality=record.source_quality_review,panel=$('#source-quality');
      panel.className='email-notice';panel.hidden=false;
      panel.append(node('h3','','Source quality review'),node('p','',quality.notes),
        node('p','evidence-note',quality.review_scope?'Editorial source comparison by Codex; not independent authentication or full-content review. Native text is preserved.':'Editorial source comparison by Codex, not cell-by-cell financial verification. Native text is preserved. Date-role observations below do not control primary-date filters.'));
      if(quality.review_scope)panel.append(node('p','evidence-note',quality.review_scope));
      if(quality.component_assessment){
        const assessment=quality.component_assessment;
        panel.append(node('h4','','Compound file: bounded assessment'),node('p','',assessment.review_scope));
        for(const finding of assessment.findings)panel.append(node('p','',`PDF pages ${finding.pdf_pages.join(', ')}: ${finding.finding}`));
        for(const start of assessment.component_start_observations){const b=node('button','text-button',`Observed ${start.kind.replaceAll('_',' ')}: PDF page ${start.pdf_page}`);b.type='button';b.addEventListener('click',()=>openDocument(id,start.pdf_page));panel.append(b);}
        panel.append(node('p','evidence-note','Observed starts are not complete component segmentation. No primary date or verified legal status is assigned.'));
      }
      const roles={application_signature_date:'Application signature date',court_order_signature_date:'Court order signature date',form_version_marker:'Form / version marker',document_year:'Document year',preliminary_print_timestamp:'Preliminary print timestamp',planned_settlement_date:'Planned settlement date',statement_reporting_period:'Statement reporting period',portfolio_as_of_date:'Portfolio as-of date',transaction_reporting_period:'Transaction reporting period',handwritten_date_unresolved:'Handwritten date · unresolved'};
      const details=node('details','evidence');details.append(node('summary','',`Date roles & source evidence (${quality.date_observations.length})`));
      for(const observation of quality.date_observations){
        const section=node('div','');
        const reading=observation.period_start?`${observation.period_start} through ${observation.period_end}`:observation.normalized_day||observation.source_year||'No primary-date assignment';
        section.append(node('h4','',`${roles[observation.role]||observation.role} · ${reading}`));
        if(observation.note)section.append(node('p','',observation.note));
        section.append(node('blockquote','',observation.native_quote));
        const button=node('button','text-button',`View role evidence · PDF page ${observation.pdf_page} ↗`);button.type='button';
        button.addEventListener('click',()=>openDocument(id,observation.pdf_page));section.append(button);details.append(section);
      }
      if(quality.date_observations.length)panel.append(details);
    }
    sourceDetail('Email headers', `${record.email_headers} unverified candidates in this file; not unique messages or contacts`);
    sourceDetail('File size', `${(record.bytes / 1048576).toFixed(2)} MiB`);
    sourceDetail('SHA-256', record.sha256);
    if (focus) {
      $('#reader-title').focus({ preventScroll: true });
      if (matchMedia('(max-width: 850px)').matches) $('.inspector').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  } catch (error) {
    if (version !== state.documentVersion) return;
    $('#reader-dataset').textContent = 'DOCUMENT UNAVAILABLE';
    $('#page-text').textContent = error.message;
    $('#reader-status').textContent = error.message;
  }
}

async function init() {
  $('#search').value = state.q;
  $('#quality').value = ['all', 'review', 'substantial'].includes(state.quality) ? state.quality : 'all';
  $('#date-status').value=['all','dated','uncertain','undated','unreviewed'].includes(state.dateStatus) ? state.dateStatus : 'all';
  $('#date-from').value=state.dateFrom;
  $('#date-to').value=state.dateTo;
  $('#period-from').value=state.periodFrom;
  $('#period-to').value=state.periodTo;
  if(state.periodFrom||state.periodTo)$('#period-from').closest('details').open=true;
  $('#period-from').addEventListener('change',()=>search());
  $('#period-to').addEventListener('change',()=>search());
  $('#clear-periods').addEventListener('click',()=>{$('#period-from').value='';$('#period-to').value='';search();});
  function syncDates() {
    const disabled=!['all','dated'].includes($('#date-status').value);
    $('#date-from').disabled=disabled;
    $('#date-to').disabled=disabled;
    if(disabled) {$('#date-from').value='';$('#date-to').value='';}
  }
  syncDates();
  $('#date-status').addEventListener('change',()=>{syncDates();search();});
  $('#date-from').addEventListener('change',()=>search());
  $('#date-to').addEventListener('change',()=>search());
  $('#clear-dates').addEventListener('click',()=>{
    $('#date-status').value='all';$('#date-from').value='';$('#date-to').value='';syncDates();search();
  });
  $('#all-datasets').dataset.dataset = '';
  $('#all-datasets').addEventListener('click', () => { state.dataset = ''; search(); });
  $('#search-form').addEventListener('submit', (event) => { event.preventDefault(); search(); });
  $('#quality').addEventListener('change', () => search());
  $('#person').addEventListener('change',()=>search());
  $('#reset').addEventListener('click', () => {
    state.dataset = '';
    $('#search').value = '';
    $('#quality').value = 'all';
    $('#person').value='';
    $('#period-from').value='';$('#period-to').value='';
    $('#date-status').value='all';$('#date-from').value='';$('#date-to').value='';syncDates();
    search();
  });
  $('#prev-results').addEventListener('click', () => { state.resultPage -= 1; search({ resetPage: false }); });
  $('#next-results').addEventListener('click', () => { state.resultPage += 1; search({ resetPage: false }); });
  $('#prev-page').addEventListener('click', () => openDocument(state.selected, state.pdfPage - 1));
  $('#next-page').addEventListener('click', () => openDocument(state.selected, state.pdfPage + 1));
  $('#page-form').addEventListener('submit', (event) => {
    event.preventDefault();
    const input = $('#page-number');
    if (input.reportValidity()) openDocument(state.selected, Number(input.value));
  });
  try {
    const [overview,vocabulary]=await Promise.all([api('/api/overview'),api('/api/people')]);
    state.people=vocabulary.people;
    for(const person of state.people) {
      const option=node('option','',`${person.label} (${person.documents} pilot ${person.documents===1?'document':'documents'})`);
      option.value=person.id;$('#person').append(option);
    }
    if(state.person&&!state.people.some(p=>p.id===state.person)) throw new Error('Unknown person-name filter in URL. Remove the person parameter to continue.');
    $('#person').value=state.person;
    $('#stat-docs').textContent = format(overview.documents);
    $('#stat-pages').textContent = format(overview.pages);
    $('#stat-datasets').textContent = overview.datasets.length;
    $('#stat-review').textContent = format(overview.low_text_pages);
    $('#all-count').textContent = overview.documents;
    const counts=overview.date_status_counts;
    $('#date-coverage').textContent=`${counts.dated||0} reviewed dates · ${counts.uncertain||0} uncertain · ${counts.undated||0} reviewed undated · ${counts.unreviewed||0} not yet reviewed. Ranges include reviewed dates only, with inclusive endpoints; dates mentioned in the body do not control the filter.`;
    for(const option of $('#date-status').options) {
      if(option.value!=='all') option.textContent=`${dateLabels[option.value]} (${counts[option.value]||0})`;
    }
    for (const dataset of overview.datasets) {
      const button = node('button', 'dataset');
      button.type = 'button';
      button.dataset.dataset = String(dataset.dataset);
      button.append(node('span', 'dataset-number', String(dataset.dataset).padStart(2, '0')), node('span', '', `Dataset ${dataset.dataset}`), node('span', 'count', dataset.documents));
      button.addEventListener('click', () => { state.dataset = String(dataset.dataset); search(); });
      $('#datasets').append(button);
    }
    await search({ resetPage: false, keepReader: true });
    if (initialDocument) {
      const result = state.results.find((r) => r.id === initialDocument);
      state.matches = (state.q||state.person) && result ? result.matching_pages : [];
      await openDocument(initialDocument, initialPage);
    }
  } catch (error) {
    $('#results-status').textContent = `Cannot load the published pilot: ${error.message}`;
    $('#results-status').classList.add('error');
  }
}

init();
