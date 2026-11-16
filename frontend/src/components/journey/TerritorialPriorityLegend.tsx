import { TERRITORIAL_PALETTE } from '../../integrations/journeyModel'
import { PRIORITY_LABELS } from '../../integrations/territorialPresentation'

export function TerritorialPriorityLegend() {
  return <section className="v2-territorial-legend" aria-labelledby="territorial-legend-title">
    <div className="legend-heading"><h2 id="territorial-legend-title">Priorité d’examen indicative</h2></div>
    <ul>{Object.entries(TERRITORIAL_PALETTE).map(([color, hex], index) => <li key={color}>
      <span className="v2-priority-swatch" style={{backgroundColor:hex}} aria-hidden="true">{index === 3 ? '?' : index+1}</span>
      <span>{PRIORITY_LABELS[color as keyof typeof PRIORITY_LABELS]}</span>
    </li>)}</ul>
    <details className="journey-legend-details"><summary>Comprendre ce classement</summary>
      <p>Repérage fondé sur les interfaces entre voies et continuités écologiques.</p>
      <p className="v2-small-note">La couleur ne mesure ni une urgence de travaux ni une priorité écologique globale. Les niveaux de justification des solutions sont indépendants.</p>
      <p>Ce classement ne signale pas une urgence écologique et ne recommande pas de travaux.</p>
    </details>
  </section>
}
