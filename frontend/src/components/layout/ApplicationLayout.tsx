import { useState, useRef, useEffect } from 'react'
import type { Map as MapLibreMap, LngLatBoundsLike } from 'maplibre-gl'
import { PriorityLegend } from '../legend/PriorityLegend'
import { DepartmentPanel } from '../map/DepartmentPanel'
import { RegionMap } from '../map/RegionMap'
import { RealGridLayer } from '../map/RealGridLayer'
import type { DepartmentCode } from '../map/normandyDepartments'
import { ZoneDetail } from '../sector/ZoneDetail'
import { loadRealGrid, loadTestGrid, type RealGridData } from '../../integrations/geojsonAdapter'
import { priorityFromFeature } from '../../integrations/priorityAdapter'

export function ApplicationLayout() {
  const [selectedDepartment, setSelectedDepartment] = useState<DepartmentCode | null>(null)
  const [hoveredDepartment, setHoveredDepartment] = useState<DepartmentCode | null>(null)
  const [selectedRealHexagonId, setSelectedRealHexagonId] = useState<string | null>(null)
  const [hoveredRealHexagonId, setHoveredRealHexagonId] = useState<string | null>(null)
  const [realGrid, setRealGrid] = useState<RealGridData | null>(null)
  const [testGrid, setTestGrid] = useState<RealGridData | null>(null)
  const [testModeEnabled, setTestModeEnabled] = useState(false)
  const [showRealGrid, setShowRealGrid] = useState(true)
  const mapRef = useRef<MapLibreMap | undefined>(undefined)
  const activeGrid = testModeEnabled ? testGrid : realGrid
  const activeGridData = activeGrid?.featureCollection ?? { type: 'FeatureCollection' as const, features: [] }

  const handleSelectRealHexagon = (id: string | null) => {
    setSelectedRealHexagonId(id)
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
    setTestModeEnabled((prev) => !prev)
    if (selectedRealHexagonId) {
      setSelectedRealHexagonId(null)
    }
    setHoveredRealHexagonId(null)
  }

  const handleToggleRealGrid = () => {
    setShowRealGrid((prev) => !prev)
    if (selectedRealHexagonId) {
      setSelectedRealHexagonId(null)
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

  useEffect(() => {
    void (async () => {
      const [testResult, realResult] = await Promise.all([loadTestGrid(), loadRealGrid()])
      setTestGrid(testResult)
      setRealGrid(realResult)
    })()
  }, [])

  useEffect(() => {
    setSelectedRealHexagonId(null)
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
            <RegionMap {...departmentState} mapRef={mapRef} hexagonCount={testGrid?.featureCollection.features.length ?? 0} realGridCount={realGrid?.featureCollection.features.length ?? 0} isTestData={true} testModeEnabled={testModeEnabled} showRealGrid={showRealGrid} onZoomToTestZone={handleZoomToTestZone} onZoomToPilot={handleZoomToPilot} onToggleTestMode={handleToggleTestMode} onToggleRealGrid={handleToggleRealGrid} />
            <RealGridLayer map={mapRef.current} realGridData={activeGridData} selectedRealHexagonId={selectedRealHexagonId} hoveredRealHexagonId={hoveredRealHexagonId} onSelectRealHexagon={handleSelectRealHexagon} onHoverRealHexagon={setHoveredRealHexagonId} showRealGrid={showRealGrid || testModeEnabled} />
            <PriorityLegend testModeEnabled={testModeEnabled} />
          </div>

          <details className="sources-note">
            <summary>Sources et limites</summary>
            <p>
              Les mesures réelles mobilisent les familles officielles TVB/SRCE, BD TOPO, OCS GE,
              BD Haie, SIPAF, Cartofriches et zones humides DREAL. Le pilote et la grille M1 restent
              provisoires ; M2 doit encore valider leur interprétation scientifique. Le mode TEST
              applique des couleurs synthétiques à la même grille M1, explicitement non validées.
              Le fond cartographique sert uniquement au repérage.
            </p>
          </details>
          <a className="analysis-jump" href="#analysis-section">
            Voir l'analyse
          </a>
        </section>

        <section id="analysis-section" className="analysis-workspace" aria-label="Diagnostic et analyse">
          {selectedRealHexagonId ? (
            <ZoneDetail
              selectedHexagonId={selectedRealHexagonId}
              testModeEnabled={testModeEnabled}
              isRealGrid={!testModeEnabled}
              gridVersion={activeGrid?.gridVersion}
              ecologicalPriority={selectedRealPriority ? priorityFromFeature(selectedRealPriority.properties) : null}
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

