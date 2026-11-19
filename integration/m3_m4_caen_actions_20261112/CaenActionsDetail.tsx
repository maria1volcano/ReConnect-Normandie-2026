import { useEffect, useState } from 'react'

interface StudyPriority { niveau: number | null; libelle: string; couleur: string; note: string }
interface ActionOption {
  action_id: string; regle_id: string; titre: string; titre_etude?: string
  statut_instruction: string; statut_scientifique: string; justification: string; observations: string
  conditions_manquantes: string[]; prochaines_etapes?: string[]; piste_existante_id: string | null
}
interface Decision {
  priorite_etude_interventions: StudyPriority; diagnostic_territorial: string; orientation: string
  action_principale: ActionOption | null; motif_absence_action_principale: string | null
  actions_complementaires: ActionOption[]; motif_absence_complementaires: string; options_actions: ActionOption[]
  conditions_validation_avant_travaux: string[]; pistes_existantes_ids: string[]
}
interface Fiche {
  maille_id: string; grid_version: string; territory_id: string; secteur: string
  decision_interventions: Decision; priorite_ecologique: { conclusion: string }
  diagnostic_techniciens: { nb_evenements_observes: number; nb_evenements_exclusifs_observes: number }
}

function StudyAction({ action }: { action: ActionOption }) {
  return <>
    <h3>{action.action_id} / {action.regle_id} — {action.titre_etude ?? action.titre}</h3>
    <p><strong>Étude indicative à instruire.</strong> Statut scientifique de {action.regle_id} : {action.statut_scientifique.replaceAll('_', ' ')}.</p>
    <p>{action.justification}</p>
    <ol>{action.prochaines_etapes?.map((step) => <li key={step}>{step}</li>)}</ol>
    <p>Aucune construction ni intervention de travaux validée.</p>
  </>
}

export function CaenActionsDetail({ cellId, gridVersion, territoryId }: { cellId: string; gridVersion: string; territoryId: string }) {
  const [fiche, setFiche] = useState<Fiche | null>(null), [error, setError] = useState(false)
  useEffect(() => {
    const controller = new AbortController()
    setFiche(null); setError(false)
    const query = new URLSearchParams({ grid_version: gridVersion, territory_id: territoryId })
    void fetch(`/__internal/m2/caen/fiches/${encodeURIComponent(cellId)}?${query}`, { signal: controller.signal })
      .then((r) => { if (!r.ok) throw new Error('Fiche indisponible'); return r.json() })
      .then((f: Fiche) => {
        if (controller.signal.aborted) return
        if (f.maille_id !== cellId || f.grid_version !== gridVersion || f.territory_id !== territoryId || !f.decision_interventions) throw new Error('Fiche incompatible')
        setFiche(f)
      }).catch(() => { if (!controller.signal.aborted) setError(true) })
    return () => controller.abort()
  }, [cellId, gridVersion, territoryId])
  const decision = fiche?.decision_interventions
  return <aside className="zone-detail" data-maille-id={fiche?.maille_id} aria-labelledby="caen-actions-title"><div className="detail-content">
    <h2 id="caen-actions-title">{fiche?.secteur ?? 'Fiche territoriale'}</h2>
    {error ? <p role="alert">La fiche n'a pas pu être chargée pour ce territoire et cette version.</p> : !fiche || !decision ? <p role="status">Chargement…</p> : <>
      <p><strong>Priorité d'étude indicative : {decision.priorite_etude_interventions.libelle}</strong></p>
      <p>{decision.diagnostic_territorial}</p>
      <p><strong>Orientation :</strong> {decision.orientation}</p>
      <section aria-label="Action principale à l'étude">
        {decision.action_principale ? <StudyAction action={decision.action_principale} /> : <>
          <h3>Aucune intervention sélectionnée</h3><p>{decision.motif_absence_action_principale}</p>
        </>}
      </section>
      <section aria-label="Actions complémentaires envisageables"><h3>Actions complémentaires envisageables</h3>
        {decision.actions_complementaires.length ? decision.actions_complementaires.map((a) => <StudyAction key={a.action_id} action={a} />) : <p>{decision.motif_absence_complementaires}</p>}
      </section>
      <h3>Conditions de validation avant travaux</h3>
      <ul>{decision.conditions_validation_avant_travaux.map((c) => <li key={c}>{c}</li>)}</ul>
      <p><strong>Priorité écologique D/S : {fiche.priorite_ecologique.conclusion === 'indeterminee' ? 'indéterminée' : fiche.priorite_ecologique.conclusion}.</strong> Le rang d'étude ci-dessus ne modifie pas D/S et ne valide aucune règle R1–R4.</p>
      <details className="detail-expandable"><summary>Pistes existantes, justifications et conditions manquantes</summary>
        <p>{decision.pistes_existantes_ids.length} pistes historiques traçables dans cette maille. Une piste conservée n'est pas une action activée.</p>
        {decision.options_actions.map((a) => <div key={a.action_id}>
          <h4>{a.action_id} / {a.regle_id} — {a.titre}</h4>
          <p>Instruction : {a.statut_instruction.replaceAll('_', ' ')} ; statut scientifique : {a.statut_scientifique.replaceAll('_', ' ')}.</p>
          <p>{a.observations}</p><p>{a.justification}</p>
          <ul>{a.conditions_manquantes.map((c) => <li key={c}>{c}</li>)}</ul>
          <p>{a.piste_existante_id ? 'Piste historique conservée et référencée dans le lot.' : 'Aucune piste historique qualifiable pour cette famille.'}</p>
        </div>)}
      </details>
      <details className="detail-expandable"><summary>Observations SIG et sources</summary>
        <p>{fiche.diagnostic_techniciens.nb_evenements_observes} événements locaux ; {fiche.diagnostic_techniciens.nb_evenements_exclusifs_observes} comptes exclusifs. Ce sont des intersections XY et non un décompte d'obstacles confirmés.</p>
        <p>{cellId} · {gridVersion} · {territoryId}</p>
        <p>IGN, DREAL/SRCE et Cerema ; sources, précision, versions et observations détaillées dans la fiche JSON et le manifeste. Les observations OCS GE restent un contexte ; elles ne changent pas les couleurs V1.</p>
      </details>
    </>}
  </div></aside>
}
