const priorityItems = [
  { key: 'high', label: "Priorité d'examen élevée" },
  { key: 'moderate', label: "Priorité d'examen modérée" },
  { key: 'low', label: "Priorité d'examen faible" },
  { key: 'unknown', label: 'Priorité indéterminée' },
  { key: 'not-analysed', label: 'Zone non analysée' },
] as const

export function PriorityLegend() {
  return (
    <aside className="priority-legend" aria-labelledby="legend-title">
      <div className="legend-heading">
        <h2 id="legend-title">Priorité d’examen</h2>
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

