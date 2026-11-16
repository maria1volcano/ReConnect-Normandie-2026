import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import {createHash} from 'node:crypto'
const root=path.resolve(process.env.RECONNECT_BUILD_DIR || 'dist')
const digest=file=>createHash('sha256').update(fs.readFileSync(file)).digest('hex')
const walk=dir=>fs.readdirSync(dir,{withFileTypes:true}).flatMap(entry=>entry.isDirectory()?walk(path.join(dir,entry.name)):[path.join(dir,entry.name)])
assert.ok(fs.existsSync(path.join(root,'index.html')),'Build requis')
let publicFiles=0
for(const file of walk(path.resolve('public'))){
 const relative=path.relative(path.resolve('public'),file),target=path.join(root,relative)
 assert.ok(fs.existsSync(target),'Ressource publique conservée : '+relative)
 assert.equal(digest(target),digest(file),'Les données publiques ne sont pas remplacées : '+relative);publicFiles++
}
// Shared presentation is public; private loaders, pinned manifests and payloads remain forbidden.
const forbidden=['/Users/','fiches_multiactions_v2.json','17 335 tronçons routiers','172 éléments retenus','Le pilote produit 205 pistes sur 88 secteurs','m2.multiactions.experimental-2.0','caen6-examen-multiactions-presentation-20261115-1','NORM-G1K-FLAT-R+006424-C+000493','/multiactions-v2/','http://127.0.0.1:8765','Choisir les premières actions à étudier','Actions à étudier et pistes historiques','95378d1f13bc94418b813b682f3c7a75572126374cb2e825b9e72da0ea8e6057']
for(const file of walk(root)){
 assert.ok(!/\.(?:zip|gpkg|sqlite|pem|key|env)$/i.test(file),'Aucun lot interne ou secret embarqué')
 if(/\.(?:js|css|html)$/.test(file)){
  const text=fs.readFileSync(file,'utf8')
  for(const term of forbidden)assert.ok(!text.includes(term),'Contenu de revue locale absent du bundle : '+term)
 }
}
console.log('PASS production : adaptateurs et contenus expérimentaux exclus ; présentation commune autorisée ;',publicFiles,'ressources publiques identiques ; aucun lot interne ou chemin privé.')
