interface ZoneDetailProps {
  selectedHexagonId?: string | null
}

export function ZoneDetail({ selectedHexagonId }: ZoneDetailProps) {
  return (
    <aside className="zone-detail" aria-labelledby="zone-detail-title">
      <div className="detail-handle" aria-hidden="true" />
      {selectedHexagonId ? (
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
          <p className="detail-note">
            <strong>NOTE :</strong> Cette maille fait partie des données de démonstration TEST et
            ne représente pas un résultat scientifique validé.
          </p>
        </div>
      ) : (
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
      )}

      {!selectedHexagonId && (
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
      )}
    </aside>
  )
}

