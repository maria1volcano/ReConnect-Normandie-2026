const {chromium}=require(process.env.PLAYWRIGHT_MODULE_PATH||'playwright-core');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const out=process.env.RECONNECT_UI_QA_DIR||path.join(os.tmpdir(),'reconnect-unified-qa/comparison');fs.mkdirSync(out,{recursive:true});
const sources=[['public',process.env.RECONNECT_PUBLIC_PREVIEW_URL||'http://127.0.0.1:5187'],['local',process.env.RECONNECT_V2_UI_URL||'http://127.0.0.1:5184']];
const sectors=['NORM-G1K-FLAT-R+006424-C+000493','NORM-G1K-FLAT-R+006422-C+000487'];
(async()=>{const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_EXECUTABLE_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try{
 const receipt={ok:true,comparisons:[],errors:[],remote:null},headers={};
 for(const [kind,base]of sources){
  const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage();page.on('pageerror',e=>receipt.errors.push(kind+': '+e));
  for(const width of [320,390,768,1440]){
   await page.setViewportSize({width,height:1000});await page.goto(base+'/?maille='+encodeURIComponent(sectors[0]));
   const panel=page.locator(`aside[data-maille-id="${sectors[0]}"]`);await panel.waitFor();
   await page.locator('.region-map[aria-busy="false"]').waitFor({timeout:60000});
   await page.waitForTimeout(400);
   const geometry=await page.evaluate(()=>{
    const rect=selector=>{const r=document.querySelector(selector).getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}};
    const logo=document.querySelector('.brand-symbol'),style=getComputedStyle(logo),size=logo.getBoundingClientRect();
    return {header:rect('.app-header'),brand:rect('.brand'),nav:rect('.header-nav'),map:rect('.map-frame'),panel:rect('.v2-panel'),overflow:document.documentElement.scrollWidth>innerWidth,
     logo:{loaded:logo.complete&&logo.naturalWidth===814&&logo.naturalHeight===653,width:size.width,ratio:size.width/size.height,fit:style.objectFit},
     navigation:[...document.querySelectorAll('.header-nav a')].map(a=>({label:a.innerText,href:a.getAttribute('href'),focusable:a.tabIndex>=0}))}
   });
   assert.equal(geometry.overflow,false);assert.ok(geometry.logo.loaded);assert.ok(Math.abs(geometry.logo.ratio-814/653)<.01);assert.ok(geometry.logo.width>=48&&geometry.logo.width<=65);
   assert.deepEqual(geometry.navigation.map(a=>a.label),['Carte','Catalogue des actions','Méthode et sources']);assert.ok(geometry.navigation.every(a=>a.focusable));
   if(kind==='public')headers[width]=geometry;else {assert.deepEqual(geometry.header,headers[width].header);assert.deepEqual(geometry.brand,headers[width].brand);assert.deepEqual(geometry.nav,headers[width].nav);assert.equal(geometry.map.width,headers[width].map.width);assert.equal(geometry.panel.width,headers[width].panel.width)}
   assert.equal(await page.locator('.map-canvas').count(),1);assert.equal(await page.locator('.classification-switcher').count(),0);
   assert.equal(await page.locator('.v2-territorial-legend li').count(),4);
   const legend=await page.locator('.v2-territorial-legend').innerText();assert.ok(!legend.includes('vert'));
   const record={source:kind,width,geometry,sectors:[]};
   for(const [i,id]of sectors.entries()){
    if(i){await page.locator('#sector-select').selectOption(id);await page.locator(`aside[data-maille-id="${id}"]`).waitFor()}
    const current=page.locator(`aside[data-maille-id="${id}"]`),cards=current.locator('.v2-action');
    const details=await cards.evaluateAll(cards=>cards.map(c=>({id:c.dataset.actionId,source:c.dataset.source,level:c.dataset.level||null,why:c.querySelector('.v2-action-why p').innerText,solution:c.querySelector('.v2-action-solution p').innerText,checks:c.querySelectorAll('.v2-action-more li').length})));
    assert.ok(details.every(c=>c.source===(kind==='public'?'historical_public':'local_experimental')&&c.checks===3));
    if(kind==='public')assert.ok(details.every(c=>c.level===null));
    for(const c of details)assert.ok(c.why.length>80&&c.solution.length>60);
    record.sectors.push({id,label:await current.locator('.context-label').innerText(),actions:details.length,levels:details.map(c=>c.level)});
    await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(out,`${kind}_sector_${i+1}_${width}.png`),fullPage:true});
   }
   await page.getByRole('link',{name:'Méthode et sources',exact:true}).click();await page.locator('.v2-real-example').waitFor();
   assert.equal(await page.locator('[data-formula-origin]').count(),3);assert.equal(await page.locator('.v2-reference-list a').count(),12);assert.equal(await page.locator('.v2-rule-grid .scientific-citations').count(),4);
   await page.locator('.v2-method-page details').evaluateAll(els=>els.forEach(el=>el.open=true));assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await page.locator('.v2-method-page details').evaluateAll(els=>els.forEach(el=>el.open=false));
   await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(out,`${kind}_method_${width}.png`)});
   await page.locator('#calculs').screenshot({path:path.join(out,`${kind}_formulas_${width}.png`)});
   await page.locator('#references').screenshot({path:path.join(out,`${kind}_references_${width}.png`)});
   await page.getByRole('link',{name:'Carte',exact:true}).click();await page.locator('#sector-select').waitFor();
   await page.locator('#sector-search').fill('herouville');assert.ok((await page.locator('#sector-select option').allTextContents()).slice(1).every(t=>t.includes('Hérouville-Saint-Clair')));
   await page.locator('#sector-search').fill('introuvable');assert.equal(await page.locator('#sector-select option').count(),1);
   receipt.comparisons.push(record);console.log('PASS comparaison',kind,width);
  }
  if(kind==='public'){
   // Even a same-origin response is refused if it is not the authorized historical snapshot.
   const tampered=await context.newPage(),api=[];tampered.on('request',r=>{if(r.url().includes('/api/'))api.push(r.url())});
   await tampered.route('**/data/caen-6com/cells.json',async r=>{const original=await r.fetch(),data=await original.json();Object.values(data)[0].mode='local_experimental';await r.fulfill({response:original,json:data})});
   await tampered.goto(base);await tampered.getByRole('alert').waitFor();assert.equal(await tampered.locator('.v2-action').count(),0);assert.deepEqual(api,[]);
   await tampered.unroute('**/data/caen-6com/cells.json');await tampered.getByRole('button',{name:'Réessayer le chargement',exact:true}).click();await tampered.locator('#sector-select option').nth(101).waitFor({state:'attached'});await tampered.close();receipt.tampered_public_response_rejected=true;receipt.public_retry=true;
  }
  await context.close();
 }
 // Observe the deployed preview without attempting to bypass its Vercel access protection.
 if(process.env.RECONNECT_REMOTE_PREVIEW_URL){
  const remote=await browser.newPage();await remote.goto(process.env.RECONNECT_REMOTE_PREVIEW_URL,{waitUntil:'domcontentloaded'});await remote.waitForTimeout(1200);
  const u=new URL(remote.url());receipt.remote={requested:process.env.RECONNECT_REMOTE_PREVIEW_URL,origin:u.origin,path:u.pathname,title:await remote.title(),application_header:await remote.locator('.app-header').count()};
  await remote.screenshot({path:path.join(out,'vercel_current.png')});await remote.close();
 }
 assert.deepEqual(receipt.errors,[]);fs.writeFileSync(path.join(out,'comparison.json'),JSON.stringify(receipt,null,2));console.log('PASS interface commune, deux secteurs identiques, quatre largeurs, méthode et permissions.');
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
