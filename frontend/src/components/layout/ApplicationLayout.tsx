import { useState, useRef, useEffect } from 'react'
import type { Map as MapLibreMap, LngLatBoundsLike } from 'maplibre-gl'
import { PriorityLegend } from '../legend/PriorityLegend'
import { DepartmentPanel } from '../map/DepartmentPanel'
import { RegionMap } from '../map/RegionMap'
import { HexGridLayer } from '../map/HexGridLayer'
import { RealGridLayer } from '../map/RealGridLayer'
import type { DepartmentCode } from '../map/normandyDepartments'
import { ZoneDetail } from '../sector/ZoneDetail'
import { loadHexagonGrid, loadRealGrid } from '../../integrations/geojsonAdapter'
import type { FeatureCollection } from 'geojson'

export function ApplicationLayout() {
  const [selectedDepartment, setSelectedDepartment] = useState<DepartmentCode | null>(null)
  const [hoveredDepartment, setHoveredDepartment] = useState<DepartmentCode | null>(null)
  const [selectedHexagonId, setSelectedHexagonId] = useState<string | null>(null)
  const [hoveredHexagonId, setHoveredHexagonId] = useState<string | null>(null)
  const [selectedRealHexagonId, setSelectedRealHexagonId] = useState<string | null>(null)
  const [hoveredRealHexagonId, setHoveredRealHexagonId] = useState<string | null>(null)
  const [hexagonData, setHexagonData] = useState<FeatureCollection>({ type: 'FeatureCollection', features: [] })
  const [realGridData, setRealGridData] = useState<FeatureCollection>({ type: 'FeatureCollection', features: [] })
  const [hexagonCount, setHexagonCount] = useState(0)
  const [realGridCount, setRealGridCount] = useState(0)
  const [isTestData, setIsTestData] = useState(false)
  const [testModeEnabled, setTestModeEnabled] = useState(false)
  const [showRealGrid, setShowRealGrid] = useState(true)
  const mapRef = useRef<MapLibreMap | undefined>(undefined)

  const handleSelectHexagon = (id: string | null) => {
    setSelectedHexagonId(id)
    if (id) {
      setSelectedDepartment(null)
      setSelectedRealHexagonId(null)
    }
  }

  const handleSelectRealHexagon = (id: string | null) => {
    setSelectedRealHexagonId(id)
    if (id) {
      setSelectedDepartment(null)
      setSelectedHexagonId(null)
    }
  }

  const handleZoomToTestZone = () => {
    const map = mapRef.current
    if (!map || hexagonData.features.length === 0) return

    const bounds: LngLatBoundsLike = [
      [-0.29, 49.17],
      [-0.11, 49.29],
    ]
    map.fitBounds(bounds, { padding: 50, duration: 800 })
  }

  const handleZoomToPilot = () => {
    const map = mapRef.current
    if (!map || realGridData.features.length === 0) return

    // Pilot bbox from M1: [-0.28, 49.20, -0.22, 49.26]
    const bounds: LngLatBoundsLike = [
      [-0.28, 49.20],
      [-0.22, 49.26],
    ]
    map.fitBounds(bounds, { padding: 50, duration: 800 })
  }

  const handleToggleTestMode = () => {
    setTestModeEnabled((prev) => !prev)
    if (selectedHexagonId) {
      setSelectedHexagonId(null)
    }
    if (selectedRealHexagonId) {
      setSelectedRealHexagonId(null)
    }
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

  const hexagonState = {
    selectedHexagonId,
    hoveredHexagonId,
    onSelectHexagon: handleSelectHexagon,
    onHoverHexagon: setHoveredHexagonId,
  }

  useEffect(() => {
    void (async () => {
      const result = await loadHexagonGrid()
      setHexagonData(result.featureCollection)
      setHexagonCount(result.featureCollection.features.length)
      setIsTestData(result.isTestData)
    })()
  }, [])

  useEffect(() => {
    void (async () => {
      const result = await loadRealGrid()
      setRealGridData(result.featureCollection)
      setRealGridCount(result.featureCollection.features.length)
    })()
  }, [])

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
            <RegionMap {...departmentState} mapRef={mapRef} hexagonCount={hexagonCount} realGridCount={realGridCount} isTestData={isTestData} testModeEnabled={testModeEnabled} showRealGrid={showRealGrid} onZoomToTestZone={handleZoomToTestZone} onZoomToPilot={handleZoomToPilot} onToggleTestMode={handleToggleTestMode} onToggleRealGrid={handleToggleRealGrid} />
            <HexGridLayer map={mapRef.current} hexagonData={hexagonData} testModeEnabled={testModeEnabled} {...hexagonState} />
            <RealGridLayer map={mapRef.current} realGridData={realGridData} selectedRealHexagonId={selectedRealHexagonId} hoveredRealHexagonId={hoveredRealHexagonId} onSelectRealHexagon={handleSelectRealHexagon} onHoverRealHexagon={setHoveredRealHexagonId} showRealGrid={showRealGrid && !testModeEnabled} />
            <PriorityLegend showRealGrid={showRealGrid && !testModeEnabled} />
          </div>

          <details className="sources-note">
            <summary>Sources et limites</summary>
            <p>
              Le fond cartographique sert uniquement au repérage. Les limites du pilote, les
              mailles et leurs sources seront chargées depuis les exports validés par M2/M4.
            </p>
          </details>
        </section>

        {selectedHexagonId ? (
          <aside className="zone-detail" aria-label="Fiche maille">
            <ZoneDetail selectedHexagonId={selectedHexagonId} testModeEnabled={testModeEnabled} />
          </aside>
        ) : selectedRealHexagonId ? (
          <aside className="zone-detail" aria-label="Fiche maille réelle">
            <ZoneDetail selectedHexagonId={selectedRealHexagonId} testModeEnabled={false} isRealGrid={true} />
          </aside>
        ) : selectedDepartment ? (
          <aside className="zone-detail" aria-label="Fiche département">
            <DepartmentPanel {...departmentState} />
          </aside>
        ) : (
          <ZoneDetail />
        )}
      </main>
    </div>
  )
}

