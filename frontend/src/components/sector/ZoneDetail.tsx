import { useState, useEffect } from 'react'
import type { PriorityExamen, StatutAnalyse, ZoneDiagnosticBundle } from '../../types/hexagon'
import {
  loadZoneDiagnostic,
  loadM1Measurements,
  loadOCSMeasurements,
  loadM1SourceCatalog,
  type M1Measurements,
  type M1SourceCatalog,
  type OCSMeasurement,
} from '../../integrations/geojsonAdapter'
import {
  loadM2CellSummary,
  type M2CellSummary,
} from '../../integrations/m2Adapter'
import {
  ECOLOGICAL_PRIORITY,
  PRIORITY_GRID_VERSION,
  resolveEcologicalPriority,
  type ResolvedEcologicalPriority,
  type ScientificValidationStatus,
} from '../../integrations/priorityAdapter'
import { ActionSuggestions } from './ActionSuggestions'
import { ConflictsPanel } from './ConflictsPanel'

interface ZoneDetailProps {
  selectedHexagonId?: string | null
  testModeEnabled?: boolean
  isRealGrid?: boolean
  gridVersion?: string
  ecologicalPriority?: ResolvedEcologicalPriority | null
}

const validationLabels: Record<ScientificValidationStatus, string> = {
  VALIDATED: 'Validée scientifiquement',
  PENDING: 'Validation scientifique en attente',
  REJECTED: 'Validation scientifique rejetée',
  UNKNOWN: 'Non validée',
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

const coverageLabels: Record<string, { label: string; detail: string; tone: string }> = {
  complete_for_provisional_pilot: {
    label: 'Données disponibles',
    detail: 'Couverture complète de l’emprise pilote provisoire pour les sources géographiques de base.',
    tone: 'available',
  },
  available_bounded_wfs_non_exhaustive: {
    label: 'Couverture partielle',
    detail: 'Extrait borné disponible, mais inventaire non exhaustif.',
    tone: 'partial',
  },
  available_inventory_non_exhaustive: {
    label: 'Couverture partielle',
    detail: 'Inventaire disponible mais non exhaustif : une valeur nulle ne prouve pas une absence réelle.',
    tone: 'partial',
  },
  available_bounded_wfs_heterogeneous_inventory: {
    label: 'Couverture partielle',
    detail: 'Extrait disponible ; couverture, précision et millésimes hétérogènes.',
    tone: 'partial',
  },
  unavailable_authorized_extract_required: {
    label: 'Données non disponibles',
    detail: 'Une extraction autorisée est requise ; la valeur reste indisponible, jamais assimilée à zéro.',
    tone: 'unavailable',
  },
  unavailable_licence_and_resource_unconfirmed: {
    label: 'À vérifier',
    detail: 'Licence et ressource téléchargeable non confirmées ; aucune mesure n’est affichée.',
    tone: 'unknown',
  },
}

function coverageInfo(status: string) {
  return coverageLabels[status] ?? {
    label: 'À vérifier',
    detail: `État de couverture non documenté (${status}).`,
    tone: 'unknown',
  }
}

function OCSRow({ measurement }: { measurement: OCSMeasurement }) {
  const percentage = measurement.ocs_fraction_of_cell * 100
  const barWidth = `${Math.min(100, Math.max(0, percentage))}%`

  return (
    <div className="ocs-item">
      <div className="ocs-row-main">
        <div className="ocs-code">{measurement.ocs_code_cs}</div>
        <div className="ocs-area">{formatArea(measurement.ocs_area_m2)}</div>
        <div className="ocs-fraction">{percentage.toFixed(1)}%</div>
      </div>
      <div className="ocs-bar" aria-label={`${percentage.toFixed(1)} % de la surface de la maille`}>
        <span className="ocs-bar-fill" style={{ width: barWidth }} />
      </div>
    </div>
  )
}

export function ZoneDetail({
  selectedHexagonId,
  testModeEnabled = false,
  isRealGrid = false,
  gridVersion = PRIORITY_GRID_VERSION,
  ecologicalPriority,
}: ZoneDetailProps) {
  const [bundle, setBundle] = useState<ZoneDiagnosticBundle | null>(null)
  const [m1Measurements, setM1Measurements] = useState<M1Measurements | null>(null)
  const [ocsMeasurements, setOCSMeasurements] = useState<OCSMeasurement[]>([])
  const [sourceCatalog, setSourceCatalog] = useState<M1SourceCatalog | null>(null)
  const [m2Summary, setM2Summary] = useState<M2CellSummary | null>(null)
  const [m2State, setM2State] = useState<'idle' | 'loading' | 'available' | 'unavailable'>('idle')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)
  const diagnostic = bundle?.diagnostic ?? null

  useEffect(() => {
    let cancelled = false

    if (!selectedHexagonId) {
      setBundle(null)
      setM1Measurements(null)
      setOCSMeasurements([])
      setSourceCatalog(null)
      setError(false)
      return () => {
        cancelled = true
      }
    }

    setBundle(null)
    setM1Measurements(null)
    setOCSMeasurements([])
    setSourceCatalog(null)
    setLoading(true)
    setError(false)

    void (async () => {
      try {
        if (isRealGrid) {
          // Load M1 measurements for real grid
          const [measurements, ocs, sources] = await Promise.all([
            loadM1Measurements(selectedHexagonId, gridVersion),
            loadOCSMeasurements(selectedHexagonId, gridVersion),
            loadM1SourceCatalog(),
          ])
          if (!cancelled) {
            setM1Measurements(measurements)
            setOCSMeasurements(ocs)
            setSourceCatalog(sources)
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
  }, [selectedHexagonId, testModeEnabled, isRealGrid, gridVersion])

  useEffect(() => {
    const controller = new AbortController()

    if (!selectedHexagonId || !isRealGrid) {
      setM2Summary(null)
      setM2State('idle')
      return () => controller.abort()
    }

    setM2Summary(null)
    setM2State('loading')
    void loadM2CellSummary(selectedHexagonId, controller.signal, gridVersion)
      .then((summary) => {
        setM2Summary(summary)
        setM2State('available')
      })
      .catch((loadError: unknown) => {
        if (loadError instanceof DOMException && loadError.name === 'AbortError') return
        setM2Summary(null)
        setM2State('unavailable')
      })

    return () => controller.abort()
  }, [selectedHexagonId, isRealGrid, gridVersion])

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

  const measurementSourceIds = m1Measurements?.source_ids.split(';').filter(Boolean) ?? []
  const measurementSources = measurementSourceIds.map((sourceId) => ({
    sourceId,
    metadata: sourceCatalog?.sources[sourceId] ?? null,
  }))

  const coverageRows = m1Measurements
    ? [
        ['Sources géographiques de base', m1Measurements.p0_coverage_status],
        ['Haies — BD Haie', m1Measurements.bdhaie_coverage_status],
        ['Passages à faune — SIPAF', m1Measurements.sipaf_coverage_status],
        ['Friches — Cartofriches', m1Measurements.cartofriches_coverage_status],
        ['Zones humides — DREAL', m1Measurements.wetland_coverage_status],
        ['Mares — PRAM', m1Measurements.pram_coverage_status],
        ['Friches — EPFN', m1Measurements.epfn_coverage_status],
      ] as const
    : []

  const sortedOCSMeasurements = [...ocsMeasurements].sort((a, b) => b.ocs_area_m2 - a.ocs_area_m2)
  const mainOCSMeasurements = sortedOCSMeasurements.slice(0, 5)
  const additionalOCSMeasurements = sortedOCSMeasurements.slice(5)
  const currentEcologicalPriority = isRealGrid && selectedHexagonId
    ? ecologicalPriority ?? resolveEcologicalPriority(selectedHexagonId, gridVersion)
    : null
  const priorityDisplay = currentEcologicalPriority
    ? ECOLOGICAL_PRIORITY[currentEcologicalPriority.category]
    : null

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
                  <span className="detail-status-value">Analyse scientifique M2 en attente</span>
                </div>
              </>
            )}
          </div>

          {currentEcologicalPriority && priorityDisplay && (
            <section className="detail-section ecological-priority-section" aria-labelledby="ecological-priority-title">
              <div className="ecological-priority-heading">
                <div>
                  <h3 id="ecological-priority-title" className="detail-section-title">
                    Priorité d'examen écologique
                  </h3>
                  <p>Classification soumise à validation scientifique</p>
                </div>
                <span
                  className="ecological-priority-swatch"
                  style={{ backgroundColor: priorityDisplay.color }}
                  aria-hidden="true"
                />
              </div>

              <p className="ecological-priority-current">
                {currentEcologicalPriority.category === 'INDETERMINATE' &&
                currentEcologicalPriority.resolution_reason !== 'validated'
                  ? 'Priorité indéterminée — méthode scientifique en attente de validation'
                  : priorityDisplay.label}
              </p>

              <dl className="ecological-priority-metadata">
                <div>
                  <dt>Catégorie actuelle</dt>
                  <dd>{priorityDisplay.label}</dd>
                </div>
                <div>
                  <dt>Statut de validation</dt>
                  <dd>{validationLabels[currentEcologicalPriority.scientific_validation]}</dd>
                </div>
                <div>
                  <dt>Fiabilité</dt>
                  <dd>{currentEcologicalPriority.reliability.level}</dd>
                </div>
                {currentEcologicalPriority.method_version && (
                  <div>
                    <dt>Version de méthode</dt>
                    <dd>{currentEcologicalPriority.method_version}</dd>
                  </div>
                )}
              </dl>

              <div className="ecological-priority-explanation">
                <strong>Justification</strong>
                <p>{currentEcologicalPriority.justification ?? 'Aucune justification validée disponible.'}</p>
              </div>

              <div className="ecological-priority-explanation">
                <strong>Limites et incertitudes</strong>
                <p>
                  {currentEcologicalPriority.reliability.uncertainty ??
                    'Le niveau d’incertitude n’est pas documenté.'}
                </p>
                {currentEcologicalPriority.reliability.limitations.length > 0 && (
                  <ul>
                    {currentEcologicalPriority.reliability.limitations.map((limitation) => (
                      <li key={limitation}>{limitation}</li>
                    ))}
                  </ul>
                )}
              </div>

              {currentEcologicalPriority.provenance.length > 0 && (
                <p className="ecological-priority-provenance">
                  Provenance : {currentEcologicalPriority.provenance.join(' · ')}
                </p>
              )}
            </section>
          )}

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

          <section className="detail-section m2-observation-section" aria-labelledby="m2-observation-title">
            <div className="m2-section-heading">
              <div>
                <h3 id="m2-observation-title" className="detail-section-title">Observations géométriques M2</h3>
                <p>Données réelles · consultation interne uniquement</p>
              </div>
              <span className="m2-internal-badge">Interne</span>
            </div>

            {m2State === 'loading' && <p className="m2-service-state">Chargement des observations M2…</p>}

            {(m2State === 'idle' || m2State === 'unavailable') && (
              <div className="m2-unavailable" role="status">
                <strong>Données M2 non chargées</strong>
                <span>Le service local interne est indisponible ou non configuré.</span>
              </div>
            )}

            {m2State === 'available' && m2Summary && (
              <>
                <div className="indicators-grid m2-indicators-grid">
                  <div className="indicator-item">
                    <span className="indicator-label">Observations liées</span>
                    <span className="indicator-value">{m2Summary.observations.distinctEventCount}</span>
                    <span className="indicator-unit">événements distincts dans cette maille</span>
                  </div>
                  <div className="indicator-item">
                    <span className="indicator-label">Relations événement–maille</span>
                    <span className="indicator-value">{m2Summary.observations.relationshipCount}</span>
                    <span className="indicator-unit">liens locaux, pas un total écologique</span>
                  </div>
                  <div className="indicator-item">
                    <span className="indicator-label">ENJ-01</span>
                    <span className="indicator-value">Inconnu</span>
                    <span className="indicator-unit">couverture non attestée</span>
                  </div>
                  <div className="indicator-item">
                    <span className="indicator-label">ENJ-02</span>
                    <span className="indicator-value">
                      {m2Summary.indicators.enj02.availability === 'observed' ? 'Présence observée' : 'Inconnu'}
                    </span>
                    <span className="indicator-unit">indicateur descriptif disponible</span>
                  </div>
                </div>
                <div className="m2-qualification">
                  <span>Qualification</span>
                  <strong>Observations géométriques détectées</strong>
                </div>
                <p className="detail-note">
                  {m2Summary.observations.distinctEventCount === 0
                    ? 'Aucun événement documenté dans cette maille ne démontre une absence écologique. '
                    : ''}
                  Couverture et complétude inconnues. Priorités scientifiques et actions de restauration non calculées.
                </p>
              </>
            )}
          </section>

          {ocsMeasurements.length > 0 && (
            <div className="detail-section">
              <div className="ocs-heading">
                <div>
                  <h3 className="detail-section-title">Occupation du sol</h3>
                  <p>OCS GE 2023 · catégories classées par surface décroissante</p>
                </div>
              </div>
              <div className="ocs-list">
                {mainOCSMeasurements.map((measurement) => (
                  <OCSRow key={measurement.ocs_code_cs} measurement={measurement} />
                ))}
              </div>
              {additionalOCSMeasurements.length > 0 && (
                <details className="ocs-more">
                  <summary>Afficher les {additionalOCSMeasurements.length} autres catégories</summary>
                  <div className="ocs-list ocs-list--additional">
                    {additionalOCSMeasurements.map((measurement) => (
                      <OCSRow key={measurement.ocs_code_cs} measurement={measurement} />
                    ))}
                  </div>
                </details>
              )}
              <p className="ocs-note">
                Les codes officiels sont conservés tels que fournis. L'export M1 ne contient pas de libellés de nomenclature.
              </p>
            </div>
          )}

          {m1Measurements && (
            <>
              <details className="detail-expandable provenance-section">
                <summary className="detail-expandable-header">
                  <h3 className="detail-section-title">Sources et provenance</h3>
                </summary>
                <div className="detail-expandable-content">
                  <p className="detail-section-intro">
                    Sources M1 effectivement associées aux mesures de cette maille.
                  </p>
                  <ul className="sources-list">
                    {measurementSources.map(({ sourceId, metadata }) => (
                      <li className="source-item" key={sourceId}>
                        <div className="source-name">{metadata?.name ?? sourceId}</div>
                        <div className="source-meta">
                          {metadata ? `${metadata.producer} · ${metadata.reference_year ?? 'Année non précisée'}` : 'Provenance à vérifier'}
                        </div>
                        <div className="source-meta">Identifiant M1 : {sourceId}</div>
                        {metadata?.version && <div className="source-meta">Version : {metadata.version}</div>}
                        {metadata?.license && <div className="source-meta">Licence : {metadata.license}</div>}
                        {metadata?.geographic_coverage && (
                          <div className="source-meta">Couverture : {metadata.geographic_coverage}</div>
                        )}
                        {metadata?.official_url && (
                          <a className="source-link" href={metadata.official_url} target="_blank" rel="noreferrer">
                            Consulter la source officielle
                          </a>
                        )}
                        {metadata?.restrictions && <p className="source-desc">{metadata.restrictions}</p>}
                      </li>
                    ))}
                  </ul>
                  {!sourceCatalog && <p className="detail-unavailable">Métadonnées de provenance indisponibles.</p>}
                </div>
              </details>

              <details className="detail-expandable quality-limitations-section">
                <summary className="detail-expandable-header">
                  <h3 className="detail-section-title">Qualité et limites des données</h3>
                </summary>
                <div className="detail-expandable-content">
                  <div className="coverage-list">
                    {coverageRows.map(([label, status]) => {
                      const info = coverageInfo(status)
                      return (
                        <div className="coverage-item" key={label}>
                          <div className="coverage-heading">
                            <span>{label}</span>
                            <span className={`coverage-state coverage-state--${info.tone}`}>{info.label}</span>
                          </div>
                          <p>{info.detail}</p>
                        </div>
                      )
                    })}
                  </div>
                  <p className="detail-note">
                    Les intersections sont fusionnées avant calcul pour éviter les doubles comptes. Les cellules de bord utilisent leur surface réelle. Un zéro signifie qu’aucun objet documenté n’intersecte la maille dans la source utilisée ; il ne prouve pas l’absence réelle lorsque l’inventaire est incomplet.
                  </p>
                  <div className="method-info">
                    <span className="method-label">Calculs :</span>
                    <span className="method-value">{m1Measurements.measurement_crs} · longueurs en {m1Measurements.length_unit} · aires en {m1Measurements.area_unit}</span>
                  </div>
                </div>
              </details>
            </>
          )}

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
                <span>DONNÉES SYNTHÉTIQUES — DÉMONSTRATION</span>
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

