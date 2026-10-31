export function ZoneDetail() {
  return (
    <aside className="zone-detail" aria-labelledby="zone-detail-title">
      <div className="detail-handle" aria-hidden="true" />
      <div className="detail-state">
        <span className="detail-icon" aria-hidden="true">
          <span />
        </span>
        <p className="context-label">Fiche secteur</p>
        <h2 id="zone-detail-title">Sélectionnez un secteur</h2>
        <p>
          Choisissez une maille sur la carte pour consulter sa priorité d’examen, ses diagnostics,
          la qualité des données et les pistes associées.
        </p>
      </div>

      <div className="detail-preview" aria-label="Informations disponibles après sélection">
        <div>
          <span>01</span>
          <p>Priorité et explications</p>
        </div>
        <div>
          <span>02</span>
          <p>Conflits potentiels qualifiés</p>
        </div>
        <div>
          <span>03</span>
          <p>Pistes, sources et limites</p>
        </div>
      </div>
    </aside>
  )
}

