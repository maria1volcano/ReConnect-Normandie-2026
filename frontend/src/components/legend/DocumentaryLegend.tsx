const levels = [
  { key: 'V1', label: 'V1 — indices croisés à vérifier', color: '#D9534F' },
  { key: 'V2', label: 'V2 — croisement cartographique documenté', color: '#F29A48' },
  { key: 'V3', label: 'V3 — continuité cartographiée à examiner', color: '#E6C65B' },
  { key: 'V4', label: 'V4 — information insuffisante', color: '#89938F' },
] as const

export function DocumentaryLegend() {
  return (
    <aside className="priority-legend" aria-labelledby="documentary-legend-title">
      <div className="legend-heading">
        <h2 id="documentary-legend-title">Ordre de vérification documentaire</h2>
        <span>Exploratoire</span>
      </div>
      <ul>
        {levels.map((level) => (
          <li key={level.key}>
            <span className="legend-swatch" style={{ backgroundColor: level.color }} aria-hidden="true" />
            <span>{level.label}</span>
          </li>
        ))}
      </ul>
      <div className="legend-test-label">
        <strong>ANALYSE EXPLORATOIRE — REVUE INTERNE</strong>
        <span>Ces couleurs indiquent un ordre exploratoire de vérification documentaire, et non une priorité écologique scientifiquement validée. Elles ne sont ni un risque, ni une urgence, ni une recommandation de travaux.</span>
      </div>
    </aside>
  )
}
