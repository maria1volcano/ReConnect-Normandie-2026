import { useState, useEffect } from 'react'
import type { PriorityExamen, StatutAnalyse, ZoneDiagnosticBundle } from '../../types/hexagon'
import { loadZoneDiagnostic, loadM1Measurements, loadOCSMeasurements, type M1Measurements, type OCSMeasurement } from '../../integrations/geojsonAdapter'
import { ActionSuggestions } from './ActionSuggestions'
import { ConflictsPanel } from './ConflictsPanel'

interface ZoneDetailProps {
  selectedHexagonId?: string | null
  testModeEnabled?: boolean
  isRealGrid?: boolean
}

// Extract short readable label from full maille_id
function getShortLabel(maille_id: string): string {
  // Extract row and column for readable label: "R6425-C495"
  const match = maille_id.match(/R\+(\d+)-C\+(\d+)/)
  if (match) {
    return `R${match[1]}-C${match[2]}`
  }
  return maille_id
}

// Format number for French readers
function formatNumber(value: number | null, decimals: number = 1): string {
  if (value === null || value === undefined) return 'Donnée indisponible'
  return value.toLocaleString('fr-FR', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

// Format area in km² if large enough
function formatArea(value: number | null): string {
  if (value === null || value === undefined) return 'Donnée indisponible'
  if (value >= 1000000) {
    return `${formatNumber(value / 1000000, 2)} km²`
  }
  return `${formatNumber(value, 0)} m²`
}

// Format length in km if large enough
function formatLength(value: number | null): string {
  if (value === null || value === undefined) return 'Donnée indisponible'
  if (value >= 1000) {
    return `${formatNumber(value / 1000, 2)} km`
  }
  return `${formatNumber(value, 0)} m`
}

export function ZoneDetail({ selectedHexagonId, testModeEnabled = false, isRealGrid = false }: ZoneDetailProps) {
  const [bundle, setBundle] = useState<ZoneDiagnosticBundle | null>(null)
  const [m1Measurements, setM1Measurements] = useState<M1Measurements | null>(null)
  const [ocsMeasurements, setOCSMeasurements] = useState<OCSMeasurement[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)
  const diagnostic = bundle?.diagnostic ?? null

  useEffect(() => {
    let cancelled = false

    if (!selectedHexagonId) {
      setBundle(null)
      setM1Measurements(null)
      setOCSMeasurements([])
      setError(false)
      return () => {
        cancelled = true
      }
    }

    setBundle(null)
    setM1Measurements(null)
    setOCSMeasurements([])
    setLoading(true)
    setError(false)

    void (async () => {
      try {
        if (isRealGrid) {
          // Load M1 measurements for real grid
          const [measurements, ocs] = await Promise.all([
            loadM1Measurements(selectedHexagonId),
            loadOCSMeasurements(selectedHexagonId),
          ])
          if (!cancelled) {
            setM1Measurements(measurements)
            setOCSMeasurements(ocs)
            setLoading(false)
          }
        } else {
          // Load TEST diagnostic data
          const result = await loadZoneDiagnostic(selectedHexagonId, testModeEnabled)
          if (!cancelled) {
            setBundle(result)
            setLoading(false)
          }
        }
      } catch (err) {
        console.error('[ZoneDetail] Erreur chargement diagnostic:', err)
        if (!cancelled) {
          setError(true)
          setLoading(false)
        }
      }
    })()

    return () => {
      cancelled = true
    }
  }, [selectedHexagonId, testModeEnabled, isRealGrid])

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
      ) : isRealGrid ? (
        <div className="detail-content">
          <div className="detail-header">
            <span className="detail-icon" aria-hidden="true">
              <span />
            </span>
            <p className="context-label">Fiche maille réelle M1</p>
            <h2 id="zone-detail-title">{getShortLabel(selectedHexagonId)}</h2>
            <div className="detail-badge detail-badge--info" aria-label="État des données">
              <span>Zone pilote provisoire</span>
            </div>
            <div className="detail-status">
              <span className="detail-status-label">Maille :</span>
              <span className="detail-status-value">{selectedHexagonId}</span>
            </div>
            {m1Measurements && (
              <>
                <div className="detail-status">
                  <span className="detail-status-label">Version grille :</span>
                  <span className="detail-status-value">{m1Measurements.grid_version}</span>
                </div>
                <div className="detail-status">
                  <span className="detail-status-label">Statut :</span>
                  <span className="detail-status-value">Analyse scientifique en attente</span>
                </div>
              </>
            )}
          </div>

          {loading && (
            <div className="detail-state" role="status">
              <p>Chargement des mesures géographiques M1…</p>
            </div>
          )}

          {!loading && (error || !m1Measurements) && (
            <div className="detail-state" role="status">
              <p>Mesures géographiques indisponibles pour cette maille.</p>
            </div>
          )}

          {m1Measurements && (
            <div className="detail-section">
              <h3 className="detail-section-title">Mesures géographiques M1</h3>
              <div className="indicators-grid">
                <div className="indicator-item">
                  <span className="indicator-label">Surface réelle</span>
                  <span className="indicator-value">{formatArea(m1Measurements.cell_area_m2)}</span>
                </div>
                <div className="indicator-item">
                  <span className="indicator-label">Routes</span>
                  <span className="indicator-value">{formatLength(m1Measurements.road_length_m)}</span>
                  <span className="indicator-unit">({m1Measurements.road_object_count} tronçons)</span>
                </div>
                <div className="indicator-item">
                  <span className="indicator-label">Réservoirs écologiques</span>
                  <span className="indicator-value">{formatArea(m1Measurements.reservoir_area_m2)}</span>
                  <span className="indicator-unit">({m1Measurements.reservoir_object_count} objets)</span>
                </div>
                <div className="indicator-item">
                  <span className="indicator-label">Corridors</span>
                  <span className="indicator-value">{formatArea(m1Measurements.corridor_area_m2)}</span>
                  <span className="indicator-unit">({m1Measurements.corridor_object_count} objets)</span>
                </div>
                <div className="indicator-item">
                  <span className="indicator-label">Zones construites</span>
                  <span className="indicator-value">{formatArea(m1Measurements.constructed_area_m2)}</span>
                </div>
                <div className="indicator-item">
                  <span className="indicator-label">Haies</span>
                  <span className="indicator-value">{formatLength(m1Measurements.hedge_length_m)}</span>
                  <span className="indicator-unit">({m1Measurements.hedge_object_count} linéaires)</span>
                </div>
                <div className="indicator-item">
                  <span className="indicator-label">Friches</span>
                  <span className="indicator-value">{formatArea(m1Measurements.cartofriches_area_m2)}</span>
                  <span className="indicator-unit">({m1Measurements.cartofriches_site_count} sites)</span>
                </div>
                <div className="indicator-item">
                  <span className="indicator-label">Zones humides</span>
                  <span className="indicator-value">{formatArea(m1Measurements.wetland_area_m2)}</span>
                  <span className="indicator-unit">({m1Measurements.wetland_record_count} objets)</span>
                </div>
                <div className="indicator-item">
                  <span className="indicator-label">Passages à faune (SIPAF)</span>
                  <span className="indicator-value">
                    {m1Measurements.sipaf_record_count === null ? 'Donnée indisponible' : m1Measurements.sipaf_record_count}
                  </span>
                  <span className="indicator-unit">(inventaire non exhaustif)</span>
                </div>
              </div>
            </div>
          )}

          {ocsMeasurements.length > 0 && (
            <div className="detail-section">
              <h3 className="detail-section-title">Occupation du sol (OCS GE 2023)</h3>
              <div className="ocs-list">
                {ocsMeasurements.map((ocs, index) => (
                  <div key={index} className="ocs-item">
                    <div className="ocs-code">{ocs.ocs_code_cs}</div>
                    <div className="ocs-area">{formatArea(ocs.ocs_area_m2)}</div>
                    <div className="ocs-fraction">{(ocs.ocs_fraction_of_cell * 100).toFixed(1)}%</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {m1Measurements && (
            <div className="detail-section">
              <h3 className="detail-section-title">Sources et qualité</h3>
              <div className="quality-display">
                <div className="quality-item">
                  <span className="quality-label">Couverture sol :</span>
                  <span className="quality-value">{m1Measurements.p0_coverage_status}</span>
                </div>
                <div className="quality-item">
                  <span className="quality-label">Haies (BD Haie) :</span>
                  <span className="quality-value">{m1Measurements.bdhaie_coverage_status}</span>
                </div>
                <div className="quality-item">
                  <span className="quality-label">Friches (Cartofriches) :</span>
                  <span className="quality-value">{m1Measurements.cartofriches_coverage_status}</span>
                </div>
                <div className="quality-item">
                  <span className="quality-label">Zones humides (DREAL) :</span>
                  <span className="quality-value">{m1Measurements.wetland_coverage_status}</span>
                </div>
                <div className="quality-item">
                  <span className="quality-label">Unités de mesure :</span>
                  <span className="quality-value">
                    Longueur: {m1Measurements.length_unit}, Aire: {m1Measurements.area_unit}
                  </span>
                </div>
                <div className="quality-item">
                  <span className="quality-label">CRS des calculs :</span>
                  <span className="quality-value">{m1Measurements.measurement_crs}</span>
                </div>
              </div>
            </div>
          )}

          <div className="detail-section">
            <h3 className="detail-section-title">Analyse scientifique</h3>
            <div className="detail-badge detail-badge--warning" aria-label="État des données">
              <span>En attente de validation M2</span>
            </div>
            <p>
              <strong>Les priorités d'examen, les conflits confirmés et les recommandations de
              restauration ne sont pas encore disponibles.</strong> Ces éléments seront produits par M2
              après validation scientifique de la grille et des nomenclatures.
            </p>
            <p className="detail-note">
              <strong>NOTE :</strong> La grille M1 est provisoire. M2 doit valider la pertinence de la
              résolution (1 km²), de l'échelle des sources TVB (2014) et des règles de détection avant
              toute interprétation écologique.
            </p>
          </div>

          <details className="detail-expandable">
            <summary className="detail-expandable-header">
              <h3 className="detail-section-title">Identifiant technique complet</h3>
            </summary>
            <div className="detail-expandable-content">
              <div className="technical-info">
                <span className="technical-label">maille_id :</span>
                <span className="technical-value">{selectedHexagonId}</span>
              </div>
              {m1Measurements && (
                <>
                  <div className="technical-info">
                    <span className="technical-label">Sources utilisées :</span>
                    <span className="technical-value">{m1Measurements.source_ids}</span>
                  </div>
                  <div className="technical-info">
                    <span className="technical-label">Cellule de bordure :</span>
                    <span className="technical-value">{m1Measurements.is_boundary ? 'Oui' : 'Non'}</span>
                  </div>
                </>
              )}
            </div>
          </details>
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

            {diagnostic.enjeux_ecologiques.length === 0 &&
              diagnostic.pressions_humanis.length === 0 &&
              !diagnostic.priorite_explication && (
                <p className="detail-unavailable">Aucun signal détecté ou données insuffisantes</p>
              )}
          </div>

          <ConflictsPanel
            conflicts={bundle?.conflicts ?? []}
            state={bundle?.conflictState ?? 'donnees_manquantes'}
          />

          <ActionSuggestions
            actions={bundle?.actions ?? []}
            state={bundle?.actionState ?? 'donnees_manquantes'}
          />

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

