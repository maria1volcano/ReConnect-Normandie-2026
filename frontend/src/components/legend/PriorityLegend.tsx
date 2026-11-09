const priorityItems = [
  { key: 'high', label: "Priorité d'examen élevée" },
  { key: 'moderate', label: "Priorité d'examen modérée" },
  { key: 'low', label: "Priorité d'examen faible" },
  { key: 'unknown', label: 'Priorité indéterminée' },
  { key: 'not-analysed', label: 'Zone non analysée' },
] as const

interface PriorityLegendProps {
  showRealGrid?: boolean
}

export function PriorityLegend({ showRealGrid = false }: PriorityLegendProps) {
  if (showRealGrid) {
    return (
      <aside className="priority-legend" aria-labelledby="legend-title">
        <div className="legend-heading">
          <h2 id="legend-title">Grille géographique</h2>
          <span>Mesures M1</span>
        </div>
        <ul>
          <li>
            <span className="legend-swatch legend-swatch--neutral" aria-hidden="true" />
            <span>Mailles candidates M1</span>
          </li>
        </ul>
        <p className="legend-note">
          L'analyse scientifique (priorités, conflits, actions) est en attente de validation M2.
        </p>
      </aside>
    )
  }

  return (
    <aside className="priority-legend" aria-labelledby="legend-title">
      <div className="legend-heading">
        <h2 id="legend-title">Priorité d'examen</h2>
        <span>Lecture préparatoire</span>
      </div>
      <ul>
        {priorityItems.map((item) => (
          <li key={item.key}>
            <span className={`legend-swatch legend-swatch--${item.key}`} aria-hidden="true" />
            <span>{item.label}</span>
          </li>
        ))}
      </ul>
    </aside>
  )
}
