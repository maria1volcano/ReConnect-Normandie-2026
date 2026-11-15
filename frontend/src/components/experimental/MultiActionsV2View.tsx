import { useEffect, useMemo, useRef, useState } from 'react'
import type { CSSProperties } from 'react'
import type { Map as MapLibreMap, LngLatBoundsLike } from 'maplibre-gl'
import type { Geometry } from 'geojson'
import { SiteHeader } from '../layout/SiteHeader'
import { RegionMap } from '../map/RegionMap'
import { RealGridLayer } from '../map/RealGridLayer'
import { LEVEL_NAMES, loadV2, loadV2Cell, type V2Action, type V2Cell } from '../../integrations/multiActionsV2Adapter'
import { actionFamilyVisual } from '../../integrations/actionFamilyVisuals'
import { presentAction, readableNonSelection } from '../../integrations/actionPresentation'
import { PRIORITY_LABELS, prioritySymbol, searchText, territorialSummary } from '../../integrations/territorialPresentation'
import { linkClickHandler } from '../../app/router'
import { ActionFamilyIcon } from './ActionFamilyIcon'
import { TerritorialPriorityLegend } from './TerritorialPriorityLegend'
import './multiActionsV2.css'

function geometryBounds(geometry: Geometry): LngLatBoundsLike | null {
  let west=Infinity, south=Infinity, east=-Infinity, north=-Infinity
  const walk = (value: unknown): void => {
    if (!Array.isArray(value)) return
    if (typeof value[0] === 'number' && typeof value[1] === 'number') {
      west=Math.min(west,value[0]);east=Math.max(east,value[0]);south=Math.min(south,value[1]);north=Math.max(north,value[1])
    } else value.forEach(walk)
  }
  if ('coordinates' in geometry) walk(geometry.coordinates)
  return Number.isFinite(west) ? [[west,south],[east,north]] : null
}

function ActionCard({action}: {action: V2Action}) {
  const family = actionFamilyVisual(action.action_id), copy = presentAction(action)
  const theme = { '--family-color': family.color, '--family-icon-background': family.iconBackground } as CSSProperties
  return <article className="v2-action" style={theme} data-action-id={action.action_id} data-level={action.level}>
    <header className="v2-action-header">
      <div className="v2-family">
        {family.iconName && <span className="v2-family-icon"><ActionFamilyIcon family={family}/></span>}
        <p className="v2-family-name">{family.label}</p>
      </div>
      <p className="v2-level" aria-label={`Justification : ${LEVEL_NAMES[action.level]}, niveau ${action.level}`}>
        {LEVEL_NAMES[action.level]}<span aria-hidden="true">{action.level}</span>
      </p>
    </header>
    <h3>{action.name}</h3>
    <section className="v2-action-why"><h4>Pourquoi cette action ?</h4><p>{copy.why.join(' ')}</p></section>
    <section className="v2-action-solution"><h4>Solution envisageable</h4><p>{copy.intervention.join(' ')}</p></section>
    <details className="v2-action-more">
      <summary>En savoir plus<span className="v2-sr-only"> sur {family.label.toLowerCase()}</span></summary>
      <h4>Les observations utiles</h4>
      <dl className="v2-local-indicators">{copy.highlights.map(i => <div key={i.label}><dt>{i.label}</dt><dd>{i.value.toLocaleString('fr-FR')}</dd></div>)}</dl>
      <p className="v2-indicator-note">Comptes cartographiques ; plusieurs relations peuvent concerner le même objet.</p>
      <p className="v2-specific-limit"><strong>Point à confirmer.</strong> {copy.keyLimit}</p>
      <h4>Avant de décider</h4><ul>{copy.checks.map(check => <li key={check}>{check}</li>)}</ul>
    </details>
  </article>
}

const OBSERVATIONS: Record<string,string> = {routes:'Tronçons routiers',haies:'Haies',friches:'Sites recensés dans Cartofriches',plans_eau:'Plans d’eau',zones_humides:'Éléments d’inventaire humide',corridors:'Espaces de continuité régionaux',reservoirs:'Réservoirs de biodiversité'}
function SectorResources({cell}: {cell: V2Cell}) {
  return <details className="v2-technical"><summary>Données et méthode du secteur</summary>
    <p>Sources acquises en novembre 2026 : IGN, DREAL Normandie et Cerema. La référence du schéma régional est de 2014 ; la date d’acquisition ne garantit pas l’actualité écologique.</p>
    <dl className="v2-local-indicators">{Object.entries(OBSERVATIONS).map(([key,label]) => <div key={key}><dt>{label}</dt><dd>{cell.observations[key]?.nombre_objets_observes?.toLocaleString('fr-FR') ?? 'Non renseigné'}</dd></div>)}</dl>
    <p>Ces inventaires ne sont pas reconnus comme exhaustifs sur le plan écologique : un compte nul n’atteste pas une absence réelle.</p>
    {cell.actions.map(action => {
      const copy=presentAction(action)
      return <details className="v2-complete-indicators" key={action.action_id}><summary>Tous les indicateurs : {actionFamilyVisual(action.action_id).label}</summary>
        <dl className="v2-local-indicators">{copy.indicators.map(i=><div key={i.label}><dt>{i.label}</dt><dd>{i.value.toLocaleString('fr-FR')}</dd></div>)}</dl>
        {copy.interpretation.map(p=><p key={p}>{p}</p>)}
      </details>
    })}
    <p>{cell.local_event_count.toLocaleString('fr-FR')} relations géométriques sont rattachées à ce secteur, dont {cell.canonical_event_count.toLocaleString('fr-FR')} comptées exclusivement ici pour éviter les doublons entre secteurs. Elles ne correspondent pas à des obstacles confirmés.</p>
    <p>Les résultats historiques de priorité écologique restent indéterminés. Les réponses et fichiers complets sont conservés pour l’équipe technique dans les ressources internes protégées.</p>
  </details>
}

function CellDetail({id}: {id: string}) {
  const [cell,setCell]=useState<V2Cell|null>(null),[error,setError]=useState(false),[retry,setRetry]=useState(0)
  useEffect(()=>{
    const control=new AbortController();setCell(null);setError(false)
    void loadV2Cell(id,control.signal).then(c=>{if(!control.signal.aborted)setCell(c)})
      .catch(()=>{if(!control.signal.aborted)setError(true)})
    return()=>control.abort()
  },[id,retry])
  if (!cell) return <aside className="v2-panel" aria-live="polite"><h2>Fiche du secteur</h2>
    <p role={error?'alert':'status'}>{error?'La fiche du secteur est indisponible pour le moment.':'Chargement des pistes…'}</p>
    {error&&<button onClick={()=>setRetry(v=>v+1)}>Réessayer la fiche</button>}</aside>
  const priority=cell.territorial_priority
  return <aside className="v2-panel" data-maille-id={id} aria-labelledby="v2-detail-title">
    <p className="context-label">Secteur {cell.sector.number}</p><h2 id="v2-detail-title">{cell.municipalities.join(' / ')}</h2>
    <p className="v2-territorial-status"><span className="v2-priority-swatch" style={{backgroundColor:priority.color_hex}} aria-hidden="true">{prioritySymbol(priority)}</span>
      <span>Priorité d’examen indicative<strong>{PRIORITY_LABELS[priority.color]}</strong></span></p>
    <p className="v2-sector-summary">{territorialSummary(cell)}</p>
    <p className="v2-piste-count">{cell.actions.length ? `${cell.actions.length} solution${cell.actions.length>1?'s':''} à étudier`:'Aucune proposition pour ce secteur'}
      {cell.actions.length>1&&<span>Sans classement de bénéfice entre les solutions.</span>}</p>
    {cell.comparisons.some(c=>c.observations_liees)&&<p className="v2-linked v2-plain-note">Certaines pistes utilisent les mêmes observations ; elles ne constituent pas des confirmations indépendantes.</p>}
    {!cell.actions.length&&<div className="v2-empty"><h3>Aucune piste territorialisée retenue</h3><p>Les observations disponibles ne permettent pas de formuler une piste pour ces quatre familles. Cela ne prouve pas une absence d’enjeu écologique.</p></div>}
    <div className="v2-actions">{cell.actions.map(a=><ActionCard key={a.action_id} action={a}/>)}</div>
    <p className="v2-reserve">Ces pistes nécessitent une confirmation écologique et technique avant toute décision de travaux.</p>
    {!!cell.not_selected.length&&<details className="v2-extra"><summary>Familles sans proposition</summary>{cell.not_selected.map(a=><section key={a.action_id}><h4>{actionFamilyVisual(a.action_id).label}</h4><p>{readableNonSelection(a.reason)}</p></section>)}</details>}
    <SectorResources cell={cell}/>
    <a className="v2-method-link" href="/methode" onClick={linkClickHandler('/methode')}>Comprendre la méthode et les sources</a>
  </aside>
}

export function MultiActionsV2View() {
  const [data,setData]=useState<Awaited<ReturnType<typeof loadV2>>|null>(null),[error,setError]=useState(false),[retry,setRetry]=useState(0)
  const [selected,setSelected]=useState<string|null>(()=>new URLSearchParams(window.location.search).get('maille'))
  const [hovered,setHovered]=useState<string|null>(null),[query,setQuery]=useState(''),[showGrid,setShowGrid]=useState(true)
  const [,setMapRevision]=useState(0),map=useRef<MapLibreMap|undefined>(undefined)
  useEffect(()=>{
    const control=new AbortController();setError(false);setData(null)
    void loadV2(control.signal).then(d=>{if(!control.signal.aborted)setData(d)}).catch(()=>{if(!control.signal.aborted)setError(true)})
    return()=>control.abort()
  },[retry])
  useEffect(()=>{
    const sync=()=>setSelected(new URLSearchParams(window.location.search).get('maille'))
    window.addEventListener('popstate',sync);return()=>window.removeEventListener('popstate',sync)
  },[])
  const bounds=useMemo(():LngLatBoundsLike|null=>{
    if(!data)return null
    const geometries=data.grid.features.map(f=>f.geometry)
    const coordinates=geometries.flatMap(g=>'coordinates'in g?[g.coordinates]:[])
    return geometryBounds({type:'MultiPolygon',coordinates} as Geometry)
  },[data])
  const features=data?.grid.features??[],selectedFeature=features.find(f=>f.properties.maille_id===selected)
  const matching=features.filter(f=>searchText(query).split(/\s+/).every(term=>searchText(f.properties.sector.label).includes(term.replace(/^0+(?=\d)/,''))))
  const select=(id:string|null,zoom=false)=>{
    setSelected(id)
    const url=new URL(window.location.href);if(id)url.searchParams.set('maille',id);else url.searchParams.delete('maille')
    window.history.replaceState({},'',url)
    if(zoom&&id){const geometry=features.find(f=>f.properties.maille_id===id)?.geometry,target=geometry&&geometryBounds(geometry)
      if(target&&map.current)map.current.fitBounds(target,{padding:48,maxZoom:14,duration:window.matchMedia('(prefers-reduced-motion: reduce)').matches?0:400})}
    if(id&&window.innerWidth<=1000)document.querySelector('#v2-analysis')?.scrollIntoView({behavior:'instant',block:'start'})
  }
  const readout=features.find(f=>f.properties.maille_id===hovered)??selectedFeature
  return <div className="application-shell"><SiteHeader experimental/>
    <main id="main-content" className="workspace v2-workspace">
      <section className="v2-hero"><p className="context-label">Territoire pilote : Caen et cinq communes voisines</p>
        <h1 id="v2-title">Où étudier les continuités écologiques ?</h1>
        <p>Repérez les secteurs à examiner et découvrez les solutions envisageables, avec les observations qui les motivent.</p>
        {data&&<p className="v2-summary">{data.metadata.cells} secteurs analysés · {data.metadata.proposals} pistes d’action · couverture limitée au territoire pilote</p>}
      </section>
      <section className="map-workspace" aria-labelledby="v2-title">
        {error&&<div role="alert" className="v2-empty"><p>Les données du territoire sont indisponibles pour le moment.</p><button onClick={()=>setRetry(v=>v+1)}>Réessayer le chargement</button></div>}
        {!data&&!error&&<p role="status">Chargement des données du territoire…</p>}
        {data&&<>
          <div className="v2-sector-search"><label htmlFor="sector-search">Rechercher une commune ou un secteur</label>
            <input id="sector-search" type="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Ex. : Colombelles, secteur 58" aria-controls="sector-select"/>
            <label className="v2-selector" htmlFor="sector-select">Choisir un secteur
              <select id="sector-select" value={matching.some(f=>f.properties.maille_id===selected)?selected??'':''} onChange={e=>select(e.target.value||null,true)}>
                <option value="">{matching.length?'Sélectionner sur la carte ou dans la liste':'Aucun secteur correspondant'}</option>
                {matching.map(f=><option key={f.properties.maille_id} value={f.properties.maille_id}>{f.properties.sector.label} · {PRIORITY_LABELS[f.properties.territorial_priority.color]}</option>)}
              </select>
            </label><p className="v2-search-count" role="status">{matching.length} secteur{matching.length>1?'s':''} correspondant{matching.length>1?'s':''}</p>
          </div>
          <div className="map-frame"><RegionMap compactControls selectedDepartment={null} mapRef={map} onMapReady={()=>setMapRevision(v=>v+1)}
            realGridCount={data.metadata.cells} showRealGrid={showGrid} onToggleRealGrid={()=>setShowGrid(v=>!v)} studyAreaBounds={bounds} testModeAvailable={false}
            onZoomToPilot={()=>{if(map.current&&bounds)map.current.fitBounds(bounds,{padding:32,duration:0})}}/>
            <RealGridLayer map={map.current} realGridData={data.grid} selectedRealHexagonId={selected} hoveredRealHexagonId={hovered}
              onSelectRealHexagon={id=>select(id)} onHoverRealHexagon={setHovered} showRealGrid={showGrid} classificationView="study" contextualBasemap/>
          </div>
          <p className="v2-map-readout" aria-live="polite">{readout?`${readout.properties.sector.label} · ${PRIORITY_LABELS[readout.properties.territorial_priority.color]}`:'Cliquez sur une maille pour ouvrir sa fiche.'}</p>
          <TerritorialPriorityLegend/>
          {selectedFeature&&<a className="v2-to-detail" href="#v2-analysis">Voir les solutions de ce secteur</a>}
        </>}
      </section>
      <section id="v2-analysis" aria-label="Pistes du secteur">
        {data&&selectedFeature?<CellDetail key={selected} id={selectedFeature.properties.maille_id}/>:<div className="v2-panel v2-welcome"><p className="context-label">Comprendre un secteur</p><h2>{selected?'Secteur introuvable':'Choisissez un secteur sur la carte'}</h2><p>Sa fiche expliquera la couleur de la maille, les solutions à étudier et les vérifications à réaliser.</p><p>La recherche permet aussi de retrouver un secteur par sa commune.</p><a className="v2-method-link" href="/methode" onClick={linkClickHandler('/methode')}>Découvrir la méthode</a></div>}
      </section>
      <p className="v2-footer">Version locale de revue · données internes, diffusion non autorisée.</p>
    </main>
  </div>
}
