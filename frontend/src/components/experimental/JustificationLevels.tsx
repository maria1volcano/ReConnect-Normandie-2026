import { LEVEL_NAMES } from '../../integrations/multiActionsV2Adapter'

const EXPLANATIONS = {
  A: 'Un élément ou une rencontre entre éléments permet de poser une question d’étude localisée.',
  B: 'Une relation cartographique est pertinente ; son rôle écologique reste à confirmer.',
  C: 'Un élément est observé ; son lien avec les continuités écologiques reste à explorer.',
} as const

/** Reading aid only: grades are supplied by M2, never inferred from the map. */
export function JustificationLevels() {
  return <dl className="v2-justification-levels">
    {(Object.keys(LEVEL_NAMES) as Array<keyof typeof LEVEL_NAMES>).map(level => <div key={level}>
      <dt><span aria-hidden="true">{level}</span><span className="v2-sr-only">Niveau {level} : </span>{LEVEL_NAMES[level]}</dt>
      <dd>{EXPLANATIONS[level]}</dd>
    </div>)}
  </dl>
}
