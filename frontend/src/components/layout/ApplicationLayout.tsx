import { useState, useRef, useEffect, useMemo } from 'react'
import type { Map as MapLibreMap, LngLatBoundsLike } from 'maplibre-gl'
import { PriorityLegend } from '../legend/PriorityLegend'
import { SiteHeader } from './SiteHeader'
import { StudyLegend } from '../legend/StudyLegend'
import { DocumentaryLegend } from '../legend/DocumentaryLegend'
import { DepartmentPanel } from '../map/DepartmentPanel'
import { RegionMap } from '../map/RegionMap'
import { RealGridLayer } from '../map/RealGridLayer'
import type { DepartmentCode } from '../map/normandyDepartments'
import { ZoneDetail } from '../sector/ZoneDetail'
import { TerritorialZoneDetail } from '../sector/TerritorialZoneDetail'
import { loadRealGrid, loadTestGrid, type RealGridData } from '../../integrations/geojsonAdapter'
import { navigate } from '../../app/router'
import { loadCells } from '../../integrations/m4Adapter'
import { mailleIdsForRule, type RuleId } from '../../integrations/catalogueData'
import { priorityFromFeature } from '../../integrations/priorityAdapter'
import { CAEN_TERRITORY_ID } from '../../integrations/gridDatasets'

// Le mode TEST historique (43 mailles pilotes Orne, données synthétiques) reste
// implémenté et ses fichiers/données sont conservés, mais il est retiré de la
// navigation publique : la carte REAL 101 mailles est l'expérience principale.
// Repassez TEST_MODE_UI_ENABLED à true pour réactiver l'interface TEST.
const TEST_MODE_UI_ENABLED = false

// D/S reste séparée du rang indicatif d’étude. Les deux vues sont accessibles.
const REAL_VIEW_SWITCHER_ENABLED = true

interface SelectedGridCell {
  gridVersion: string
  mailleId: string
}

function featureCollectionBounds(
  featureCollection: RealGridData['featureCollection'],
): LngLatBoundsLike | null {
  let west = Infinity
  let south = Infinity
  let east = -Infinity
  let north = -Infinity

  const walk = (coordinates: unknown): void => {
    if (!Array.isArray(coordinates)) return
    const [first, second] = coordinates
    if (typeof first === 'number' && typeof second === 'number') {
      west = Math.min(west, first)
      east = Math.max(east, first)
      south = Math.min(south, second)
      north = Math.max(north, second)
      return
    }
    for (const child of coordinates) walk(child)
  }

  for (const feature of featureCollection.features) {
    if (feature.geometry) walk((feature.geometry as { coordinates?: unknown }).coordinates)
  }

  return Number.isFinite(west) ? [[west, south], [east, north]] : null
}

export function ApplicationLayout() {
  const [selectedDepartment, setSelectedDepartment] = useState<DepartmentCode | null>(null)
  const [hoveredDepartment, setHoveredDepartment] = useState<DepartmentCode | null>(null)
  const [selectedGridCell, setSelectedGridCell] = useState<SelectedGridCell | null>(null)
  const [hoveredRealHexagonId, setHoveredRealHexagonId] = useState<string | null>(null)
  const [realGrid, setRealGrid] = useState<RealGridData | null>(null)
  const [testGrid, setTestGrid] = useState<RealGridData | null>(null)
  const [testModeEnabled, setTestModeEnabled] = useState(false)
  const [showRealGrid, setShowRealGrid] = useState(true)
  const [realView, setRealView] = useState<'documentary' | 'ecological'>('documentary')
  const [realReloadNonce, setRealReloadNonce] = useState(0)
  const [familyHighlight, setFamilyHighlight] = useState<{ ruleId: RuleId; ids: Set<string> } | null>(null)
  const [, setMapRevision] = useState(0)
  const mapRef = useRef<MapLibreMap | undefined>(undefined)
  const activeGrid = testModeEnabled ? testGrid : realGrid
  const activeGridData = activeGrid?.featureCollection ?? { type: 'FeatureCollection' as const, features: [] }
  const hasStudies = !testModeEnabled && realGrid?.featureCollection.features.length === 101 && realGrid.featureCollection.features.every((f) => !!f.properties.study_priority)
  const classificationView = realView === 'ecological' ? 'ecological' : hasStudies ? 'study' : 'documentary'
  const selectedRealHexagonId = selectedGridCell && selectedGridCell.gridVersion === activeGrid?.gridVersion
    ? selectedGridCell.mailleId
    : null

  const handleSelectRealHexagon = (id: string | null) => {
    setSelectedGridCell(id && activeGrid ? { gridVersion: activeGrid.gridVersion, mailleId: id } : null)
    if (id) {
      setSelectedDepartment(null)
    }
  }

  const handleZoomToTestZone = () => {
    const map = mapRef.current
    if (!map || !testGrid || testGrid.featureCollection.features.length === 0) return
    const bounds: LngLatBoundsLike = testGrid.dataset.bounds
    map.fitBounds(bounds, { padding: 50, duration: 800 })
  }

  const handleZoomToPilot = () => {
    const map = mapRef.current
    if (!map || !realGrid || realGrid.featureCollection.features.length === 0) return
    const bounds: LngLatBoundsLike = realGrid.dataset.bounds
    map.fitBounds(bounds, { padding: 50, duration: 800 })
  }

  const handleToggleTestMode = () => {
    const nextTestMode = !testModeEnabled
    setTestModeEnabled(nextTestMode)
    const map = mapRef.current
    const bounds = nextTestMode ? testGrid?.dataset.bounds : realStudyBounds
    if (map && bounds) {
      map.fitBounds(bounds, { padding: 50, duration: 800 })
    }
    if (selectedRealHexagonId) {
      setSelectedGridCell(null)
    }
    setHoveredRealHexagonId(null)
  }

  const handleRealViewChange = (view: 'documentary' | 'ecological') => {
    setRealView(view)
    setSelectedGridCell(null)
    setHoveredRealHexagonId(null)
  }

  const handleToggleRealGrid = () => {
    setShowRealGrid((prev) => !prev)
    if (selectedRealHexagonId) {
      setSelectedGridCell(null)
    }
  }

  const departmentState = {
    selectedDepartment,
    hoveredDepartment,
    onSelectDepartment: setSelectedDepartment,
    onHoverDepartment: setHoveredDepartment,
  }

  const selectedRealPriority = selectedRealHexagonId
    ? activeGridData.features.find((feature) => feature.properties.maille_id === selectedRealHexagonId)
    : undefined

  const realStudyBounds = useMemo(
    () => (realGrid && !testModeEnabled ? featureCollectionBounds(realGrid.featureCollection) : null),
    [realGrid, testModeEnabled],
  )

  useEffect(() => {
    void (async () => {
      const [testResult, realResult] = await Promise.all([loadTestGrid(), loadRealGrid()])
      setTestGrid(testResult)
      setRealGrid(realResult)
    })()
  }, [realReloadNonce])

  useEffect(() => {
    setSelectedGridCell(null)
    setHoveredRealHexagonId(null)
  }, [realGrid?.dataset.key, realGrid?.gridVersion])

  // Filtre « famille d'investigation » transmis par le catalogue (?famille=R1…R4)
  // et sélection directe d'une maille (?maille=…). Réévalué à chaque navigation.
  useEffect(() => {
    const applyQuery = () => {
      const params = new URLSearchParams(window.location.search)
      const famille = params.get('famille')
      const maille = params.get('maille')
      if (famille && ['R1', 'R2', 'R3', 'R4'].includes(famille)) {
        void loadCells()
          .then((cells) => setFamilyHighlight({ ruleId: famille as RuleId, ids: mailleIdsForRule(cells, famille as RuleId) }))
          .catch(() => setFamilyHighlight(null))
      } else {
        setFamilyHighlight(null)
      }
      if (maille && realGrid) {
        const exists = realGrid.featureCollection.features.some(
          (feature) => feature.properties.maille_id === maille,
        )
        if (exists) {
          setSelectedGridCell({ gridVersion: realGrid.gridVersion, mailleId: maille })
        }
      }
    }
    applyQuery()
    window.addEventListener('popstate', applyQuery)
    return () => window.removeEventListener('popstate', applyQuery)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [realGrid?.gridVersion])

  // Centrer la carte sur les mailles de la famille d'investigation sélectionnée.
  useEffect(() => {
    const map = mapRef.current
    if (!map || !familyHighlight || !realGrid) return
    const features = realGrid.featureCollection.features.filter((feature) =>
      familyHighlight.ids.has(feature.properties.maille_id),
    )
    if (features.length === 0) return
    const bounds = featureCollectionBounds({
      type: 'FeatureCollection',
      features,
    })
    if (bounds) {
      map.fitBounds(bounds, { padding: 60, duration: 800, maxZoom: 13 })
    }
  }, [familyHighlight, realGrid])

  return (
    <div className="application-shell">
      <SiteHeader />

      <main id="main-content" className="workspace">
        <section className="map-workspace" aria-labelledby="map-title">
          <div className="workspace-heading">
            <div>
              <p className="context-label">Normandie</p>
              <h1 id="map-title">Choisir les premières actions à étudier</h1>
            </div>
            <p>
              Des observations locales pour orienter les études et préparer les décisions des collectivités.
            </p>
          </div>

          <div className="map-frame">
            <RegionMap onMapReady={() => setMapRevision((v) => v + 1)} {...departmentState} mapRef={mapRef} hexagonCount={testGrid?.featureCollection.features.length ?? 0} realGridCount={realGrid?.featureCollection.features.length ?? 0} isTestData={true} testModeEnabled={testModeEnabled} showRealGrid={showRealGrid} onZoomToTestZone={handleZoomToTestZone} onZoomToPilot={handleZoomToPilot} onToggleTestMode={handleToggleTestMode} onToggleRealGrid={handleToggleRealGrid} studyAreaBounds={realStudyBounds} testModeAvailable={TEST_MODE_UI_ENABLED} />
            <RealGridLayer classificationView={testModeEnabled ? 'ecological' : classificationView} map={mapRef.current} realGridData={activeGridData} selectedRealHexagonId={selectedRealHexagonId} hoveredRealHexagonId={hoveredRealHexagonId} onSelectRealHexagon={handleSelectRealHexagon} onHoverRealHexagon={setHoveredRealHexagonId} showRealGrid={showRealGrid || testModeEnabled} highlightedMailleIds={familyHighlight?.ids ?? null} />
            {testModeEnabled ? <PriorityLegend testModeEnabled /> : classificationView === 'study' ? null : realView === 'documentary' ? <DocumentaryLegend /> : <PriorityLegend realIndeterminateOnly />}
            {!testModeEnabled && realGrid?.loadingError && <div className="map-status map-status--error" role="alert"><strong>Grille REAL indisponible</strong><span>{realGrid.loadingError} — vérifiez la disponibilité de la source de données puis réessayez.</span><button type="button" className="retry-button" onClick={() => setRealReloadNonce((nonce) => nonce + 1)}>Réessayer</button></div>}
          </div>

          {hasStudies && realView !== 'ecological' && <StudyLegend />}
          {!hasStudies && !testModeEnabled && realGrid && !realGrid.loadingError && <p className="detail-note">Les décisions du nouveau lot ne sont pas disponibles dans cet export. Le classement documentaire antérieur reste affiché sans nouvelle action déduite.</p>}
          {familyHighlight && !testModeEnabled && (
            <div className="family-banner" role="status">
              <div>
                <strong>Famille {familyHighlight.ruleId}</strong>
                <span>
                  {familyHighlight.ids.size} secteur{familyHighlight.ids.size > 1 ? 's' : ''} concerné
                  {familyHighlight.ids.size > 1 ? 's' : ''} — surlignés sur la carte. Cliquez une
                  maille pour ouvrir sa fiche diagnostic.
                </span>
              </div>
              <button type="button" className="family-banner-close" onClick={() => navigate('/')}>
                Effacer le filtre
              </button>
            </div>
          )}

          {REAL_VIEW_SWITCHER_ENABLED && !testModeEnabled && (
            <div className="classification-switcher" role="group" aria-label="Vue cartographique réelle">
              <button type="button" className={realView === 'documentary' ? 'is-active' : ''} aria-pressed={realView === 'documentary'} onClick={() => handleRealViewChange('documentary')}>{hasStudies ? 'Priorités d’étude des actions' : 'Classement documentaire antérieur'}</button>
              <button type="button" className={realView === 'ecological' ? 'is-active' : ''} aria-pressed={realView === 'ecological'} onClick={() => handleRealViewChange('ecological')}>Priorité écologique D/S</button>
            </div>
          )}

          <details className="sources-note">
            <summary>Sources et limites</summary>
            <p>
              Les observations réelles mobilisent notamment IGN BD TOPO et ADMIN EXPRESS, le SRCE
              2014, les inventaires DREAL et Cartofriches. La vue indicative prépare l’instruction des actions. Les priorités écologiques restent indéterminées faute de validation. Le mode TEST
              conserve séparément les 43 mailles historiques et leurs couleurs synthétiques.
              Le fond cartographique sert uniquement au repérage.
            </p>
          </details>
          <a className="analysis-jump" href="#analysis-section">
            Voir l'analyse
          </a>
        </section>

        <section id="analysis-section" className="analysis-workspace" aria-label="Diagnostic et analyse">
          {selectedRealHexagonId && !testModeEnabled ? (
            <TerritorialZoneDetail mailleId={selectedRealHexagonId} gridVersion={activeGrid?.gridVersion ?? ''} territoryId={selectedRealPriority?.properties.territory_id ?? CAEN_TERRITORY_ID} />
          ) : selectedRealHexagonId ? (
            <ZoneDetail
              selectedHexagonId={selectedRealHexagonId}
              testModeEnabled={testModeEnabled}
              isRealGrid={!testModeEnabled}
              gridVersion={activeGrid?.gridVersion}
              ecologicalPriority={selectedRealPriority ? priorityFromFeature(selectedRealPriority.properties) : null}
              cellAreaM2={selectedRealPriority?.properties.area_m2}
              isBoundary={selectedRealPriority?.properties.is_boundary}
            />
          ) : selectedDepartment ? (
            <DepartmentPanel {...departmentState} />
          ) : (
            <ZoneDetail />
          )}
        </section>
      </main>
    </div>
  )
}

