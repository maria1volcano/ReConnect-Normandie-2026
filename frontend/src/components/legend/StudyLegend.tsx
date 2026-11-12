export function StudyLegend() {
  return <aside className="study-legend" aria-labelledby="study-legend-title">
    <h2 id="study-legend-title">Priorités d’étude des actions écologiques</h2>
    <ul>
      {[['#D64545', 'Priorité 1 — action à examiner en premier'], ['#EF9229', 'Priorité 2 — intervention potentielle à évaluer'],
        ['#E8C84A', 'Priorité 3 — préservation à examiner'], ['#9098A4', 'Décision non évaluable']].map(([color, label]) =>
        <li key={label}><span className="legend-swatch" style={{ backgroundColor: color }} aria-hidden="true" />{label}</li>)}
    </ul>
    <p>Classement indicatif fondé sur les données cartographiques. Les aménagements nécessitent une validation écologique et technique avant réalisation.</p>
  </aside>
}
