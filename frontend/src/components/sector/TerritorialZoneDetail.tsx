import { useEffect, useState } from 'react'
import { loadM4CellBundle, type M4CellBundle } from '../../integrations/m4Adapter'

interface Props {
  mailleId: string
  gridVersion: string
  territoryId: string
}

function formatArea(value: number): string {
  return value >= 1_000_000
    ? `${(value / 1_000_000).toLocaleString('fr-FR', { maximumFractionDigits: 2 })} km²`
    : `${value.toLocaleString('fr-FR', { maximumFractionDigits: 0 })} m²`
}

export function TerritorialZoneDetail({ mailleId, gridVersion, territoryId }: Props) {
  const [data, setData] = useState<M4CellBundle | null>(null)
  const [state, setState] = useState<'loading' | 'available' | 'unavailable'>('loading')

  useEffect(() => {
    const controller = new AbortController()
    setData(null)
    setState('loading')
    void loadM4CellBundle(gridVersion, mailleId, territoryId, controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) {
          setData(result)
          setState('available')
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) setState('unavailable')
      })
    return () => controller.abort()
  }, [gridVersion, mailleId, territoryId])

  if (state !== 'available' || !data) {
    return (
      <aside className="zone-detail" aria-live="polite">
        <div className="detail-state">
          <p className="context-label">Fiche territoriale M2</p>
          <h2>{mailleId}</h2>
          <p>{state === 'loading' ? 'Chargement de la fiche…' : 'Fiche indisponible pour cette version de grille.'}</p>
        </div>
      </aside>
    )
  }

  const leads = data.investigations.filter((item) => item.lead_status === 'a_etudier')
  return (
    <aside className="zone-detail" aria-labelledby="territorial-detail-title">
      <div className="detail-content">
        <div className="detail-header">
          <p className="context-label">Fiche territoriale réelle</p>
          <h2 id="territorial-detail-title">{data.municipalities.map((item) => item.nom).join(', ')}</h2>
          <div className="detail-status"><span className="detail-status-label">Maille :</span><span className="detail-status-value">{data.maille_id}</span></div>
          <div className="detail-status"><span className="detail-status-label">Surface :</span><span className="detail-status-value">{formatArea(data.area_m2)}</span></div>
          <div className="detail-status"><span className="detail-status-label">Grille :</span><span className="detail-status-value">{data.grid_version}</span></div>
        </div>

        <section className="detail-section">
          <h3 className="detail-section-title">Ordre de vérification documentaire</h3>
          <p className="ecological-priority-current">{data.documentary.rule} — {data.documentary.title}</p>
          <p>{data.documentary.reason}</p>
          <p className="detail-note">Classification exploratoire : elle ne constitue pas une priorité écologique validée.</p>
        </section>

        <section className="detail-section">
          <h3 className="detail-section-title">Priorité écologique — non évaluée</h3>
          <p className="ecological-priority-current">Indéterminée</p>
          <p>Méthode scientifique non validée pour cette classification. Aucune recommandation de restauration n’est produite.</p>
        </section>

        <section className="detail-section">
          <h3 className="detail-section-title">Croisements géométriques observés</h3>
          <div className="indicators-grid">
            <div className="indicator-item"><span className="indicator-label">Événements locaux</span><span className="indicator-value">{data.geometric_observations.local_event_count}</span></div>
            <div className="indicator-item"><span className="indicator-label">Propriétaires canoniques</span><span className="indicator-value">{data.geometric_observations.canonical_event_count}</span></div>
          </div>
          {data.geometric_observations.local_event_count === 0 && <p className="detail-note">Zéro événement observé ne démontre pas une absence de conflit écologique.</p>}
        </section>

        <section className="detail-section">
          <h3 className="detail-section-title">Pistes d’investigation documentaire</h3>
          {leads.length === 0 ? <p>Données insuffisantes pour qualifier une piste locale.</p> : leads.map((lead) => (
            <details className="detail-expandable" key={`${lead.rule_id}:${lead.action_id}`}>
              <summary className="detail-expandable-header"><h4 className="detail-section-title">{lead.rule_id} / {lead.action_id} — {lead.title}</h4></summary>
              <div className="detail-expandable-content">
                <p><strong>Statut scientifique : non évaluable.</strong></p>
                <p>{lead.evidence}</p><p>{lead.reason}</p>
                <ul>{lead.missing_conditions.map((condition) => <li key={condition}>{condition}</li>)}</ul>
              </div>
            </details>
          ))}
        </section>

        <details className="detail-expandable">
          <summary className="detail-expandable-header"><h3 className="detail-section-title">Sources, qualité et limites</h3></summary>
          <div className="detail-expandable-content">
            <p>IGN BD TOPO et ADMIN EXPRESS ; DREAL SRCE 2014 et inventaires de zones humides ; Cerema Cartofriches.</p>
            <ul>{data.limitations.map((limit) => <li key={limit}>{limit}</li>)}</ul>
          </div>
        </details>
      </div>
    </aside>
  )
}
