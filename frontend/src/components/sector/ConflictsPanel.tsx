import type { EvidenceLevel, PotentialConflict, RelatedDataState } from '../../types/hexagon'

interface ConflictsPanelProps {
  conflicts: PotentialConflict[]
  state: RelatedDataState
  loading?: boolean
  error?: boolean
}

const evidenceLabels: Record<EvidenceLevel, string> = {
  croisement_detecte: 'Croisement cartographique détecté',
  conflit_potentiel: 'Conflit potentiel à vérifier',
  obstacle_confirme: 'Obstacle documenté',
  non_concluant: 'Données insuffisantes pour conclure',
}

function stateMessage(state: RelatedDataState): string {
  switch (state) {
    case 'aucun_documente':
      return "Aucun conflit n'est documenté dans ce scénario. Cela ne démontre pas l'absence de problème écologique."
    case 'donnees_manquantes':
      return 'Les données disponibles ne permettent pas de rechercher ou qualifier les conflits potentiels.'
    case 'analyse_non_realisee':
      return "L'analyse des conflits n'a pas été réalisée pour cette maille."
    default:
      return 'Aucun conflit potentiel disponible.'
  }
}

export function ConflictsPanel({ conflicts, state, loading = false, error = false }: ConflictsPanelProps) {
  const countLabel = conflicts.length === 1 ? '1 signal' : `${conflicts.length} signaux`

  return (
    <details className="detail-expandable diagnostic-related-section" open>
      <summary className="detail-expandable-header">
        <span>
          <span className="detail-section-title">Conflits écologiques potentiels</span>
          {!loading && !error && state === 'disponible' && (
            <span className="related-section-count">{countLabel}</span>
          )}
        </span>
      </summary>
      <div className="detail-expandable-content">
        <p className="related-section-intro">
          Ces signaux décrivent des situations cartographiques à examiner. Ils ne prouvent pas une rupture
          écologique fonctionnelle.
        </p>

        {loading ? (
          <p className="related-state">Chargement des conflits potentiels…</p>
        ) : error ? (
          <p className="related-state related-state--error" role="alert">
            Les conflits potentiels n'ont pas pu être chargés.
          </p>
        ) : conflicts.length === 0 ? (
          <p className="related-state">{stateMessage(state)}</p>
        ) : (
          <div className="related-records">
            {conflicts.map((conflict) => (
              <details className="related-record" key={conflict.conflit_id}>
                <summary className="related-record-summary">
                  <span className="related-record-heading">
                    <span className="related-record-title">{conflict.titre}</span>
                    <span className={`related-status related-status--${conflict.evidence_level}`}>
                      {evidenceLabels[conflict.evidence_level]}
                    </span>
                  </span>
                </summary>
                <div className="related-record-content">
                  <p>{conflict.description}</p>
                  <dl className="related-facts">
                    <div>
                      <dt>Identifiant</dt>
                      <dd>{conflict.conflit_id}</dd>
                    </div>
                    <div>
                      <dt>Élément écologique</dt>
                      <dd>{conflict.feature_ecologique}</dd>
                    </div>
                    <div>
                      <dt>Pression ou infrastructure</dt>
                      <dd>{conflict.pression_humaine}</dd>
                    </div>
                    {conflict.methode_detection && (
                      <div>
                        <dt>Élément de détection</dt>
                        <dd>{conflict.methode_detection}</dd>
                      </div>
                    )}
                    <div>
                      <dt>Qualification</dt>
                      <dd>{conflict.qualification}</dd>
                    </div>
                  </dl>

                  <div className="related-detail-block">
                    <h4>Sources disponibles</h4>
                    {conflict.sources.length > 0 ? (
                      <ul>
                        {conflict.sources.map((source) => (
                          <li key={`${conflict.conflit_id}-${source.nom}`}>
                            {source.nom}
                            {source.producteur ? ` — ${source.producteur}` : ''}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p>Aucune source documentée.</p>
                    )}
                  </div>

                  <div className="related-detail-block related-detail-block--limits">
                    <h4>Limites importantes</h4>
                    <ul>
                      {conflict.limites.map((limit) => (
                        <li key={limit}>{limit}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </details>
            ))}
          </div>
        )}
      </div>
    </details>
  )
}
