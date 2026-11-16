const {chromium}=require(process.env.PLAYWRIGHT_MODULE_PATH || 'playwright-core');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const base=process.env.RECONNECT_V2_UI_URL || 'http://127.0.0.1:5184',api=process.env.RECONNECT_V2_API_URL || 'http://127.0.0.1:8768';
const out=process.env.RECONNECT_UI_QA_DIR || path.join(os.tmpdir(),'reconnect_final_20261115');fs.mkdirSync(out,{recursive:true});
const discover=()=>{const el=document.querySelector('.application-shell');if(!el)return null;const k=Object.keys(el).find(k=>k.startsWith('__reactFiber$'));for(let f=el[k];f;f=f.return)for(let h=f.memoizedState;h&&typeof h==='object';h=h.next){const m=h.memoizedState?.current;if(m&&typeof m.project==='function'&&typeof m.queryRenderedFeatures==='function')return m}return null};
const scope=new URLSearchParams({territory_id:'caen_et_nord_6communes',grid_version:'M1-CAEN-6COM-1KM2-FLAT-L93-O0-V1',dataset_version:'M1-CAEN-ET-NORD-20261111-V1',decision_version:'m2.multiactions.experimental-2.0'}).toString();
const jargon=/\b(?:XY|D\/S|SRCE|R[1-4]|A0[1-4]|SHA-?256|non_evaluable|conflit_id)\b|référence\(s\)|NORM-G1K/u;
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROME_EXECUTABLE_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--disable-background-networking','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage(),errors=[],external=[],tileResponses=[];
  await context.route('**/*',r=>{const u=new URL(r.request().url());if(['http:','https:'].includes(u.protocol)&&!['127.0.0.1','localhost','tile.openstreetmap.org'].includes(u.hostname)){external.push(u.origin);return r.abort()}return r.continue()});
  page.on('pageerror',e=>errors.push(String(e)));page.on('response',r=>{if(new URL(r.url()).hostname==='tile.openstreetmap.org')tileResponses.push({status:r.status(),url:r.url()})});
  const get=async route=>{const r=await page.request.get(api+'/api/internal/caen/multiactions-v2/'+route+'?'+scope);assert.equal(r.status(),200);return r.json()};
  const grid=await get('grid'),method=await get('methodology'),cells=[];
  for(let i=0;i<101;i+=4)cells.push(...await Promise.all(grid.features.slice(i,i+4).map(f=>get('cells/'+encodeURIComponent(f.properties.maille_id)))));
  await page.goto(base);await page.getByRole('heading',{name:'Où étudier les continuités écologiques ?',exact:true}).waitFor();
  await page.locator('.region-map[aria-busy="false"]').waitFor({timeout:60000});await page.waitForFunction(discover);
  const mappaint=await page.evaluate(discover=>{const m=(new Function('return ('+discover+')'))()();return {fill:m.getPaintProperty('real-grid-fill','fill-color'),opacity:m.getPaintProperty('real-grid-fill','fill-opacity')}},discover.toString());
  assert.deepEqual(mappaint.fill,['get','study_color']);assert.ok(JSON.stringify(mappaint.opacity).includes('0.3'));
  assert.equal(await page.locator('.map-canvas').count(),1);assert.equal(await page.locator('.classification-switcher').count(),0);
  await page.getByText('Secteur à examiner en priorité',{exact:true}).first().waitFor();assert.equal(await page.locator('.v2-examples').count(),0);assert.equal(await page.getByRole('button',{name:'Plusieurs pistes à Caen',exact:true}).count(),0);
  await page.getByText('Territoire pilote : Caen et cinq communes voisines',{exact:true}).waitFor();
  const colors={rouge:0,orange:0,jaune:0,gris:0},rendered={cells:0,actions:0,empty:0,four:0,A:0,B:0,C:0};
  for(const cell of cells){
   await page.locator('#sector-select').selectOption(cell.maille_id);const panel=page.locator(`aside[data-maille-id="${cell.maille_id}"]`);await panel.waitFor();
   const feature=grid.features.find(f=>f.properties.maille_id===cell.maille_id);assert.deepEqual(feature.properties.territorial_priority,cell.territorial_priority);
   assert.equal(await panel.locator('h2').innerText(),cell.municipalities.join(' / '));assert.ok((await page.locator('#sector-select option:checked').innerText()).includes(cell.municipalities[0]));
   const swatch=await panel.locator('.v2-territorial-status .v2-priority-swatch').evaluate(el=>el.style.backgroundColor);
   const hex=cell.territorial_priority.color_hex;const rgb='rgb('+[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)).join(', ')+')';assert.equal(swatch,rgb);
   colors[cell.territorial_priority.color]++;rendered.cells++;rendered.empty+=!cell.actions.length;rendered.four+=cell.actions.length===4;
   assert.deepEqual(await panel.locator('.v2-action').evaluateAll(cards=>cards.map(c=>({id:c.dataset.actionId,level:c.dataset.level}))),cell.actions.map(a=>({id:a.action_id,level:a.level})));
   for(const a of cell.actions){rendered.actions++;rendered[a.level]++}
   const contents=await panel.locator('.v2-action').evaluateAll(cards=>cards.map(card=>{
    const details=card.querySelector('.v2-action-more');details.open=true;
    const result={why:card.querySelector('.v2-action-why p').innerText,solution:card.querySelector('.v2-action-solution p').innerText,text:details.innerText,indicators:details.querySelectorAll('.v2-local-indicators dd').length,checks:details.querySelectorAll('ul > li').length,limits:details.querySelectorAll('.v2-specific-limit').length};details.open=false;return result;
   }));
   for(const copy of contents){assert.ok(copy.why.length>80&&copy.solution.length>60);assert.ok(copy.indicators>=1&&copy.indicators<=2);assert.equal(copy.checks,3);assert.equal(copy.limits,1);assert.ok(!jargon.test(copy.why+' '+copy.solution+' '+copy.text))}
   assert.equal(await panel.locator('.v2-linked').count(),Number(cell.comparisons.some(c=>c.observations_liees)));assert.equal(await panel.locator('.v2-reserve').count(),1);assert.equal(await panel.locator('pre').count(),0);
   if(!cell.actions.length)await panel.getByRole('heading',{name:'Aucune piste territorialisée retenue'}).waitFor();
  }
  assert.deepEqual(colors,{rouge:27,orange:33,jaune:9,gris:32});assert.deepEqual(rendered,{cells:101,actions:205,empty:13,four:15,A:93,B:45,C:67});
  const contrasts=await page.locator('.v2-priority-swatch').evaluateAll(els=>{
   const lum=c=>c.match(/[\d.]+/g).slice(0,3).map(Number).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0);
   return els.map(el=>{const c=getComputedStyle(el),a=lum(c.color),b=lum(c.backgroundColor);return(Math.max(a,b)+.05)/(Math.min(a,b)+.05)});
  });assert.ok(Math.min(...contrasts)>=4.5,'Repères numérotés lisibles sur toutes les couleurs');
  console.log('PASS navigateur : 101 mailles, 205 cartes, 15 secteurs à quatre pistes, 13 sans proposition et couleurs 27/33/9/32.');
  // Search is a filter of the same selector, including accent-insensitive municipality names.
  await page.locator('#sector-search').fill('herouville');const results=await page.locator('#sector-select option').allTextContents();assert.ok(results.length>1&&results.slice(1).every(t=>t.includes('Hérouville-Saint-Clair')));
  await page.locator('#sector-search').fill('introuvable');assert.equal(await page.locator('#sector-select option').count(),1);await page.getByText('0 secteur correspondant',{exact:true}).waitFor();
  await page.locator('#sector-search').fill('secteur '+method.example.sector.number);assert.ok((await page.locator('#sector-select option').allTextContents()).includes(method.example.sector.label+' · Priorité d’examen élevée'));
  await page.locator('#sector-select').selectOption(method.example.maille_id);await page.locator(`aside[data-maille-id="${method.example.maille_id}"]`).waitFor();await page.locator('#sector-search').fill('');
  const cases=[['yellow',cells.find(c=>c.territorial_priority.color==='jaune').maille_id],['gray',cells.find(c=>c.territorial_priority.color==='gris').maille_id],['uncertain','NORM-G1K-FLAT-R+006429-C+000492'],['linked','NORM-G1K-FLAT-R+006423-C+000488'],['four',method.example.maille_id],['exploratory','NORM-G1K-FLAT-R+006421-C+000491'],['empty','NORM-G1K-FLAT-R+006421-C+000490'],['red',cells.find(c=>c.territorial_priority.color==='rouge').maille_id]];
  for(const [name,id]of cases){await page.locator('#sector-select').selectOption(id);await page.locator(`aside[data-maille-id="${id}"]`).waitFor();await page.screenshot({path:path.join(out,'desktop_'+name+'.png'),fullPage:true})}
  const panel=page.locator('.v2-panel[data-maille-id]');
  for(const width of [320,390,768,1024,1440]){
   await page.setViewportSize({width,height:950});await page.waitForTimeout(200);
   await panel.locator('.v2-action-more').evaluateAll(els=>els.forEach(el=>el.open=true));
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'Pas de débordement, détails ouverts à '+width);
   const overlaps=await page.locator('.v2-action-header').evaluateAll(els=>els.map(el=>{const a=el.querySelector('.v2-family').getBoundingClientRect(),b=el.querySelector('.v2-level').getBoundingClientRect();return !(a.right<=b.left||b.right<=a.left||a.bottom<=b.top||b.bottom<=a.top)}));assert.ok(overlaps.every(v=>!v));
   const geometry=await page.evaluate(()=>{const h=document.querySelector('.app-header').getBoundingClientRect(),b=document.querySelector('.brand').getBoundingClientRect(),n=document.querySelector('.header-nav').getBoundingClientRect(),m=document.querySelector('main').getBoundingClientRect();return {headerOverlap:!(b.right<=n.left||n.right<=b.left||b.bottom<=n.top||n.bottom<=b.top),contentOverlap:h.bottom>m.top+1}});assert.deepEqual(geometry,{headerOverlap:false,contentOverlap:false});
   await panel.locator('.v2-action-more').evaluateAll(els=>els.forEach(el=>el.open=false));
  }
  await page.setViewportSize({width:390,height:844});await page.locator('#sector-select').selectOption(method.example.maille_id);await page.locator(`aside[data-maille-id="${method.example.maille_id}"]`).waitFor();
  const more=page.locator('.v2-action-more').first();await more.locator('summary').focus();await page.keyboard.press('Enter');assert.equal(await more.getAttribute('open'),'');await page.locator('.v2-action').first().screenshot({path:path.join(out,'mobile_details.png')});await page.keyboard.press('Enter');
  await page.screenshot({path:path.join(out,'mobile_four.png'),fullPage:true});
  // Native disclosure keeps the detailed indicators and human-readable sources, without JSON.
  await page.locator('.v2-technical > summary').click();assert.equal(await panel.locator('pre').count(),0);assert.ok(!jargon.test(await panel.locator('.v2-technical').innerText()));await page.locator('.v2-technical > summary').click();
  // Real click after recentering on the full pilot, on a coordinate confirmed to hit a rendered cell.
  await page.getByRole('button',{name:'Zoomer vers le territoire d’étude Caen et cinq communes'}).click();await page.locator('.map-frame').scrollIntoViewIfNeeded();
  await page.waitForFunction(d=>{const m=(new Function('return ('+d+')'))()();return m&&!m.isMoving()&&m.isStyleLoaded()},discover.toString());
  const hit=await page.evaluate(d=>{const m=(new Function('return ('+d+')'))()(),rect=m.getCanvas().getBoundingClientRect();for(let y=100;y<rect.height-70;y+=12)for(let x=65;x<rect.width-50;x+=12){const f=m.queryRenderedFeatures([x,y],{layers:['real-grid-fill']})[0];if(f&&document.elementFromPoint(rect.x+x,rect.y+y)?.tagName==='CANVAS')return{x:rect.x+x,y:rect.y+y,id:f.properties.maille_id}}},discover.toString());assert.ok(hit);await page.mouse.click(hit.x,hit.y);await page.locator(`aside[data-maille-id="${hit.id}"]`).waitFor();assert.equal(new URL(page.url()).searchParams.get('maille'),hit.id);
  await page.getByRole('link',{name:'Méthode et sources',exact:true}).click();await page.getByRole('heading',{name:'Méthode et sources',exact:true}).waitFor();await page.locator('.v2-real-example').waitFor();
  assert.equal(await page.locator('pre').count(),0);assert.ok(!jargon.test(await page.locator('main').innerText()));assert.equal(await page.locator('.v2-equation').count(),3);assert.equal(await page.locator('.v2-reference-list a').count(),12);
  await page.getByRole('heading',{name:'Une méthode fondée sur des travaux scientifiques et des données publiques',exact:true}).waitFor();
  assert.equal(await page.locator('[data-formula-origin]').count(),3);assert.ok((await page.locator('.scientific-mesh').innerText()).includes('ne sont pas calculés ici'));
  assert.equal(await page.locator('.v2-rule-grid .scientific-citations').count(),4);assert.ok((await page.locator('.scientific-numeric-example').innerText()).includes('0,86223'));
  for(const width of [320,390,768,1024,1440]){await page.setViewportSize({width,height:950});await page.locator('.v2-method-technical').evaluate(el=>el.open=true);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'Méthode '+width);await page.locator('.v2-method-technical').evaluate(el=>el.open=false);await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));if(width===390||width===1440)await page.screenshot({path:path.join(out,'method_'+width+'.png'),fullPage:true})}
  await page.getByRole('link',{name:'Ouvrir la fiche de cet exemple'}).click();await page.locator(`aside[data-maille-id="${method.example.maille_id}"]`).waitFor();assert.equal(await page.locator('.v2-action').count(),4);
  // Failed requests stay errors and do not fall back to public or old experimental data.
  await page.route('**/multiactions-v2/cells/**',r=>r.fulfill({status:503,contentType:'application/json',headers:{'Access-Control-Allow-Origin':new URL(base).origin},body:'{"error":"source_unavailable"}'}));
  await page.locator('#sector-select').selectOption('NORM-G1K-FLAT-R+006421-C+000491');await page.getByRole('alert').filter({hasText:'La fiche du secteur est indisponible'}).waitFor();await page.unroute('**/multiactions-v2/cells/**');await page.getByRole('button',{name:'Réessayer la fiche'}).click();await page.locator('aside[data-maille-id="NORM-G1K-FLAT-R+006421-C+000491"]').waitFor();
  // Deliberate tile failure preserves the vector grid and its interactions.
  const offline=await context.newPage();await offline.route('https://tile.openstreetmap.org/**',r=>r.abort());await offline.goto(base);await offline.locator('.region-map[aria-busy="false"]').waitFor({timeout:60000});await offline.getByText('Fond routier indisponible',{exact:true}).waitFor();await offline.locator('#sector-select').selectOption(method.example.maille_id);await offline.locator(`aside[data-maille-id="${method.example.maille_id}"]`).waitFor();assert.equal(await offline.locator('.v2-action').count(),4);
  const collision=await offline.evaluate(()=>{const a=document.querySelector('.v2-basemap-status').getBoundingClientRect(),b=document.querySelector('.maplibregl-ctrl-attrib').getBoundingClientRect();return !(a.right<=b.left||b.right<=a.left||a.bottom<=b.top||b.bottom<=a.top)});assert.equal(collision,false,'Attributions non masquées par le message de repli');await offline.screenshot({path:path.join(out,'offline_map.png'),fullPage:true});await offline.close();
  if(process.env.RECONNECT_V2_PREVIEW_URL){const prod=await context.newPage(),calls=[];prod.on('request',r=>{if(r.url().includes('/multiactions-v2/'))calls.push(r.url())});await prod.goto(process.env.RECONNECT_V2_PREVIEW_URL);await prod.getByRole('heading',{name:'Où étudier les continuités écologiques ?',exact:true}).waitFor();assert.deepEqual(calls,[]);assert.equal(await prod.locator('.v2-hero').count(),1);assert.ok((await prod.locator('.v2-source-notice').innerText()).includes('165 pistes historiques'));assert.equal(await prod.locator('[data-level]').count(),0);await prod.close()}
  const denied=await page.request.get(base+'/@fs'+path.resolve('../../Datathon-normandie-2026/data/derived/m2_multiactions_experimental_v2_20261112_01/lot_experimental_v2/fiches_multiactions_v2.json'));assert.equal(denied.status(),403,'Le serveur frontend ne publie pas le lot brut');
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
  const receipt={ok:true,minimum_priority_symbol_contrast:Math.min(...contrasts),raw_source_access_denied:true,rendered,colors,viewports:[320,390,768,1024,1440],single_map:true,municipality_and_sector_search:true,keyboard_disclosure:true,real_mobile_map_click:true,readable_resources_without_json:true,method_equations:3,verified_references:12,failed_cell_retry:true,basemap_failure_keeps_grid:true,production_v2_disabled:!!process.env.RECONNECT_V2_PREVIEW_URL,osm_tile_successes:tileResponses.filter(r=>r.status===200).length,osm_tile_failures:tileResponses.filter(r=>r.status>=400).length,unexpected_external_requests:external,javascript_errors:errors};
  fs.writeFileSync(path.join(out,'validation_browser.json'),JSON.stringify(receipt,null,2));console.log('PASS parcours final : recherche, couleurs, quatre pistes, mobile, méthode, erreurs, clavier et protections. Tuiles OSM reçues :',receipt.osm_tile_successes);
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
