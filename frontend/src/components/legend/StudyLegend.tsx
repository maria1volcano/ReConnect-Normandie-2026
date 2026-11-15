import { PRIORITY_LABELS } from '../../integrations/territorialPresentation'

export function StudyLegend() {
  return <aside className="study-legend" aria-labelledby="study-legend-title">
    <h2 id="study-legend-title">Priorités d’étude des actions écologiques</h2>
    <ul>
      {[['#D64545', PRIORITY_LABELS.rouge], ['#EF9229', PRIORITY_LABELS.orange],
        ['#E8C84A', PRIORITY_LABELS.jaune], ['#9098A4', PRIORITY_LABELS.gris]].map(([color, label]) =>
        <li key={label}><span className="legend-swatch" style={{ backgroundColor: color }} aria-hidden="true" />{label}</li>)}
    </ul>
    <p>Ordre indicatif d’examen principalement fondé sur les interfaces routières cartographiées, sans urgence ni priorité de travaux. Les niveaux de justification des solutions restent indépendants.</p>
  </aside>
}
