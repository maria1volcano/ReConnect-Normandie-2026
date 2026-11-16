const {chromium}=require(process.env.PLAYWRIGHT_MODULE_PATH||'playwright-core');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const base=process.env.RECONNECT_PUBLIC_PREVIEW_URL||'http://127.0.0.1:5187',out=process.env.RECONNECT_UI_QA_DIR||path.join(os.tmpdir(),'reconnect-mvp-public');fs.mkdirSync(out,{recursive:true});
(async()=>{const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_EXECUTABLE_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try{
 const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage(),apiRequests=[],errors=[];
 page.on('pageerror',e=>errors.push(String(e)));
 await context.route('**/api/**',r=>{apiRequests.push(r.request().url());return r.abort()});
 const routes=[['/','Où étudier les continuités écologiques ?'],['/methode','Méthode et sources'],['/catalogue','Catalogue des actions']];
 for(const [route,title]of routes){
  await page.goto(base+route);await page.getByRole('heading',{name:title,exact:typeof title==='string'}).waitFor();
  await page.locator('.v2-source-notice').waitFor();assert.ok((await page.locator('.v2-source-notice').innerText()).includes('165 pistes historiques autorisées'));
  assert.equal(await page.locator('.classification-switcher').count(),0,'Pas de mode technique dans le parcours public');assert.equal(await page.locator('[data-level]').count(),0,'Aucun niveau A/B/C historique inventé');if(route==='/')assert.equal(await page.locator('.v2-hero').count(),1,'Présentation partagée');
  for(const width of [320,390,768,1024,1440]){
   await page.setViewportSize({width,height:1000});await page.waitForTimeout(150);
   const geometry=await page.evaluate(()=>{const h=document.querySelector('.app-header').getBoundingClientRect(),m=document.querySelector('main').getBoundingClientRect(),b=document.querySelector('.brand').getBoundingClientRect(),n=document.querySelector('.header-nav').getBoundingClientRect();return {overflow:document.documentElement.scrollWidth>innerWidth,headerOverlap:!(b.right<=n.left||n.right<=b.left||b.bottom<=n.top||n.bottom<=b.top),contentOverlap:h.bottom>m.top+1}});
   assert.deepEqual(geometry,{overflow:false,headerOverlap:false,contentOverlap:false},route+' '+width);
  }
  if(route==='/methode'){await page.getByRole('heading',{name:'Une méthode fondée sur des travaux scientifiques et des données publiques',exact:true}).waitFor();assert.equal(await page.locator('[data-formula-origin]').count(),3);assert.equal(await page.locator('.v2-reference-list a').count(),12);assert.ok((await page.locator('.scientific-numeric-example').innerText()).includes('0,727383'));}
  if(route==='/'){await page.locator('#sector-select option').nth(101).waitFor({state:'attached'});assert.equal(await page.locator('.map-canvas').count(),1)}
  if(route==='/catalogue'){await page.locator('[data-family]').nth(3).waitFor();assert.equal(await page.locator('[data-family]').count(),4);assert.equal(await page.locator('[data-catalogue-total]').getAttribute('data-catalogue-total'),'165');assert.equal(await page.locator('[data-level]').count(),0)}
  assert.ok(!/\b(?:V[1-4]|R[1-4]|A0[1-4]|D\/S|XY|SHA-?256)\b|NORM-G1K/.test(await page.locator('main').innerText()),'Vocabulaire public lisible : '+route);
  if(route==='/methode'){
   const contrasts=await page.locator('.doc-section').evaluateAll(sections=>{
    const lum=c=>c.match(/[\d.]+/g).slice(0,3).map(Number).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0);
    return sections.flatMap(s=>[...s.querySelectorAll('h2,p')].map(el=>{const a=lum(getComputedStyle(el).color),b=lum(getComputedStyle(s).backgroundColor);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05)}));
   });assert.ok(contrasts.every(n=>n>=4.5),'Contrastes documentaires de production');
  }
  await page.screenshot({path:path.join(out,'public_'+(route.slice(1)||'carte')+'.png'),fullPage:true});
 }
 // Navigation through the production SPA and direct route loads both work.
 await page.getByRole('link',{name:'Méthode et sources',exact:true}).click();await page.getByRole('heading',{name:'Méthode et sources'}).waitFor();
 await page.getByRole('link',{name:'Carte',exact:true}).click();await page.getByRole('heading',{name:'Où étudier les continuités écologiques ?',exact:true}).waitFor();
 const response=await page.request.get(base+'/data/caen-6com/cells.json');assert.equal(response.status(),200);const cells=await response.json();assert.equal(Object.keys(cells).length,101);
 const entries=Object.values(cells).flatMap(c=>c.investigations);assert.equal(entries.length,404);const leads=entries.filter(i=>i.lead_status==='a_etudier').length;assert.equal(leads,165,'La production conserve son export autorisé, sans inventer les 205 propositions locales');
 await page.goto(base+'/?maille='+encodeURIComponent('NORM-G1K-FLAT-R+006422-C+000487'));
 const panel=page.locator('aside[data-maille-id="NORM-G1K-FLAT-R+006422-C+000487"]');await panel.waitFor();
 await panel.getByText('Données et méthode du secteur',{exact:true}).click();
 assert.equal(await panel.locator('pre').count(),0);assert.ok(!/\b(?:R[1-4]|A0[1-4]|D\/S|XY|SHA-?256)\b|NORM-G1K/.test(await panel.innerText()),'La fiche publique ne montre aucun identifiant interne');
 await page.screenshot({path:path.join(out,'public_fiche.png'),fullPage:true});
 let renderedLeads=0,empty=0;const families={},colors={rouge:0,orange:0,jaune:0,gris:0};
 for(const [id,c]of Object.entries(cells)){
  await page.locator('#sector-select').selectOption(id);const current=page.locator(`aside[data-maille-id="${id}"]`);await current.waitFor();
  const expected=c.investigations.filter(a=>a.lead_status==='a_etudier').map(a=>a.action_id);
  assert.deepEqual(await current.locator('.v2-action').evaluateAll(cards=>cards.map(c=>c.dataset.actionId)),expected);
  assert.equal(await current.locator('[data-level]').count(),0);assert.equal(await current.locator('.v2-level').count(),expected.length);
  for(const id of expected)families[id]=(families[id]||0)+1;
  renderedLeads+=expected.length;empty+=!expected.length;colors[c.documentary.level]++;
  if(!expected.length)await current.locator('.v2-empty').waitFor();
 }
 assert.equal(renderedLeads,165);assert.equal(empty,30);assert.deepEqual(families,{A03:35,A04:60,A01:50,A02:20});assert.deepEqual(colors,{rouge:27,orange:33,jaune:9,gris:32});
 assert.equal(cells['NORM-G1K-FLAT-R+006422-C+000487'].documentary.observations.nombre_paires_route_corridor_2d,88);
 assert.equal(cells['NORM-G1K-FLAT-R+006422-C+000487'].documentary.observations.paires_route_matrice_fragile_en_service_au_sol,45);
 assert.equal(cells['NORM-G1K-FLAT-R+006422-C+000487'].geometric_observations.local_event_count,89);
 assert.deepEqual(apiRequests,[],'Aucun backend local nécessaire au build public');assert.deepEqual(errors,[]);
 const receipt={ok:true,routes:['/','/methode','/catalogue'],viewports:[320,390,768,1024,1440],without_backend:true,api_requests:apiRequests,public_cells:101,historical_family_examinations:entries.length,authorized_historical_leads:leads,v2_actions_exposed:0,release_difference_visible:true,rendered_historical_leads:renderedLeads,empty_sectors:empty,families,colors,javascript_errors:errors};fs.writeFileSync(path.join(out,'validation_production.json'),JSON.stringify(receipt,null,2));console.log('PASS production : présentation commune, 101 secteurs, 165 pistes historiques, 30 sans piste ; cinq largeurs et navigation sans backend.');
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
