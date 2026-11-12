import { useEffect, useState } from 'react'
import { loadM4CellBundle, type M4CellBundle, type M4StudyAction } from '../../integrations/m4Adapter'

interface Props { mailleId: string; gridVersion: string; territoryId: string }
export const ACTION_NAMES: Record<string, string> = {
  A04: 'Faciliter le passage de la faune',
  A01: 'Restaurer les continuités bocagères',
  A03: 'Réhabiliter les friches au bénéfice de la biodiversité',
  A02: 'Préserver et reconnecter les mares et milieux humides',
}
const OBSERVATION_NAMES: Record<string, string> = {
  haies: 'Haies', plans_eau: 'Plans d’eau', friches: 'Sites Cartofriches', zones_humides: 'Zones humides inventoriées',
  corridors: 'Corridors cartographiés', reservoirs: 'Réservoirs cartographiés', routes: 'Tronçons routiers',
}
function readable(text: string): string {
  return text.replace(/V1[–-]V3/g, 'cartographiques').replace(/\bV[1-4]\b/g, 'cartographique')
    .replace(/\bA0[1-4]\b/g, (id) => ACTION_NAMES[id]).replace(/\bR[1-4]\b/g, 'scientifique')
}
function area(value: number): string {
  return value >= 1_000_000 ? `${(value / 1_000_000).toLocaleString('fr-FR', { maximumFractionDigits: 2 })} km²`
    : `${value.toLocaleString('fr-FR', { maximumFractionDigits: 0 })} m²`
}
function ActionStudy({ action }: { action: M4StudyAction }) {
  return <article className="action-study" data-action-id={action.action_id}>
    <p className="study-status">À instruire — étude indicative</p>
    <h4>{ACTION_NAMES[action.action_id]}</h4>
    <p>{readable(action.justification)}</p>
    <p className="detail-note">Pertinence écologique non évaluable à ce stade.</p>
    {!!action.prochaines_etapes?.length && <ol>{action.prochaines_etapes.map((step) => <li key={step}>{readable(step)}</li>)}</ol>}
  </article>
}
export function TerritorialZoneDetail({ mailleId, gridVersion, territoryId }: Props) {
  const [data, setData] = useState<M4CellBundle | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    const controller = new AbortController()
    setData(null); setError(null)
    void loadM4CellBundle(gridVersion, mailleId, territoryId, controller.signal)
      .then((result) => { if (!controller.signal.aborted) setData(result) })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : 'Source de données indisponible')
      })
    return () => controller.abort()
  }, [gridVersion, mailleId, territoryId])
  if (!data) return <aside className="zone-detail" aria-live="polite"><div className="detail-state">
    <p className="context-label">Fiche territoriale</p><h2>Diagnostic du secteur</h2>
    <p role={error ? 'alert' : undefined}>{error ? `Fiche indisponible : ${error}` : 'Chargement de la fiche…'}</p>
  </div></aside>
  const d = data.instruction
  const p = data.study_priority
  const selectedIds = new Set([d?.main_action?.action_id, ...(d?.complementary_actions.map((a) => a.action_id) ?? [])])
  const notSelected = d?.options.filter((a) => !selectedIds.has(a.action_id)) ?? []
  const historicalLeads = data.investigations.filter((a) => a.lead_status === 'a_etudier')
  return <aside className="zone-detail territorial-detail" data-maille-id={mailleId} aria-labelledby="territorial-detail-title">
    <div className="detail-content">
      <header className="detail-header">
        <p className="context-label">Fiche territoriale · {area(data.area_m2)}</p>
        <h2 id="territorial-detail-title">{data.municipalities.map((m) => m.nom).join(', ')}</h2>
        {p ? <p className="study-priority" data-study-color={p.couleur} style={{ borderLeftColor: p.couleur_hex }}>{p.libelle}</p>
          : <p className="detail-note">Classement documentaire antérieur · décisions du nouveau lot indisponibles</p>}
      </header>
      <section className="detail-section" aria-label="Diagnostic territorial">
        <h3 className="detail-section-title">Ce que montrent les données</h3>
        <p>{readable(d?.diagnostic ?? data.documentary.reason)}</p>
      </section>
      <section className="detail-section" aria-label="Observations locales">
        <h3 className="detail-section-title">Observations locales</h3>
        <div className="indicators-grid">
          <div className="indicator-item"><span className="indicator-label">Événements géométriques locaux</span><strong className="indicator-value">{data.geometric_observations.local_event_count}</strong></div>
          <div className="indicator-item"><span className="indicator-label">Événements attribués à cette maille</span><strong className="indicator-value">{data.geometric_observations.canonical_event_count}</strong></div>
        </div>
        <p className="detail-note">Les événements locaux peuvent être partagés entre mailles. Seuls les comptes attribués sont additionnables.</p>
        {data.geometric_observations.local_event_count === 0 && <p>Zéro événement observé ne démontre pas une absence de fragmentation écologique.</p>}
        <ul className="observations-list">{Object.entries(data.geometric_observations.source_observations)
          .filter(([name]) => Object.hasOwn(OBSERVATION_NAMES, name)).map(([name, record]) =>
            <li key={name}><strong>{OBSERVATION_NAMES[name]} :</strong> {record.nombre_objets_observes ?? 'non renseigné'} objet(s) observé(s)
              {record.nombre_objets_observes === 0 ? ' — absence écologique non démontrée' : ''}.</li>)}</ul>
        {d?.road_context && <details className="detail-expandable"><summary>Contexte routier observé</summary>
          {Object.entries(d.road_context).map(([name, values]) => <p key={name}><strong>{({categorie: 'Catégories', statut_objet: 'État de service', position_sol: 'Position (0 au sol, positive surélevée, négative souterraine)'} as Record<string, string>)[name] ?? name} :</strong> {Object.entries(values).map(([v, n]) => `${v} : ${n}`).join(' · ')}</p>)}
          <p>La position routière ne démontre pas la perméabilité écologique. Ces comptes de paires ne sont pas un trafic mesuré.</p>
        </details>}
      </section>
      <section className="detail-section" aria-label="Action principale à étudier">
        <h3 className="detail-section-title">Première action à étudier</h3>
        {d?.main_action ? <ActionStudy action={d.main_action} /> : <>
          <p className="no-intervention">{p?.couleur === 'jaune' ? 'Préservation à examiner' : 'Aucune intervention sélectionnée'}</p>
          <p>{d ? readable(d.orientation) : 'Les décisions d’action de la livraison finale ne sont pas disponibles dans cet export. Aucune sélection n’est déduite des anciennes pistes.'}</p>
          {d?.no_main_reason && <p>{readable(d.no_main_reason)}</p>}
        </>}
      </section>
      <section className="detail-section" aria-label="Actions complémentaires">
        <h3 className="detail-section-title">Autres actions pertinentes</h3>
        {d?.complementary_actions.length ? d.complementary_actions.map((a) => <ActionStudy key={a.action_id} action={a} />)
          : <p>{d ? readable(d.no_complementary_reason) : 'Aucune action complémentaire sélectionnée dans cette livraison.'}</p>}
        {notSelected.length > 0 && <details className="detail-expandable">
          <summary>Familles non sélectionnées : préconditions à vérifier ({notSelected.length})</summary>
          {notSelected.map((a) => <article className="unselected-action" key={a.action_id}>
            <h4>{ACTION_NAMES[a.action_id]}</h4><p><strong>Non sélectionnée · pertinence non évaluable</strong></p>
            <p>{readable(a.justification)}</p><p>{readable(a.observations)}</p>
            <ul>{a.conditions_manquantes.map((c) => <li key={c}>{readable(c)}</li>)}</ul>
          </article>)}
        </details>}
      </section>
      {d && <section className="detail-section" aria-label="Validation avant travaux">
        <h3 className="detail-section-title">Avant toute réalisation</h3>
        <ul>{Array.from(new Set([...d.conditions_before_works, ...(d.main_action?.conditions_manquantes ?? [])])).map((c) => <li key={c}>{readable(c)}</li>)}</ul>
      </section>}
      <section className="detail-section" aria-label="Priorité écologique D/S">
        <h3 className="detail-section-title">Priorité écologique D/S : indéterminée</h3>
        <p>Le rang indicatif d’étude est distinct du calcul écologique officiel. Aucune recommandation de travaux n’est scientifiquement validée.</p>
      </section>
      <details className="detail-expandable technical-provenance">
        <summary>Détails techniques, pistes historiques et provenance</summary>
        <dl><dt>Maille</dt><dd>{data.maille_id}</dd><dt>Territoire</dt><dd>{data.territory_id}</dd>
          <dt>Grille</dt><dd>{data.grid_version}</dd><dt>Données</dt><dd>{data.dataset_version}</dd>
          <dt>Version des décisions</dt><dd>{d?.version ?? 'non disponible'}</dd>
          <dt>Priorité scientifique</dt><dd>INDETERMINATE · validation PENDING · méthode NULL</dd>
          {data.provenance && <><dt>Empreinte du ZIP source</dt><dd>{data.provenance.source_zip_sha256}</dd></>}
        </dl>
        <h4>Pistes historiques conservées ({historicalLeads.length})</h4>
        <p>Ces pistes sont traçables ; leur présence ne sélectionne aucune restauration.</p>
        {historicalLeads.map((a) => <article key={a.action_id}><h4>{a.rule_id} / {a.action_id} — {ACTION_NAMES[a.action_id]}</h4>
          <p>Statut scientifique : {a.status}. Statut historique : {a.lead_status}.</p><p>{a.evidence}</p><p>{a.reason}</p>
          <ul>{a.missing_conditions.map((c) => <li key={c}>{c}</li>)}</ul></article>)}
        {!!d?.historical_lead_ids.length && <ul>{d.historical_lead_ids.map((id) => <li key={id}>{id}</li>)}</ul>}
        <p>Sources : IGN BD TOPO et ADMIN EXPRESS, DREAL SRCE 2014 et inventaires humides, Cerema Cartofriches. Les couvertures écologiques ne sont pas validées. L’OCS GE, lorsqu’elle est présente dans le lot, renseigne l’occupation cartographique sans prouver une continuité fonctionnelle.</p>
        <ul>{data.limitations.map((limit) => <li key={limit}>{limit}</li>)}</ul>
      </details>
    </div>
  </aside>
}
