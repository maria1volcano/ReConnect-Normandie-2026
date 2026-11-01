import { useState, useEffect } from 'react'
import type { DiagnosticDetail, PriorityExamen, StatutAnalyse } from '../../types/hexagon'
import { loadZoneDiagnostic } from '../../integrations/geojsonAdapter'

interface ZoneDetailProps {
  selectedHexagonId?: string | null
  testModeEnabled?: boolean
}

export function ZoneDetail({ selectedHexagonId, testModeEnabled = false }: ZoneDetailProps) {
  const [diagnostic, setDiagnostic] = useState<DiagnosticDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)

  useEffect(() => {
    if (!selectedHexagonId) {
      setDiagnostic(null)
      setError(false)
      return
    }

    setLoading(true)
    setError(false)

    void (async () => {
      try {
        const result = await loadZoneDiagnostic(selectedHexagonId, testModeEnabled)
        setDiagnostic(result)
        setLoading(false)
      } catch (err) {
        console.error('[ZoneDetail] Erreur chargement diagnostic:', err)
        setError(true)
        setLoading(false)
      }
    })()
  }, [selectedHexagonId, testModeEnabled])

  const getPriorityLabel = (priority?: PriorityExamen): string => {
    switch (priority) {
      case 'elevee':
        return 'Élevée'
      case 'moderee':
        return 'Modérée'
      case 'faible':
        return 'Faible'
      case 'indeterminee':
        return 'Indéterminée'
      default:
        return 'Non disponible'
    }
  }

  const getPriorityColor = (priority?: PriorityExamen): string => {
    switch (priority) {
      case 'elevee':
        return '#C76A3A'
      case 'moderee':
        return '#D7AB42'
      case 'faible':
        return '#91AD8C'
      case 'indeterminee':
        return '#9DAA9B'
      default:
        return '#B8B8B8'
    }
  }

  const getQualiteLabel = (niveau: string): string => {
    switch (niveau) {
      case 'suffisante':
        return 'Suffisante'
      case 'partielle':
        return 'Partielle'
      case 'insuffisante':
        return 'Insuffisante'
      default:
        return niveau
    }
  }

  const getStatutAnalyseLabel = (statut: StatutAnalyse): string => {
    switch (statut) {
      case 'calculee':
        return 'Calculée'
      case 'donnees_insuffisantes':
        return 'Données insuffisantes'
      case 'analyse_non_realisee':
        return 'Analyse non réalisée'
      default:
        return statut
    }
  }

  return (
    <aside className="zone-detail" aria-labelledby="zone-detail-title">
      <div className="detail-handle" aria-hidden="true" />

      {!selectedHexagonId ? (
        <div className="detail-state">
          <span className="detail-icon" aria-hidden="true">
            <span />
          </span>
          <p className="context-label">Fiche secteur</p>
          <h2 id="zone-detail-title">Sélectionnez un secteur</h2>
          <p>
            Choisissez une maille sur la carte pour consulter sa priorité d'examen, ses diagnostics,
            la qualité des données et les pistes associées.
          </p>
        </div>
      ) : loading ? (
        <div className="detail-state">
          <span className="detail-icon" aria-hidden="true">
            <span />
          </span>
          <p className="context-label">Fiche maille</p>
          <h2 id="zone-detail-title">{selectedHexagonId}</h2>
          <p className="detail-loading">Chargement des données...</p>
        </div>
      ) : error || !diagnostic ? (
        <div className="detail-state">
          <span className="detail-icon" aria-hidden="true">
            <span />
          </span>
          <p className="context-label">Fiche maille</p>
          <h2 id="zone-detail-title">{selectedHexagonId}</h2>
          <div className="detail-badge" aria-label="État des données">
            <span>Données de diagnostic en attente</span>
          </div>
          <p>
            Les données détaillées de cette maille (priorité d'examen, diagnostics, qualité des
            données et pistes d'action) seront disponibles une fois les exports M2/M4 intégrés.
          </p>
          {testModeEnabled && (
            <p className="detail-note">
              <strong>NOTE :</strong> Mode TEST activé mais aucune donnée de diagnostic TEST n'est
              disponible pour cette maille.
            </p>
          )}
        </div>
      ) : (
        <div className="detail-content">
          <div className="detail-header">
            <span className="detail-icon" aria-hidden="true">
              <span />
            </span>
            <p className="context-label">Fiche secteur</p>
            {diagnostic.priorite_examen && (
              <div className="priority-display">
                <div
                  className="priority-indicator"
                  style={{ backgroundColor: getPriorityColor(diagnostic.priorite_examen) }}
                  aria-hidden="true"
                />
                <div className="priority-info">
                  <span className="priority-label">{getPriorityLabel(diagnostic.priorite_examen)}</span>
                  <span className="priority-category">Priorité d'examen</span>
                </div>
              </div>
            )}
            <div className="detail-status">
              <span className="detail-status-label">Maille :</span>
              <span className="detail-status-value">{diagnostic.maille_id}</span>
            </div>
            {diagnostic.test_data && (
              <div className="detail-badge detail-badge--warning" aria-label="État des données">
                <span>DONNÉES TEST — NON VALIDÉES</span>
              </div>
            )}
            <div className="detail-status">
              <span className="detail-status-label">Statut :</span>
              <span className="detail-status-value">{getStatutAnalyseLabel(diagnostic.statut_analyse)}</span>
            </div>
          </div>

          <div className="detail-section">
            <h3 className="detail-section-title">Pourquoi ce secteur est-il signalé ?</h3>

            {diagnostic.priorite_explication && (
              <p className="detail-explanation">{diagnostic.priorite_explication}</p>
            )}

            {diagnostic.enjeux_ecologiques.length > 0 && (
              <div className="detail-subsection">
                <h4 className="detail-subsection-title">Enjeux écologiques</h4>
                <ul className="detail-list">
                  {diagnostic.enjeux_ecologiques.map((enjeu, index) => (
                    <li key={index}>{enjeu}</li>
                  ))}
                </ul>
              </div>
            )}

            {diagnostic.pressions_humanis.length > 0 && (
              <div className="detail-subsection">
                <h4 className="detail-subsection-title">Pressions humaines</h4>
                <ul className="detail-list">
                  {diagnostic.pressions_humanis.map((pression, index) => (
                    <li key={index}>{pression}</li>
                  ))}
                </ul>
              </div>
            )}

            {diagnostic.fragmentation_conflits.length > 0 && (
              <div className="detail-subsection">
                <h4 className="detail-subsection-title">Fragmentation et conflits potentiels</h4>
                <ul className="detail-list">
                  {diagnostic.fragmentation_conflits.map((conflit, index) => (
                    <li key={index}>
                      <span className="conflit-type">{conflit.type}</span>
                      {conflit.description && <span className="conflit-desc">: {conflit.description}</span>}
                      {conflit.evidence_level && (
                        <span className="conflit-level"> ({conflit.evidence_level})</span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {diagnostic.enjeux_ecologiques.length === 0 &&
              diagnostic.pressions_humanis.length === 0 &&
              diagnostic.fragmentation_conflits.length === 0 &&
              !diagnostic.priorite_explication && (
                <p className="detail-unavailable">Aucun signal détecté ou données insuffisantes</p>
              )}
          </div>

          <details className="detail-expandable">
            <summary className="detail-expandable-header">
              <h3 className="detail-section-title">Indicateurs environnementaux</h3>
            </summary>
            <div className="detail-expandable-content">
              <div className="indicators-grid">
                <div className="indicator-item">
                  <span className="indicator-label">Enjeu écologique</span>
                  <span className="indicator-value">
                    {diagnostic.indicateurs.enjeu_ecologique?.valeur || 'Non disponible'}
                  </span>
                </div>
                <div className="indicator-item">
                  <span className="indicator-label">Fragmentation</span>
                  <span className="indicator-value">
                    {diagnostic.indicateurs.fragmentation?.valeur || 'Non disponible'}
                    {diagnostic.indicateurs.fragmentation?.unite && (
                      <span className="indicator-unit"> {diagnostic.indicateurs.fragmentation.unite}</span>
                    )}
                  </span>
                </div>
                <div className="indicator-item">
                  <span className="indicator-label">Pressions</span>
                  <span className="indicator-value">
                    {diagnostic.indicateurs.pressions?.valeur || 'Non disponible'}
                  </span>
                </div>
                <div className="indicator-item">
                  <span className="indicator-label">Fiabilité</span>
                  <span className="indicator-value">
                    {diagnostic.indicateurs.fiabilite?.valeur || 'Non disponible'}
                  </span>
                </div>
              </div>
            </div>
          </details>

          <div className="detail-section">
            <h3 className="detail-section-title">Qualité et fiabilité des données</h3>
            <div className="quality-display">
              <div className="quality-item">
                <span className="quality-label">Niveau :</span>
                <span className="quality-value">{getQualiteLabel(diagnostic.qualite.niveau)}</span>
              </div>
              <div className="quality-item">
                <span className="quality-label">Couverture :</span>
                <span className="quality-value">{diagnostic.qualite.couverture}</span>
              </div>
              {diagnostic.qualite.echelle && (
                <div className="quality-item">
                  <span className="quality-label">Échelle :</span>
                  <span className="quality-value">{diagnostic.qualite.echelle}</span>
                </div>
              )}
              {diagnostic.qualite.annees && diagnostic.qualite.annees.length > 0 && (
                <div className="quality-item">
                  <span className="quality-label">Années :</span>
                  <span className="quality-value">{diagnostic.qualite.annees.join(', ')}</span>
                </div>
              )}
              {diagnostic.qualite.champs_manquants && diagnostic.qualite.champs_manquants.length > 0 && (
                <div className="quality-item">
                  <span className="quality-label">Champs manquants :</span>
                  <span className="quality-value">{diagnostic.qualite.champs_manquants.join(', ')}</span>
                </div>
              )}
            </div>
          </div>

          <details className="detail-expandable">
            <summary className="detail-expandable-header">
              <h3 className="detail-section-title">Sources et limites</h3>
            </summary>
            <div className="detail-expandable-content">
              {diagnostic.qualite.sources.length > 0 ? (
                <ul className="sources-list">
                  {diagnostic.qualite.sources.map((source, index) => (
                    <li key={index} className="source-item">
                      <div className="source-name">{source.nom}</div>
                      {source.producteur && <div className="source-meta">Producteur : {source.producteur}</div>}
                      {source.annee && <div className="source-meta">Année : {source.annee}</div>}
                      {source.echelle && <div className="source-meta">Échelle : {source.echelle}</div>}
                      {source.licence && <div className="source-meta">Licence : {source.licence}</div>}
                      {source.description && <div className="source-desc">{source.description}</div>}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="detail-unavailable">Aucune source documentée</p>
              )}
              <div className="method-info">
                <span className="method-label">Version méthode :</span>
                <span className="method-value">{diagnostic.method_version}</span>
              </div>
            </div>
          </details>

          {diagnostic.test_data && (
            <p className="detail-note">
              <strong>NOTE :</strong> Cette maille fait partie des données de démonstration TEST et ne
              représente pas un résultat scientifique validé. Les valeurs affichées sont fictives et ne
              doivent pas être utilisées pour des décisions réelles.
            </p>
          )}
        </div>
      )}
    </aside>
  )
}

