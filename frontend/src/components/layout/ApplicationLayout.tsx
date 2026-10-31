import { PriorityLegend } from '../legend/PriorityLegend'
import { RegionMap } from '../map/RegionMap'
import { ZoneDetail } from '../sector/ZoneDetail'

export function ApplicationLayout() {
  return (
    <div className="application-shell">
      <header className="app-header">
        <a className="brand" href="#main-content" aria-label="ReConnect Normandie, aller à la carte">
          <span className="brand-mark" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
          <span>
            <strong>ReConnect Normandie</strong>
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
            <RegionMap />
            <PriorityLegend />
          </div>

          <details className="sources-note">
            <summary>Sources et limites</summary>
            <p>
              Le fond cartographique sert uniquement au repérage. Les limites du pilote, les
              mailles et leurs sources seront chargées depuis les exports validés par M2/M4.
            </p>
          </details>
        </section>

        <ZoneDetail />
      </main>
    </div>
  )
}

