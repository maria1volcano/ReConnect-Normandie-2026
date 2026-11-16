const {chromium}=require(process.env.PLAYWRIGHT_MODULE_PATH||'playwright-core');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const out=process.env.RECONNECT_UI_QA_DIR||path.join(os.tmpdir(),'reconnect-catalogue-qa');fs.mkdirSync(out,{recursive:true});
const sources=[{kind:'public',base:process.env.RECONNECT_PUBLIC_PREVIEW_URL||'http://127.0.0.1:5187',total:165,families:{A04:60,A01:50,A03:35,A02:20}},{kind:'local',base:process.env.RECONNECT_V2_UI_URL||'http://127.0.0.1:5184',total:205,families:{A04:66,A01:62,A03:35,A02:42}}];
const priority=['Secteur à examiner en priorité','Priorité d’examen élevée','Priorité d’examen modérée','Informations insuffisantes'];
const discover=()=>{const el=document.querySelector('.application-shell');if(!el)return null;const k=Object.keys(el).find(k=>k.startsWith('__reactFiber$'));for(let f=el[k];f;f=f.return)for(let h=f.memoizedState;h&&typeof h==='object';h=h.next){const m=h.memoizedState?.current;if(m&&typeof m.getLayer==='function'&&typeof m.queryRenderedFeatures==='function')return m}return null};
(async()=>{const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_EXECUTABLE_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try{
 const receipt={ok:true,sources:[],javascript_errors:[]};
 for(const source of sources){
  const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage(),api=[];
  page.on('pageerror',e=>receipt.javascript_errors.push(source.kind+': '+e));
  if(source.kind==='public')await context.route('**/api/**',r=>{api.push(r.request().url());return r.abort()});
  await page.goto(source.base+'/catalogue');await page.getByRole('heading',{name:'Catalogue des actions',exact:true}).waitFor();await page.locator('[data-family]').nth(3).waitFor({timeout:60000});
  assert.equal(await page.locator('[data-catalogue-total]').getAttribute('data-catalogue-total'),String(source.total));assert.equal(await page.locator('[data-family]').count(),4);
  assert.deepEqual(await page.locator('.header-nav a').allTextContents(),['Carte','Catalogue des actions','Méthode et sources']);
  const familyCounts={};let allLevels={A:0,B:0,C:0};
  for(const [id,total]of Object.entries(source.families)){
   const card=page.locator(`[data-family="${id}"]`),rows=card.locator('[data-sector-id]');assert.equal(await rows.count(),total);familyCounts[id]=await rows.count();
   assert.equal(await card.locator('.scientific-citations').count(),1);
   if(source.kind==='public')assert.equal(await card.locator('[data-level]').count(),0);
   else for(const level of await card.locator('[data-level]').evaluateAll(els=>els.map(el=>el.dataset.level)))allLevels[level]++;
   // Every link names its own real sector, with a family and source-preserving route.
   const links=await rows.evaluateAll(els=>els.map(el=>({id:el.dataset.sectorId,href:el.getAttribute('href')})));
   for(const link of links){const u=new URL(link.href,source.base);assert.equal(u.pathname,'/');assert.equal(u.searchParams.get('maille'),link.id);assert.equal(u.searchParams.get('famille'),id)}
  }
  if(source.kind==='local')assert.deepEqual(allLevels,{A:93,B:45,C:67});
  const filters=page.getByRole('region',{name:'Filtres du catalogue'});
  await filters.getByRole('button',{name:'Bocage',exact:true}).click();assert.equal(await page.locator('[data-family]').count(),1);assert.equal(await page.locator('[data-catalogue-total]').getAttribute('data-catalogue-total'),String(source.families.A01));
  await page.getByRole('combobox',{name:'Filtrer par commune',exact:true}).selectOption('Hérouville-Saint-Clair');
  await page.getByRole('combobox',{name:'Filtrer par priorité territoriale',exact:true}).selectOption('orange');
  let rows=page.locator('[data-family="A01"] [data-sector-id]'),n=await rows.count();assert.ok(n>0);assert.ok((await rows.allTextContents()).every(t=>t.includes('Hérouville-Saint-Clair')&&t.includes(priority[1])));
  const first=await rows.first().getAttribute('data-sector-id');
  await page.getByRole('link',{name:'Voir les secteurs concernés : Bocage',exact:true}).click();
  await page.locator(`aside[data-maille-id="${first}"]`).waitFor();await page.locator('.journey-catalogue-context').getByText(new RegExp('^'+n+' secteurs correspondent')).waitFor();
  assert.equal(new URL(page.url()).searchParams.get('commune'),'Hérouville-Saint-Clair');assert.equal(new URL(page.url()).searchParams.get('priorite'),'orange');
  assert.equal(await page.locator('#sector-select option').count(),n+1);
  await page.locator('.region-map[aria-busy="false"]').waitFor({timeout:60000});await page.waitForFunction(discover);
  const highlights=await page.evaluate(({d,id})=>{const m=(new Function('return ('+d+')'))()();return m.getFeatureState({source:'real-grid-source',id}).highlighted},{d:discover.toString(),id:first});
  assert.ok(highlights,'La carte souligne les secteurs du catalogue');
  await page.screenshot({path:path.join(out,source.kind+'_map_filtered.png'),fullPage:true});
  await page.getByRole('link',{name:'Retour au catalogue',exact:true}).click();await page.locator('[data-family="A01"]').waitFor();assert.equal(await page.getByRole('combobox',{name:'Filtrer par commune',exact:true}).inputValue(),'Hérouville-Saint-Clair');
  const list=page.locator('[data-family="A01"] .journey-sector-list');await list.locator('summary').click();
  const last=page.locator('[data-family="A01"] [data-sector-id]').last(),lastId=await last.getAttribute('data-sector-id');await last.click();await page.locator(`aside[data-maille-id="${lastId}"]`).waitFor();
  await page.getByRole('link',{name:'Effacer les filtres du catalogue',exact:true}).click();assert.equal(new URL(page.url()).searchParams.has('famille'),false);assert.equal(await page.locator('#sector-select option').count(),102);
  await page.getByRole('link',{name:'Catalogue des actions',exact:true}).click();await page.locator('[data-family]').nth(3).waitFor();
  await page.locator('#catalogue-search').fill('herouville');assert.ok((await page.locator('[data-sector-id]').allTextContents()).every(t=>t.includes('Hérouville-Saint-Clair')));
  await page.locator('#catalogue-search').fill('introuvable');assert.equal(await page.locator('[data-sector-id]').count(),0);assert.equal(await page.getByRole('link',{name:/Voir les secteurs concernés/}).count(),0);assert.equal(await page.locator('[data-catalogue-total]').getAttribute('data-catalogue-total'),'0');
  await page.getByRole('button',{name:'Réinitialiser les filtres',exact:true}).click();assert.equal(await page.locator('[data-catalogue-total]').getAttribute('data-catalogue-total'),String(source.total));
  // Native details stay keyboard-accessible and retain references and scientific conditions.
  const more=page.locator('.journey-family-details').first();await more.locator('summary').first().focus();await page.keyboard.press('Enter');assert.equal(await more.getAttribute('open'),'');await more.locator('.scientific-citations > summary').click();await more.locator('summary').first().click();
  const sizes=[];
  for(const width of [320,390,768,1440]){
   await page.setViewportSize({width,height:1000});await page.evaluate(()=>scrollTo(0,0));
   const geometry=await page.evaluate(()=>{const b=document.querySelector('.brand').getBoundingClientRect(),n=document.querySelector('.header-nav').getBoundingClientRect();return {overflow:document.documentElement.scrollWidth>innerWidth,overlap:!(b.right<=n.left||n.right<=b.left||b.bottom<=n.top||n.bottom<=b.top)}});assert.deepEqual(geometry,{overflow:false,overlap:false});
   await page.locator('.journey-family-details').evaluateAll(els=>els.forEach(el=>el.open=true));await page.locator('.journey-sector-list').evaluateAll(els=>els.forEach(el=>el.open=true));assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   await page.locator('.journey-family-details').evaluateAll(els=>els.forEach(el=>el.open=false));await page.locator('.journey-sector-list').evaluateAll(els=>els.forEach(el=>el.open=false));
   await page.screenshot({path:path.join(out,source.kind+'_catalogue_'+width+'.png'),fullPage:true});
   await page.getByRole('link',{name:'Carte',exact:true}).click();await page.locator('.v2-territorial-legend').waitFor();
   const legend=page.locator('.v2-territorial-legend');assert.deepEqual(await legend.locator('li > span:last-child').allTextContents(),priority);assert.ok(!(await legend.innerText()).includes('Exploratoire'));
   const detail=legend.locator('details'),summary=detail.locator('summary');assert.equal(await detail.getAttribute('open'),null);const compact=(await legend.boundingBox()).height;
   await summary.focus();await page.keyboard.press('Enter');assert.equal(await detail.getAttribute('open'),'');assert.ok((await detail.innerText()).includes('Les niveaux de justification des solutions sont indépendants.'));assert.ok((await detail.innerText()).includes('ne recommande pas de travaux'));
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await legend.screenshot({path:path.join(out,source.kind+'_legend_open_'+width+'.png')});await summary.focus();await page.keyboard.press('Enter');
   await summary.evaluate(el=>el.blur());await legend.screenshot({path:path.join(out,source.kind+'_legend_'+width+'.png')});
   assert.ok(compact<240,'Légende compacte même à '+width);sizes.push({width,height:compact});
   await page.getByRole('link',{name:'Catalogue des actions',exact:true}).click();await page.locator('[data-family]').nth(3).waitFor();
  }
  await page.getByRole('link',{name:'Méthode et sources',exact:true}).click();await page.getByRole('heading',{name:'Méthode et sources',exact:true}).waitFor();await page.locator('.v2-real-example').waitFor();assert.equal(await page.locator('[data-formula-origin]').count(),3);assert.equal(await page.locator('.v2-reference-list a').count(),12);
  const failed=await context.newPage(),blocked=source.kind==='public'?'**/data/caen-6com/cells.json':'**/multiactions-v2/metadata**';
  await failed.route(blocked,r=>r.fulfill({status:503,contentType:'application/json',headers:{'Access-Control-Allow-Origin':new URL(source.base).origin},body:'{"error":"indisponible"}'}));
  await failed.goto(source.base+'/catalogue');await failed.getByRole('alert').filter({hasText:'Le catalogue est indisponible'}).waitFor();assert.equal(await failed.locator('[data-family]').count(),0);
  await failed.unroute(blocked);await failed.getByRole('button',{name:'Réessayer le catalogue',exact:true}).click();await failed.locator('[data-family]').nth(3).waitFor({timeout:60000});assert.equal(await failed.locator('[data-catalogue-total]').getAttribute('data-catalogue-total'),String(source.total));await failed.close();
  assert.deepEqual(api,[]);receipt.sources.push({kind:source.kind,total:source.total,families:familyCounts,levels:source.kind==='local'?allLevels:null,combined_filter_sectors:n,failed_catalogue_retry:true,legend_sizes:sizes,without_backend:source.kind==='public',api_requests:api});
  await context.close();console.log('PASS catalogue navigateur',source.kind,source.total,'pistes ; filtres, carte, liens, méthode et légende compacte.');
 }
 assert.deepEqual(receipt.javascript_errors,[]);fs.writeFileSync(path.join(out,'validation_catalogue.json'),JSON.stringify(receipt,null,2));
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
