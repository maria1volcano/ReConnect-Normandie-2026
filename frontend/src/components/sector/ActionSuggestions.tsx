import type {
  ActionStatut,
  RelatedDataState,
  RestorationActionSuggestion,
} from '../../types/hexagon'

interface ActionSuggestionsProps {
  actions: RestorationActionSuggestion[]
  state: RelatedDataState
  loading?: boolean
  error?: boolean
}

const actionStatusLabels: Record<ActionStatut, string> = {
  etayee_pour_examen: 'Piste étayée pour examen',
  conditionnelle: 'Piste à étudier — validation nécessaire',
  non_retenue_par_regle: 'Non retenue par la règle',
  non_evaluable: 'Non évaluable avec les données disponibles',
}

function stateMessage(state: RelatedDataState): string {
  switch (state) {
    case 'aucun_documente':
      return "Aucune piste d'action n'est associée à ce scénario. Cela ne préjuge pas des besoins du terrain."
    case 'donnees_manquantes':
      return "Les données disponibles ne permettent pas d'évaluer les familles d'actions."
    case 'analyse_non_realisee':
      return "L'évaluation des familles d'actions n'a pas été réalisée pour cette maille."
    default:
      return "Aucune piste d'action disponible."
  }
}

export function ActionSuggestions({ actions, state, loading = false, error = false }: ActionSuggestionsProps) {
  const countLabel = actions.length === 1 ? '1 piste' : `${actions.length} pistes`

  return (
    <details className="detail-expandable diagnostic-related-section" open>
      <summary className="detail-expandable-header">
        <span>
          <span className="detail-section-title">Pistes d'actions à étudier</span>
          {!loading && !error && state === 'disponible' && (
            <span className="related-section-count">{countLabel}</span>
          )}
        </span>
      </summary>
      <div className="detail-expandable-content">
        <p className="related-section-intro">
          Ces familles d'actions sont des possibilités conditionnelles. Elles ne constituent ni une décision de
          travaux ni une recommandation scientifiquement validée.
        </p>

        {loading ? (
          <p className="related-state">Chargement des pistes d'actions…</p>
        ) : error ? (
          <p className="related-state related-state--error" role="alert">
            Les pistes d'actions n'ont pas pu être chargées.
          </p>
        ) : actions.length === 0 ? (
          <p className="related-state">{stateMessage(state)}</p>
        ) : (
          <div className="related-records">
            {actions.map((action) => (
              <details className="related-record related-record--action" key={action.action_id}>
                <summary className="related-record-summary">
                  <span className="related-record-heading">
                    <span className="related-record-title">
                      <span className="action-rule">{action.regle_id}</span> — {action.titre}
                    </span>
                    <span className={`related-status related-status--${action.statut}`}>
                      {actionStatusLabels[action.statut]}
                    </span>
                  </span>
                </summary>
                <div className="related-record-content">
                  <dl className="related-facts">
                    <div>
                      <dt>Raison diagnostique</dt>
                      <dd>{action.motif}</dd>
                    </div>
                    <div>
                      <dt>Pertinence potentielle</dt>
                      <dd>{action.pertinence}</dd>
                    </div>
                    <div>
                      <dt>Conflits associés</dt>
                      <dd>{action.conflit_ids.length > 0 ? action.conflit_ids.join(', ') : 'Aucun conflit qualifié'}</dd>
                    </div>
                  </dl>

                  <div className="related-detail-block">
                    <h4>Conditions à vérifier</h4>
                    <ul>
                      {action.conditions_verification.map((condition) => (
                        <li key={condition}>{condition}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="related-detail-block">
                    <h4>Sources disponibles</h4>
                    {action.sources.length > 0 ? (
                      <ul>
                        {action.sources.map((source) => (
                          <li key={`${action.action_id}-${source.nom}`}>
                            {source.nom}
                            {source.producteur ? ` — ${source.producteur}` : ''}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p>Aucune source suffisante pour qualifier cette piste.</p>
                    )}
                  </div>

                  <div className="related-detail-block related-detail-block--limits">
                    <h4>Limites</h4>
                    <ul>
                      {action.limites.map((limit) => (
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
