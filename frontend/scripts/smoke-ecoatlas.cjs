const {chromium}=require(process.env.PLAYWRIGHT_MODULE_PATH||'playwright-core');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const kind=process.env.RECONNECT_ECO_SOURCE||'public',base=kind==='public'?(process.env.RECONNECT_PUBLIC_PREVIEW_URL||'http://127.0.0.1:5187'):(process.env.RECONNECT_V2_UI_URL||'http://127.0.0.1:5184');
const out=process.env.RECONNECT_UI_QA_DIR;fs.mkdirSync(out,{recursive:true});
const mid='NORM-G1K-FLAT-R+006424-C+000493',widths=[390,768,1440],total=kind==='public'?165:205;
const labels=['Secteur à examiner en priorité','Priorité d’examen élevée','Priorité d’examen modérée','Informations insuffisantes'];
const palette=['rgb(214, 69, 69)','rgb(239, 146, 41)','rgb(232, 200, 74)','rgb(144, 152, 164)'];
function visibleGrid(){const el=document.querySelector('.application-shell');if(!el)return false;const k=Object.keys(el).find(k=>k.startsWith('__reactFiber$'));for(let f=el[k];f;f=f.return)for(let h=f.memoizedState;h&&typeof h==='object';h=h.next){const m=h.memoizedState?.current;if(m&&typeof m.queryRenderedFeatures==='function')return !!m.getLayer('real-grid-fill')&&m.queryRenderedFeatures({layers:['real-grid-fill']}).length>0}return false}
// Composite actual solid surfaces. For the decorative body gradient use a
// conservative lighter forest sample; the header gradient's lightest stop is its surface token.
function contrastAudit(){
 const rgb=s=>{const n=s.match(/[\d.]+/g)?.map(Number);return n?[...n.slice(0,3),n[3]??1]:[0,0,0,0]};
 const over=(a,b)=>a.slice(0,3).map((v,i)=>v*a[3]+b[i]*(1-a[3]));
 const lum=c=>c.map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
 const selector='.app-header a,.brand small,main h1,main h2,main h3,main h4,main p,main label,main button,main input,main select,.v2-territorial-legend li,.v2-method-page li,.v2-method-page summary,.v2-method-page code,.v2-method-page a,.v2-action summary';
 const values=[...document.querySelectorAll(selector)].filter(e=>e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden'&&e.textContent.trim());
 return values.map(e=>{
  let bg=[24,55,47];const chain=[];for(let p=e;p;p=p.parentElement)chain.push(p);
  for(const p of chain.reverse()){if(p===document.body)bg=[57,97,78];if(p.classList.contains('app-header'))bg=[36,75,61];else bg=over(rgb(getComputedStyle(p).backgroundColor),bg)}
  const fg=over(rgb(getComputedStyle(e).color),bg),a=lum(fg),b=lum(bg),ratio=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);
  return {tag:e.tagName,classes:String(e.className),text:e.textContent.trim().slice(0,70),ratio,color:getComputedStyle(e).color,background:bg};
 });
}
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_EXECUTABLE_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const result={ok:false,kind,viewports:widths,pages:[],javascript_errors:[],api_requests:[],unexpected_external_requests:[],screenshots:[]};
 try{
  const context=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce'}),page=await context.newPage();
  page.on('pageerror',e=>result.javascript_errors.push(String(e)));
  page.on('request',r=>{const u=new URL(r.url());if(['http:','https:'].includes(u.protocol)&&!['localhost','127.0.0.1','tile.openstreetmap.org'].includes(u.hostname))result.unexpected_external_requests.push(u.origin)});
  if(kind==='public')await context.route('**/api/**',r=>{result.api_requests.push(r.request().url());return r.abort()});
  for(const route of ['/', '/catalogue','/methode']){
   await page.goto(base+route+(route==='/'?'?maille='+encodeURIComponent(mid):''));
   await page.getByRole('heading',{name:route==='/'?'Où étudier les continuités écologiques ?':route==='/catalogue'?'Catalogue des actions':'Méthode et sources',exact:true}).waitFor();
   if(route==='/'){await page.locator(`aside[data-maille-id="${mid}"]`).waitFor();await page.locator('.region-map[aria-busy="false"]').waitFor({timeout:60000});await page.waitForFunction(visibleGrid,null,{timeout:30000})}
   if(route==='/catalogue')await page.locator('[data-family]').nth(3).waitFor({timeout:60000});
   if(route==='/methode')await page.locator('.v2-real-example').waitFor();
   assert.deepEqual(await page.locator('.header-nav a').allTextContents(),['Carte','Catalogue des actions','Méthode et sources']);
   assert.equal(await page.locator('.header-nav [aria-current="page"]').getAttribute('href'),route);
   const record={route,widths:[],contrast_minimum:null,contrast_samples:0};
   for(const width of widths){
    await page.setViewportSize({width,height:900});await page.evaluate(()=>scrollTo(0,0));await page.evaluate(()=>document.fonts.ready);
    const geometry=await page.evaluate(()=>{const b=document.querySelector('.brand').getBoundingClientRect(),n=document.querySelector('.header-nav').getBoundingClientRect(),h=document.querySelector('.app-header').getBoundingClientRect(),m=document.querySelector('main').getBoundingClientRect(),logo=document.querySelector('.brand-symbol'),r=logo.getBoundingClientRect(),pseudo=getComputedStyle(document.body,'::before');return {overflow:document.documentElement.scrollWidth>innerWidth,headerOverlap:!(b.right<=n.left||n.right<=b.left||b.bottom<=n.top||n.bottom<=b.top),contentOverlap:h.bottom>m.top+1,headerHeight:h.height,logoLoaded:logo.complete&&logo.naturalWidth===814&&logo.naturalHeight===653,logoRatio:r.width/r.height,decorationCount:pseudo.backgroundSize.split(',').length,decorationPointerEvents:pseudo.pointerEvents}});
    assert.equal(geometry.overflow,false);assert.equal(geometry.headerOverlap,false);assert.equal(geometry.contentOverlap,false);assert.ok(geometry.logoLoaded);assert.ok(Math.abs(geometry.logoRatio-814/653)<.01);assert.equal(geometry.decorationCount,3);assert.equal(geometry.decorationPointerEvents,'none');
    if(route==='/'){
     const compact=await page.evaluate(()=>{const h=document.querySelector('.v2-hero').getBoundingClientRect(),m=document.querySelector('.map-frame').getBoundingClientRect(),s=document.querySelector('.v2-sector-search').getBoundingClientRect();return {heroHeight:h.height,mapTop:m.top,searchHeight:s.height}});if(width===1440){assert.ok(compact.heroHeight<=230);assert.ok(compact.mapTop<=430);assert.ok(compact.searchHeight<100)}
     const legend=page.locator('.v2-territorial-legend');assert.deepEqual(await legend.locator('li > span:last-child').allTextContents(),labels);assert.deepEqual(await legend.locator('.v2-priority-swatch').evaluateAll(els=>els.map(e=>e.style.backgroundColor)),palette);
     const bounds=await legend.boundingBox();assert.ok(bounds.height<240);assert.equal(await legend.locator('details').getAttribute('open'),null);
     const map=await page.locator('.map-workspace').evaluate(e=>({background:getComputedStyle(e).backgroundImage,shadow:getComputedStyle(e).boxShadow,before:getComputedStyle(e,'::before').content,after:getComputedStyle(e,'::after').content}));assert.equal((map.background.match(/linear-gradient/g)||[]).length,2);assert.notEqual(map.shadow,'none');assert.ok(['none','normal'].includes(map.before));assert.ok(['none','normal'].includes(map.after));
     await legend.locator('summary').click();assert.ok((await legend.innerText()).includes('Les niveaux de justification des solutions sont indépendants.'));await legend.locator('summary').click();
     assert.equal(await page.locator('.v2-action').count(),kind==='public'?3:4);assert.ok((await page.locator('.v2-summary').innerText()).includes(String(total)));
    }
    if(route==='/catalogue'){
     assert.equal(await page.locator('[data-family]').count(),4);assert.equal(await page.locator('[data-catalogue-total]').getAttribute('data-catalogue-total'),String(total));
     assert.equal(await page.locator('[data-level]').count(),kind==='public'?0:205);
     if(kind!=='public'){const levels=await page.locator('[data-level]').evaluateAll(els=>els.reduce((counts,e)=>(counts[e.dataset.level]=(counts[e.dataset.level]||0)+1,counts),{}));assert.deepEqual(levels,{A:93,B:45,C:67});record.levels=levels;}
     const borders=await page.locator('[data-family]').evaluateAll(els=>els.map(e=>({value:getComputedStyle(e).borderInlineStartColor,expected:e.style.getPropertyValue('--family-color')})));assert.ok(borders.every(b=>b.value&&b.expected));
    }
    if(route==='/methode'){assert.equal(await page.locator('[data-formula-origin]').count(),3);assert.equal(await page.locator('.v2-reference-list a').count(),12)}
    const audit=await page.evaluate(contrastAudit),failed=audit.filter(r=>r.ratio<4.5);record.contrast_samples+=audit.length;record.contrast_minimum=Math.min(record.contrast_minimum??Infinity,...audit.map(r=>r.ratio));
    if(failed.length){fs.writeFileSync(path.join(out,kind+'_contrast_failures.json'),JSON.stringify({route,width,failed},null,2));assert.fail('Contraste AA : '+failed.length+' éléments, '+route+' à '+width+' px')}
    await page.locator('main details:not(.maplibregl-ctrl-attrib)').evaluateAll(els=>els.forEach(e=>e.open=true));assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'Détails ouverts '+route+' '+width);await page.locator('main details:not(.maplibregl-ctrl-attrib)').evaluateAll(els=>els.forEach(e=>e.open=false));
    const heroDecoration=await page.locator(route==='/'?'.v2-hero':'.doc-hero').evaluate(e=>({content:getComputedStyle(e,'::after').content,image:getComputedStyle(e,'::after').backgroundImage}));assert.equal(heroDecoration.image,'none');assert.ok(['none','normal'].includes(heroDecoration.content));
    record.widths.push({...geometry,heroDecoration});
    if(width===390||width===1440){
     await page.evaluate(async()=>{document.activeElement?.blur();scrollTo({top:0,behavior:'instant'});await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))});await page.waitForTimeout(300);
     const filename=kind+'_'+(route==='/'?'carte':route.slice(1))+'_'+width+'.png';await page.screenshot({path:path.join(out,filename),fullPage:false});result.screenshots.push(filename);
     if(route==='/'){for(const [selector,suffix] of [['.map-frame','carte_interactive'],['.v2-territorial-legend','legende'],['#v2-analysis > .v2-panel','fiche']]){const name=kind+'_'+suffix+'_'+width+'.png';await page.locator(selector).screenshot({path:path.join(out,name)});result.screenshots.push(name)}}
     if(route==='/methode'){const name=kind+'_formules_'+width+'.png';await page.locator('#calculs').screenshot({path:path.join(out,name)});result.screenshots.push(name)}
    }
   }
   if(route==='/'){await page.locator('#sector-search').fill('herouville');assert.ok((await page.locator('#sector-select option').allTextContents()).slice(1).every(t=>t.includes('Hérouville-Saint-Clair')));await page.locator('#sector-search').fill('introuvable');assert.equal(await page.locator('#sector-select option').count(),1);await page.locator('#sector-search').fill('');assert.equal(await page.locator('#sector-select option').count(),102);await page.locator('#sector-select').selectOption('NORM-G1K-FLAT-R+006422-C+000487');await page.locator('aside[data-maille-id="NORM-G1K-FLAT-R+006422-C+000487"]').waitFor();record.search_and_selection=true;}
   // A keyboard focus is visible and reduced-motion prevents hover transitions.
   await page.locator('.header-nav a').first().focus();await page.keyboard.press('Tab');
   const focus=await page.evaluate(()=>{const s=getComputedStyle(document.activeElement);return {style:s.outlineStyle,width:parseFloat(s.outlineWidth),transition:s.transitionDuration}});assert.equal(focus.style,'solid');assert.ok(focus.width>=3);assert.ok(focus.transition.split(',').every(t=>parseFloat(t)===0));record.keyboard_focus=focus;
   if(route==='/catalogue'){
    await page.getByRole('button',{name:'Bocage',exact:true}).click();await page.getByRole('combobox',{name:'Filtrer par commune',exact:true}).selectOption('Hérouville-Saint-Clair');await page.getByRole('combobox',{name:'Filtrer par priorité territoriale',exact:true}).selectOption('orange');
    const row=page.locator('[data-family="A01"] [data-sector-id]').first(),target=await row.getAttribute('data-sector-id');assert.ok(target);
    await page.locator('.journey-sector-list > summary').click();await row.click();await page.locator(`aside[data-maille-id="${target}"]`).waitFor();assert.equal(new URL(page.url()).searchParams.get('famille'),'A01');record.catalogue_link_and_filters=true;
   }
   result.pages.push(record);console.log('PASS ÉcoAtlas',kind,route,widths.length+' largeurs, contrastes, navigation et captures.');
  }
  assert.deepEqual(result.api_requests,[]);assert.deepEqual(result.javascript_errors,[]);assert.deepEqual(result.unexpected_external_requests,[]);result.ok=true;await context.close();
 }catch(e){result.error=String(e);throw e}
 finally{fs.writeFileSync(path.join(out,kind+'_ecoatlas.json'),JSON.stringify(result,null,2));await browser.close()}
})().catch(e=>{console.error(String(e));process.exitCode=1});
