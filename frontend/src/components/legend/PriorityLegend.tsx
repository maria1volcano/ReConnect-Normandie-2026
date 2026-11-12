const priorityItems = [
  { key: 'high', label: 'Priorité écologique élevée', color: '#D9534F' },
  { key: 'moderate', label: 'Priorité écologique modérée', color: '#F29A48' },
  { key: 'low', label: 'Priorité écologique faible', color: '#E6C65B' },
  { key: 'unknown', label: 'Priorité indéterminée', color: '#89938F' },
] as const

interface PriorityLegendProps {
  testModeEnabled?: boolean
  realIndeterminateOnly?: boolean
}

export function PriorityLegend({ testModeEnabled = false, realIndeterminateOnly = false }: PriorityLegendProps) {
  const visibleItems = realIndeterminateOnly ? priorityItems.filter((item) => item.key === 'unknown') : priorityItems
  return (
    <aside className="priority-legend" aria-labelledby="legend-title">
      <div className="legend-heading">
        <h2 id="legend-title">Priorités écologiques</h2>
        <span>{testModeEnabled ? 'Démonstration' : 'Non validée'}</span>
      </div>
      <ul>
        {visibleItems.map((item) => (
          <li key={item.key}>
            <span
              className={`legend-swatch legend-swatch--${item.key}`}
              style={{ backgroundColor: item.color }}
              aria-hidden="true"
            />
            <span>{item.label}</span>
          </li>
        ))}
      </ul>
      {testModeEnabled && (
        <div className="legend-test-label">
          <strong>DONNÉES SYNTHÉTIQUES — DÉMONSTRATION</strong>
          <span>
            Les couleurs illustrent des priorités fictives. Elles ne constituent pas des conclusions
            écologiques validées.
          </span>
        </div>
      )}
      {realIndeterminateOnly && <p>Aucune priorité écologique réelle n’est scientifiquement validée à ce stade.</p>}
    </aside>
  )
}
