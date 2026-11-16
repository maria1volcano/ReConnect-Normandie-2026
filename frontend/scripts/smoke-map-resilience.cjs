const {chromium}=require(process.env.PLAYWRIGHT_MODULE_PATH||'playwright-core');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const base=process.env.RECONNECT_PUBLIC_PREVIEW_URL||'http://127.0.0.1:5187',out=process.env.RECONNECT_UI_QA_DIR;
fs.mkdirSync(out,{recursive:true});
const discover=()=>{const el=document.querySelector('.application-shell');if(!el)return null;const k=Object.keys(el).find(k=>k.startsWith('__reactFiber$'));for(let f=el[k];f;f=f.return)for(let h=f.memoizedState;h&&typeof h==='object';h=h.next){const m=h.memoizedState?.current;if(m&&typeof m.queryRenderedFeatures==='function')return m}return null};
const probe=async page=>page.evaluate(d=>{
 const m=(new Function('return ('+d+')'))()();if(!m)return {map:false};
 const canvas=m.getCanvas(),style=m.getStyle(),source=m.getSource('real-grid-source'),grid=m.getLayer('real-grid-fill');
 const features=grid?m.queryRenderedFeatures({layers:['real-grid-fill']}):[];
 return {map:true,styleLoaded:!!m.isStyleLoaded(),sourceCells:source?.serialize().data.features.length??0,renderedCells:new Set(features.map(f=>f.properties.maille_id)).size,canvas:[canvas.clientWidth,canvas.clientHeight],layers:style?.layers.map(l=>l.id),center:m.getCenter().toArray(),rasterVisibility:m.getLayoutProperty('openstreetmap','visibility')??'visible',gridOpacity:m.getPaintProperty('real-grid-fill','fill-opacity')};
},discover.toString());
const waitGrid=async page=>{await page.waitForFunction(d=>{const m=(new Function('return ('+d+')'))()();return m?.getLayer('real-grid-fill')&&m.queryRenderedFeatures({layers:['real-grid-fill']}).length>0},discover.toString(),{timeout:20000});const state=await probe(page);assert.equal(state.sourceCells,101);assert.ok(state.renderedCells>80);assert.ok(state.canvas.every(n=>n>=300));return state};
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_EXECUTABLE_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const receipt={ok:false,scenarios:[],javascript_errors:[],api_requests:[]};
 try{
  for(const scenario of ['normal','tuiles_lentes','sans_tuiles']){
   const context=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce'}),page=await context.newPage(),tiles={requests:0,success:0,blocked:0},mapErrors=[];
   await context.route('**/api/**',r=>{receipt.api_requests.push(r.request().url());return r.abort()});
   page.on('pageerror',e=>receipt.javascript_errors.push(String(e)));
   page.on('console',m=>{if(m.type()==='error'&&/RegionMap|RealGridLayer/.test(m.text()))mapErrors.push(m.text())});
   page.on('response',r=>{if(r.url().includes('tile.openstreetmap.org')){tiles.success+=Number(r.ok());tiles.blocked+=Number(!!r.headers()['x-blocked'])}});
   page.on('request',r=>{if(r.url().includes('tile.openstreetmap.org'))tiles.requests++});
   if(scenario==='tuiles_lentes')await context.route('**/tile.openstreetmap.org/**',async r=>{await new Promise(resolve=>setTimeout(resolve,30000));await r.continue().catch(()=>{})});
   if(scenario==='sans_tuiles')await context.route('**/tile.openstreetmap.org/**',r=>r.abort());
   const started=Date.now();await page.goto(base,{waitUntil:'domcontentloaded'});await page.locator('#sector-select option').nth(101).waitFor({state:'attached'});
   const initial=await waitGrid(page),gridVisibleMs=Date.now()-started;
   if(scenario==='tuiles_lentes'){assert.equal(tiles.success,0);assert.ok(gridVisibleMs<25000,'Les mailles apparaissent sans attendre les tuiles')}
   // Exercise the actual rendered layer, rather than only the dropdown.
   const target=await page.evaluate(d=>{const m=(new Function('return ('+d+')'))()(),f=m.queryRenderedFeatures({layers:['real-grid-fill']}).find(f=>f.geometry.type==='Polygon');const points=f.geometry.coordinates[0],center=points.slice(0,-1).reduce((sum,p)=>[sum[0]+p[0]/(points.length-1),sum[1]+p[1]/(points.length-1)],[0,0]);const point=m.project(center);return {id:f.properties.maille_id,x:point.x,y:point.y}},discover.toString());
   const box=await page.locator('.map-canvas').boundingBox();await page.mouse.click(box.x+target.x,box.y+target.y);await page.locator('aside[data-maille-id]').waitFor();
   const clickedId=await page.locator('aside[data-maille-id]').getAttribute('data-maille-id');assert.ok(clickedId);
   if(scenario==='sans_tuiles'){
    await page.getByRole('button',{name:'Réessayer le fond routier',exact:true}).waitFor();assert.ok((await probe(page)).renderedCells>80);
    await context.unroute('**/tile.openstreetmap.org/**');const before=tiles.requests;await page.getByRole('button',{name:'Réessayer le fond routier',exact:true}).click();
    await page.waitForFunction(d=>{const m=(new Function('return ('+d+')'))()();return m?.isSourceLoaded('openstreetmap')},discover.toString(),{timeout:20000});
    assert.ok(tiles.requests>before,'Le bouton relance réellement les requêtes de fond');assert.equal(await page.locator('aside[data-maille-id]').getAttribute('data-maille-id'),clickedId);
   }
   if(scenario==='normal'){
    // Style reload must restore the real grid and its feature states.
    await page.evaluate(d=>{const m=(new Function('return ('+d+')'))()(),s=m.getStyle();s.layers=s.layers.filter(l=>!l.id.startsWith('real-grid-'));delete s.sources['real-grid-source'];m.setStyle(s,{diff:false})},discover.toString());
    await waitGrid(page);
    const selected=await page.evaluate(({d,id})=>{const m=(new Function('return ('+d+')'))()();return m.getFeatureState({source:'real-grid-source',id}).selected},{d:discover.toString(),id:clickedId});assert.equal(selected,true);
   }
   await page.evaluate(()=>scrollTo({top:0,behavior:'instant'}));await page.screenshot({path:path.join(out,'carte_'+scenario+'_1440.png')});
   assert.deepEqual(mapErrors,[]);receipt.scenarios.push({scenario,initial,final:await probe(page),gridVisibleMs,tiles,mapErrors,map_click_selected:clickedId});console.log('PASS résilience',scenario,'grille visible en',gridVisibleMs+' ms');await context.close();
  }
  const context=await browser.newContext({viewport:{width:1440,height:900}}),page=await context.newPage();
  await page.addInitScript(()=>{const original=HTMLCanvasElement.prototype.getContext;window.__restoreMapContext=()=>{HTMLCanvasElement.prototype.getContext=original};HTMLCanvasElement.prototype.getContext=function(type,...args){return /webgl/i.test(type)?null:original.call(this,type,...args)}});
  page.on('pageerror',e=>receipt.javascript_errors.push(String(e)));
  await page.goto(base,{waitUntil:'domcontentloaded'});await page.getByText('La carte ne peut pas être affichée.',{exact:true}).waitFor();
  assert.equal(await page.getByText('Les secteurs restent sélectionnables.',{exact:true}).count(),0);
  await page.evaluate(()=>window.__restoreMapContext());await page.getByRole('button',{name:'Réessayer la carte',exact:true}).click();await waitGrid(page);assert.equal(await page.locator('canvas.maplibregl-canvas').count(),1);
  receipt.scenarios.push({scenario:'echec_webgl_et_reprise',ok:true});await context.close();
  assert.deepEqual(receipt.api_requests,[]);assert.deepEqual(receipt.javascript_errors,[]);receipt.ok=true;
 }catch(e){receipt.error=String(e);throw e}
 finally{fs.writeFileSync(path.join(out,'resilience_carte.json'),JSON.stringify(receipt,null,2));await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
