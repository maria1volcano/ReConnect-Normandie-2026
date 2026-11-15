const {chromium}=require(process.env.PLAYWRIGHT_MODULE_PATH || 'playwright-core');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const base=process.env.RECONNECT_V2_UI_URL || 'http://127.0.0.1:5184';
const out=process.env.RECONNECT_UI_QA_DIR || path.join(os.tmpdir(),'reconnect_action_family_visuals_qa');fs.mkdirSync(out,{recursive:true});
const expected={A01:{icon:'Trees',color:'rgb(40, 122, 73)',label:'Haies'},A02:{icon:'Droplets',color:'rgb(36, 126, 176)',label:'Milieux humides'},
 A03:{icon:'Sprout',color:'rgb(152, 102, 44)',label:'Friches'},A04:{icon:'Route',color:'rgb(104, 98, 168)',label:'Franchissements pour la faune'}};
(async()=>{const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_EXECUTABLE_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
 args:['--disable-background-networking','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try{const context=await browser.newContext({viewport:{width:1440,height:1080}}),errors=[],external=[],results=[];
 await context.route('**/*',r=>{const u=new URL(r.request().url());if(['http:','https:'].includes(u.protocol)&&!['127.0.0.1','localhost'].includes(u.hostname)){external.push(u.origin);return r.abort()}return r.continue()});
 const page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));
 for(const [name,suffix,levels]of [['multi','006423-C+000488',['A','A','A']],['friche','006423-C+000491',['A','A','A']],['plausible','006427-C+000495',['B','C']],['exploratoire','006421-C+000491',['C']]]){
  const id='NORM-G1K-FLAT-R+'+suffix;await page.goto(base+'/?maille='+encodeURIComponent(id));const panel=page.locator(`aside[data-maille-id="${id}"]`);await panel.waitFor({timeout:30000});
  assert.deepEqual(await panel.locator('.v2-action').evaluateAll(els=>els.map(e=>e.dataset.level)),levels);
  const cards=await panel.locator('.v2-action').evaluateAll(els=>{
   function rgb(value){return value.match(/[\d.]+/g).slice(0,3).map(Number)}
   function luminance(value){return rgb(value).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((n,v,i)=>n+v*[.2126,.7152,.0722][i],0)}
   function ratio(a,b){const x=luminance(a),y=luminance(b);return(Math.max(x,y)+.05)/(Math.min(x,y)+.05)}
   return els.map(card=>{const tile=card.querySelector('.v2-family-icon'),icon=tile.querySelector('svg'),family=card.querySelector('.v2-family-name'),badge=card.querySelector('.v2-level'),title=card.querySelector('h3');
    const cardStyle=getComputedStyle(card),tileStyle=getComputedStyle(tile),badgeStyle=getComputedStyle(badge);
    return {id:card.dataset.actionId,icon:icon.dataset.icon,label:family.textContent,color:tileStyle.color,accent:cardStyle.borderInlineStartColor,
     background:cardStyle.backgroundColor,iconContrast:ratio(tileStyle.color,tileStyle.backgroundColor),
     labelContrast:ratio(getComputedStyle(family).color,cardStyle.backgroundColor),titleContrast:ratio(getComputedStyle(title).color,cardStyle.backgroundColor),
     badgeContrast:ratio(badgeStyle.color,badgeStyle.backgroundColor),badgeText:badge.textContent,
     decorative:icon.getAttribute('aria-hidden')==='true'&&icon.getAttribute('focusable')==='false',nodes:icon.querySelectorAll('path,circle').length}
   })});
  for(const c of cards){assert.equal(c.icon,expected[c.id].icon);assert.equal(c.label,expected[c.id].label);assert.equal(c.color,expected[c.id].color);assert.equal(c.accent,expected[c.id].color);
   assert.ok(c.iconContrast>=3,'Contraste icône '+c.id);assert.ok(Math.min(c.labelContrast,c.titleContrast,c.badgeContrast)>=4.5,'Contraste texte '+c.id);assert.ok(c.decorative&&c.nodes>0);
   assert.equal(c.background,'rgb(32, 43, 40)','Fond neutre commun');}
  results.push({name,cards});
  if(name==='multi'||name==='friche'){await page.locator('.region-map[aria-busy="false"]').waitFor({timeout:60000});await page.screenshot({path:path.join(out,'desktop_'+name+'.png'),fullPage:true})}
  for(const width of [320,390,768,1440]){await page.setViewportSize({width,height:900});await page.waitForTimeout(150);
   const geometry=await panel.locator('.v2-action-header').evaluateAll(els=>els.map(el=>{const f=el.querySelector('.v2-family').getBoundingClientRect(),b=el.querySelector('.v2-level').getBoundingClientRect();return{overflow:el.scrollWidth>el.clientWidth+1,overlap:!(f.right<=b.left||b.right<=f.left||f.bottom<=b.top||b.bottom<=f.top)}}));
   assert.ok(geometry.every(v=>!v.overflow&&!v.overlap),'Icône, famille et badge lisibles à '+width);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'Débordement '+width);
  }
  if(name==='multi'||name==='plausible'){await page.setViewportSize({width:390,height:844});await panel.scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,'mobile_'+name+'.png'),fullPage:true});await page.setViewportSize({width:1440,height:1080})}
 }
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 fs.writeFileSync(path.join(out,'validation_visuals.json'),JSON.stringify({ok:true,results,viewports:[320,390,768,1440],javascript_errors:errors,external_requests:external,
   text_contrast_minimum:Math.min(...results.flatMap(r=>r.cards.flatMap(c=>[c.labelContrast,c.titleContrast,c.badgeContrast]))),
   icon_contrast_minimum:Math.min(...results.flatMap(r=>r.cards.map(c=>c.iconContrast)))},null,2));
 console.log('PASS présentation : 4 icônes/couleurs exactes, badges A/B/C distincts, fonds neutres, contrastes et 4 largeurs sans chevauchement.');
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
