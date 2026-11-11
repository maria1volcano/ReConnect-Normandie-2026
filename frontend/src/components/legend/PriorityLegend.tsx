const priorityItems = [
  { key: 'high', label: 'Priorité écologique élevée', color: '#D9534F' },
  { key: 'moderate', label: 'Priorité écologique modérée', color: '#F29A48' },
  { key: 'low', label: 'Priorité écologique faible', color: '#E6C65B' },
  { key: 'unknown', label: 'Priorité indéterminée', color: '#89938F' },
] as const

interface PriorityLegendProps {
  testModeEnabled?: boolean
}

export function PriorityLegend({ testModeEnabled = false }: PriorityLegendProps) {
  return (
    <aside className="priority-legend" aria-labelledby="legend-title">
      <div className="legend-heading">
        <h2 id="legend-title">Priorités écologiques</h2>
        <span>{testModeEnabled ? 'Démonstration' : 'Pilote réel'}</span>
      </div>
      <ul>
        {priorityItems.map((item) => (
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
        <p className="legend-test-label">DONNÉES SYNTHÉTIQUES — DÉMONSTRATION</p>
      )}
      
    </aside>
  )
}
