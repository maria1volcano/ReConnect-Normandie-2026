import { TERRITORIAL_PALETTE } from '../../integrations/multiActionsV2Adapter'
import { PRIORITY_LABELS } from '../../integrations/territorialPresentation'

export function TerritorialPriorityLegend() {
  return <section className="v2-territorial-legend" aria-labelledby="territorial-legend-title">
    <h2 id="territorial-legend-title">Priorité d’examen indicative</h2>
    <p>Repérage fondé sur les interfaces entre voies et continuités écologiques.</p>
    <ul>{Object.entries(TERRITORIAL_PALETTE).map(([color, hex], index) => <li key={color}>
      <span className="v2-priority-swatch" style={{backgroundColor:hex}} aria-hidden="true">{index === 3 ? '?' : index+1}</span>
      <span>{PRIORITY_LABELS[color as keyof typeof PRIORITY_LABELS]}</span>
    </li>)}</ul>
    <p className="v2-small-note">La couleur ne mesure ni une urgence de travaux ni une priorité écologique globale. Les niveaux de justification des solutions sont indépendants.</p>
  </section>
}
