import { useState, useRef, useEffect, useMemo } from 'react'
import type { Map as MapLibreMap, LngLatBoundsLike } from 'maplibre-gl'
import { PriorityLegend } from '../legend/PriorityLegend'
import { DocumentaryLegend } from '../legend/DocumentaryLegend'
import { DepartmentPanel } from '../map/DepartmentPanel'
import { RegionMap } from '../map/RegionMap'
import { RealGridLayer } from '../map/RealGridLayer'
import type { DepartmentCode } from '../map/normandyDepartments'
import { ZoneDetail } from '../sector/ZoneDetail'
import { TerritorialZoneDetail } from '../sector/TerritorialZoneDetail'
import { loadRealGrid, loadTestGrid, type RealGridData } from '../../integrations/geojsonAdapter'
import { priorityFromFeature } from '../../integrations/priorityAdapter'
import { CAEN_TERRITORY_ID } from '../../integrations/gridDatasets'

// Le mode TEST historique (43 mailles pilotes Orne, données synthétiques) reste
// implémenté et ses fichiers/données sont conservés, mais il est retiré de la
// navigation publique : la carte REAL 101 mailles est l'expérience principale.
// Repassez TEST_MODE_UI_ENABLED à true pour réactiver l'interface TEST.
const TEST_MODE_UI_ENABLED = false

// La vue « Priorité écologique — non validée » (101 cellules grises) reste
// implémentée dans RealGridLayer/PriorityLegend, mais le sélecteur de vue est
// retiré de l'interface : la carte affiche uniquement l'ordre de vérification
// documentaire exploratoire. Repassez à true pour réactiver le sélecteur.
const REAL_VIEW_SWITCHER_ENABLED = false

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
  const mapRef = useRef<MapLibreMap | undefined>(undefined)
  const activeGrid = testModeEnabled ? testGrid : realGrid
  const activeGridData = activeGrid?.featureCollection ?? { type: 'FeatureCollection' as const, features: [] }
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

  return (
    <div className="application-shell">
      <header className="app-header">
        <a className="brand" href="#main-content" aria-label="ReConnect Normandie, aller à la carte">
          <img
            src="/images/ecological-emblem.png"
            alt="Emblème écologique ReConnect"
            className="brand-emblem"
            width="52"
            height="52"
          />
          <span className="brand-text">
            <strong>
              ReConnect <span className="brand-normandie">Normandie</span>
              <img
                src="/images/normandy-flag.png"
                alt="Drapeau de la Normandie"
                className="brand-flag-inline"
                width="28"
                height="19"
              />
            </strong>
            <small>Prédiagnostic des continuités écologiques</small>
          </span>
        </a>

        <nav className="header-nav" aria-label="Navigation principale">
          <span aria-disabled="true">Catalogue</span>
          <span aria-disabled="true">Méthode</span>
          <small>À venir</small>
        </nav>
      </header>

      <main id="main-content" className="workspace">
        <section className="map-workspace" aria-labelledby="map-title">
          <div className="workspace-heading">
            <div>
              <p className="context-label">Normandie</p>
              <h1 id="map-title">Explorer les secteurs à examiner</h1>
            </div>
            <p>
              La priorité indique un besoin de vérification préparatoire. Elle ne constitue ni un
              score écologique, ni une décision d’investissement.
            </p>
          </div>

          <div className="map-frame">
            <RegionMap {...departmentState} mapRef={mapRef} hexagonCount={testGrid?.featureCollection.features.length ?? 0} realGridCount={realGrid?.featureCollection.features.length ?? 0} isTestData={true} testModeEnabled={testModeEnabled} showRealGrid={showRealGrid} onZoomToTestZone={handleZoomToTestZone} onZoomToPilot={handleZoomToPilot} onToggleTestMode={handleToggleTestMode} onToggleRealGrid={handleToggleRealGrid} studyAreaBounds={realStudyBounds} testModeAvailable={TEST_MODE_UI_ENABLED} />
            <RealGridLayer classificationView={testModeEnabled ? 'ecological' : realView} map={mapRef.current} realGridData={activeGridData} selectedRealHexagonId={selectedRealHexagonId} hoveredRealHexagonId={hoveredRealHexagonId} onSelectRealHexagon={handleSelectRealHexagon} onHoverRealHexagon={setHoveredRealHexagonId} showRealGrid={showRealGrid || testModeEnabled} />
            {testModeEnabled ? <PriorityLegend testModeEnabled /> : realView === 'documentary' ? <DocumentaryLegend /> : <PriorityLegend realIndeterminateOnly />}
            {!testModeEnabled && realGrid?.loadingError && <div className="map-status map-status--error" role="alert"><strong>Grille REAL indisponible</strong><span>{realGrid.loadingError} — démarrez le backend local M4 (backend/server.py) puis réessayez.</span><button type="button" className="retry-button" onClick={() => setRealReloadNonce((nonce) => nonce + 1)}>Réessayer</button></div>}
          </div>

          {REAL_VIEW_SWITCHER_ENABLED && !testModeEnabled && (
            <div className="classification-switcher" role="group" aria-label="Vue cartographique réelle">
              <button type="button" className={realView === 'documentary' ? 'is-active' : ''} aria-pressed={realView === 'documentary'} onClick={() => handleRealViewChange('documentary')}>Ordre de vérification documentaire — exploratoire</button>
              <button type="button" className={realView === 'ecological' ? 'is-active' : ''} aria-pressed={realView === 'ecological'} onClick={() => handleRealViewChange('ecological')}>Priorité écologique — non validée</button>
            </div>
          )}

          <details className="sources-note">
            <summary>Sources et limites</summary>
            <p>
              Les observations réelles mobilisent notamment IGN BD TOPO et ADMIN EXPRESS, le SRCE
              2014, les inventaires DREAL et Cartofriches. La vue documentaire ordonne uniquement
              la vérification des sources. Les priorités écologiques restent indéterminées faute de validation. Le mode TEST
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

