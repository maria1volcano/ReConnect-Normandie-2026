import {useEffect,useMemo,useState} from 'react'
import type {CSSProperties} from 'react'
import {SiteHeader} from '../layout/SiteHeader'
import {ScientificCitations} from '../method/ScientificBasis'
import {ActionFamilyIcon} from './ActionFamilyIcon'
import {actionFamilyVisual} from '../../integrations/actionFamilyVisuals'
import {LEVEL_NAMES,type JourneySource} from '../../integrations/journeyModel'
import {PRIORITY_LABELS} from '../../integrations/territorialPresentation'
import {CATALOGUE_FAMILIES,EMPTY_CATALOGUE_FILTERS,loadJourneyCatalogue,readCatalogueFilters,filterCatalogueEntries,catalogueHref,type JourneyCatalogue} from '../../integrations/journeyCatalogue'
import {linkClickHandler} from '../../app/router'
import './journey.css'

export function JourneyCataloguePage({source}:{source:JourneySource}) {
  const [catalogue,setCatalogue]=useState<JourneyCatalogue|null>(null),[error,setError]=useState(false),[retry,setRetry]=useState(0)
  const [filters,setFilters]=useState(()=>readCatalogueFilters(window.location.search))
  useEffect(()=>{
    const control=new AbortController();setError(false);setCatalogue(null)
    void loadJourneyCatalogue(source,control.signal).then(data=>{if(!control.signal.aborted)setCatalogue(data)}).catch(()=>{if(!control.signal.aborted)setError(true)})
    return()=>control.abort()
  },[source,retry])
  useEffect(()=>{const sync=()=>setFilters(readCatalogueFilters(window.location.search));window.addEventListener('popstate',sync);return()=>window.removeEventListener('popstate',sync)},[])
  useEffect(()=>window.history.replaceState({},'',catalogueHref('/catalogue',filters)),[filters])
  const communes=useMemo(()=>Array.from(new Set(catalogue?.cells.flatMap(c=>c.municipalities)??[])).sort((a,b)=>a.localeCompare(b,'fr')),[catalogue])
  const visible=CATALOGUE_FAMILIES.filter(f=>filters.family==='all'||filters.family===f.id)
  const count=catalogue?visible.reduce((n,f)=>n+filterCatalogueEntries(catalogue,f.id,filters).length,0):0
  const unit=source.kind==='historical_public'?'pistes calculées':'propositions locales'
  return <div className="application-shell"><SiteHeader/>
    <main id="main-content" className="doc-page v2-method-page journey-catalogue">
      <section className="doc-hero"><p className="context-label">Comprendre les quatre familles</p><h1>Catalogue des actions</h1>
        <p>Découvrez les situations qui peuvent motiver une étude, les observations utiles et les conditions à vérifier. Les fiches de secteurs précisent ensuite le contexte local.</p>
        {catalogue&&<p className="v2-summary">{catalogue.data.metadata.cells} secteurs · {catalogue.data.metadata.proposals} {unit} · 4 familles documentées</p>}
      </section>
      <p className="v2-source-notice" role="note" data-source={source.kind}>{source.notice}</p>
      {!catalogue&&!error&&<p role="status">Chargement des familles et des secteurs…</p>}
      {error&&<div role="alert" className="v2-empty"><p>Le catalogue est indisponible pour le moment.</p><button onClick={()=>setRetry(n=>n+1)}>Réessayer le catalogue</button></div>}
      {catalogue&&<>
        <section className="catalogue-filters journey-catalogue-filters" aria-label="Filtres du catalogue">
          <fieldset><legend>Famille</legend><div className="journey-family-filters">
            <button className={`filter-chip ${filters.family==='all'?'is-active':''}`} aria-pressed={filters.family==='all'} onClick={()=>setFilters({...filters,family:'all'})}>Toutes</button>
            {CATALOGUE_FAMILIES.map(f=><button key={f.id} className={`filter-chip ${filters.family===f.id?'is-active':''}`} aria-pressed={filters.family===f.id} onClick={()=>setFilters({...filters,family:f.id})}>{f.label}</button>)}
          </div></fieldset>
          <label>Rechercher<input id="catalogue-search" type="search" value={filters.query} placeholder="Une famille, une commune, un secteur…" onChange={e=>setFilters({...filters,query:e.target.value})}/></label>
          <label>Commune<select aria-label="Filtrer par commune" value={filters.commune} onChange={e=>setFilters({...filters,commune:e.target.value})}><option value="all">Toutes les communes</option>{communes.map(c=><option key={c} value={c}>{c}</option>)}</select></label>
          <label>Priorité territoriale<select aria-label="Filtrer par priorité territoriale" value={filters.priority} onChange={e=>setFilters({...filters,priority:e.target.value as typeof filters.priority})}><option value="all">Toutes les priorités</option>{Object.entries(PRIORITY_LABELS).map(([color,label])=><option key={color} value={color}>{label}</option>)}</select></label>
          <button className="journey-reset" onClick={()=>setFilters({...EMPTY_CATALOGUE_FILTERS})}>Réinitialiser les filtres</button>
        </section>
        <p className="journey-catalogue-count" role="status" data-catalogue-total={count}>{count} {unit} correspondent aux filtres. La priorité territoriale reste indépendante de la justification des solutions.</p>
        <div className="catalogue-grid journey-catalogue-grid">{visible.map(definition=>{
          const entries=filterCatalogueEntries(catalogue,definition.id,filters),family=actionFamilyVisual(definition.id),conditions=source.method.families[definition.methodIndex]
          const total=catalogue.families.find(f=>f.id===definition.id)!.entries.length
          const mapFilters={...filters,family:definition.id},href=entries.length?catalogueHref('/',mapFilters,entries[0].cell.maille_id):null
          const theme={'--family-color':family.color,'--family-icon-background':family.iconBackground} as CSSProperties
          return <article className="catalogue-card journey-family-card" key={definition.id} data-family={definition.id} style={theme}>
            <header className="v2-family"><span className="v2-family-icon"><ActionFamilyIcon family={family}/></span><h2>{definition.label}</h2></header>
            <h3>{definition.title}</h3><p>{definition.problem}</p>
            <section><h4>Piste de solution</h4><p>{definition.solution}</p></section>
            <section><h4>Quand l’étudier ?</h4><p>{conditions[1]}</p></section>
            <details className="journey-family-details"><summary>Conditions, limites et sources</summary>
              <h4>Observations à examiner</h4><p>{definition.indicators}</p>
              <h4>Avant une décision</h4><p>{conditions[2]}</p><p>{definition.limit}</p>
              <h4>Données utiles</h4><ul>{definition.sources.map(s=><li key={s}>{s}</li>)}</ul>
              <ScientificCitations ids={definition.references}/>
            </details>
            <p className="journey-family-count"><strong>{entries.length}</strong> secteur{entries.length>1?'s':''} correspondant{entries.length>1?'s':''} sur {total} pour cette famille.</p>
            {source.kind==='historical_public'&&<p className="v2-small-note">Pistes historiques ; justification non qualifiée.</p>}
            {href?<a className="catalogue-map-link" href={href} onClick={linkClickHandler(href)}>Voir les secteurs concernés<span className="v2-sr-only"> : {definition.label}</span></a>:<p className="catalogue-empty">Aucun secteur ne correspond à ces filtres pour cette famille.</p>}
            {!!entries.length&&<details className="journey-sector-list"><summary>Liste des {entries.length} secteurs</summary><ul className="catalogue-cells" aria-label={`Secteurs concernés : ${definition.label}`}>{entries.map(({cell,action})=>{
              const link=catalogueHref('/',mapFilters,cell.maille_id)
              return <li key={cell.maille_id}><a href={link} onClick={linkClickHandler(link)} data-sector-id={cell.maille_id}>
                <span className="journey-sector-name">{cell.sector.label}</span>
                <span className="journey-sector-priority"><span className="legend-swatch" style={{backgroundColor:cell.territorial_priority.color_hex}} aria-hidden="true"/>{PRIORITY_LABELS[cell.territorial_priority.color]}</span>
                {action.source==='local_experimental'&&<span className="v2-level" data-level={action.level}>{LEVEL_NAMES[action.level]}<span>{action.level}</span></span>}
              </a></li>
            })}</ul></details>}
          </article>
        })}</div>
        <p className="v2-reserve">Ces familles proposent des questions d’étude. Toute réalisation demande une confirmation écologique et technique du besoin et de la faisabilité.</p>
      </>}
      <a className="v2-method-link" href="/methode" onClick={linkClickHandler('/methode')}>Comprendre la méthode et les sources</a>
    </main>
  </div>
}
