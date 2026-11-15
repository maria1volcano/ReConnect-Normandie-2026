/** Editorial projection only: never evaluates, selects or ranks an action.
 * The original API payload and its A/B/C grade remain unchanged and available
 * in the technical resource. Counts below describe source relations or objects,
 * never ecological obstacles, independent sites or expected benefits.
 */
import type { V2Action } from './multiActionsV2Adapter'

export interface LocalIndicator { label: string; value: number }
export interface ActionPresentation {
  why: string[]
  intervention: string[]
  indicators: LocalIndicator[]
  interpretation: string[]
  checks: string[]
  highlights: LocalIndicator[]
  keyLimit: string
}

const INDICATOR_NAMES: Record<string, string> = {
  'Croisement cartographique route–corridor': 'Relations cartographiées entre routes et espaces de continuité',
  'Contact XY haie–route': 'Relations cartographiées entre haies et routes',
  'Contact XY haie–route situé dans SRCE': 'Relations haie–route dans les espaces du schéma régional',
  'Haie recoupant SRCE': 'Relations entre haies et espaces du schéma régional',
  'Site Cartofriches recouvrant SRCE': 'Relations entre sites de friches et espaces du schéma régional',
  'Plan d’eau recouvrant SRCE': 'Relations entre plans d’eau et espaces du schéma régional',
  'Plan d’eau recouvrant un inventaire humide': 'Relations entre plans d’eau et inventaires de milieux humides',
  'Inventaire humide recouvrant un réservoir humide': 'Relations entre inventaires et réservoirs de biodiversité humides',
  'Haies': 'Haies prises en compte pour cette piste',
  'Tronçons routiers': 'Tronçons routiers pris en compte pour cette piste',
  'Sites Cartofriches': 'Sites de friches pris en compte pour cette piste',
  'Plans d’eau': 'Plans d’eau pris en compte pour cette piste',
  'Milieux humides inventoriés': 'Éléments d’inventaire humide pris en compte pour cette piste',
  'Matrices et corridors SRCE': 'Espaces du schéma régional pris en compte pour cette piste',
  'Réservoirs SRCE': 'Réservoirs de biodiversité pris en compte pour cette piste',
}

function hasRelation(action: V2Action, value: string): boolean {
  return action.spatial_relations.includes(value)
}
function sourceStrings(action: V2Action, ...keys: string[]): string[] {
  return [...new Set(keys.flatMap(key => action.source_context[key] ?? []).filter((v): v is string => typeof v === 'string' && !!v))]
}
function sourceContextNotes(action: V2Action): string[] {
  const notes: string[] = []
  const nature = sourceStrings(action, 'nature', 'nature_plan_eau')
  if (nature.length) notes.push(`Nature indiquée par la source : ${nature.join(', ')}. Un bassin ou une retenue n’est pas automatiquement une mare.`)
  const typology = sourceStrings(action, 'typo', 'typo_zh')
  if (typology.length) notes.push(`Types indiqués dans l’inventaire humide : ${typology.join(', ')}. Leur présence et leur fonctionnement actuels restent à vérifier.`)
  const categories = sourceStrings(action, 'categorie')
  if (categories.length) notes.push(`Voies concernées dans la source : ${categories.join(', ')}.`)
  const positions = sourceStrings(action, 'position_sol').map(v => v === '0' ? 'au niveau du sol' : Number(v) > 0 ? 'surélevée' : Number(v) < 0 ? 'souterraine' : 'non précisée')
  if (positions.length) notes.push(`Position de la voie indiquée : ${[...new Set(positions)].join(', ')} ; cette indication ne mesure pas le passage réel de la faune.`)
  const hedgePrecision = [...new Set(['precision_haie_m', 'precision_planimetrique'].flatMap(key => action.source_context[key] ?? []).filter((v): v is number => typeof v === 'number' && Number.isFinite(v) && v > 0))]
  if (action.action_id === 'A01' && hedgePrecision.length) notes.push(`Précision annoncée pour les haies : ${hedgePrecision.map(v => v.toLocaleString('fr-FR')).join(', ')} m ; ce n’est pas un seuil de continuité écologique.`)
  if (action.source_context.precision_srce?.includes(null)) notes.push('La précision du tracé régional n’est pas renseignée dans la source.')
  return notes
}

export function localIndicators(action: V2Action): LocalIndicator[] {
  return action.observations.flatMap(observation => {
    // Only the pinned API's explicit counted phrases are reformatted. Unknown
    // or uncounted text stays in the original technical resource, never guessed.
    const match = observation.match(/^(.+) : (\d+) (?:référence\(s\) locale\(s\)|objet\(s\) référencé\(s\) dans cette question)\.$/u)
    const label = match && INDICATOR_NAMES[match[1]]
    return label ? [{ label, value: Number(match![2]) }] : []
  })
}

export function presentAction(action: V2Action): ActionPresentation {
  const indicators = localIndicators(action)
  const multipleObjects = (label: string) => indicators.some(i => i.label === label && i.value > 1)
  let why: string[], intervention: string[], checks: string[], interpretation: string[]
  switch (action.action_id) {
    case 'A01': {
      const contact = hasRelation(action, 'Contact XY haie–route') || hasRelation(action, 'Contact XY haie–route situé dans SRCE')
      const regional = hasRelation(action, 'Haie recoupant SRCE')
      if (action.level === 'A' && contact) why = [
        'Des haies et des routes indiquées au niveau du sol se rencontrent dans les données cartographiques de ce secteur.',
        'Cette interface permet de localiser une étude sur la préservation des haies et les déplacements possibles de la faune.',
      ]
      else if (regional) why = [
        'Des haies recoupent des espaces identifiés par le schéma régional des continuités écologiques.',
        'Cette relation rend pertinente l’étude de leur préservation et du rôle qu’elles pourraient jouer pour les déplacements de la faune ; leur fonctionnement réel reste à confirmer.',
      ]
      else if (contact) why = [
        'Les tracés de haies et de routes se rencontrent sur la carte dans ce secteur.',
        'Le contexte de cette rencontre reste à préciser pour comprendre son rôle éventuel dans une continuité bocagère.',
      ]
      else why = [
        'Des haies sont cartographiées dans ce secteur, mais leur lien avec une continuité écologique n’est pas encore documenté.',
        'Elles constituent un point de départ pour examiner leur préservation et le rôle qu’elles pourraient jouer pour la faune.',
      ]
      intervention = contact ? [
        'Étudier la gestion des haies et de leurs abords au droit des voies, en examinant les possibilités de préserver les déplacements de la faune.',
        'L’étude pourrait examiner l’opportunité d’un renforcement, dont la réalisation dépendrait de la confirmation d’un besoin local.',
      ] : [
        'Examiner les possibilités de préserver et d’entretenir les haies existantes.',
        'L’étude pourrait aussi examiner si un renforcement répondrait aux besoins des espèces et aux usages locaux.',
      ]
      interpretation = [
        'Une rencontre de tracés ou un lien avec le schéma régional ne démontre pas une rupture de haie. Une limite du secteur peut aussi créer une coupure apparente.',
        ...sourceContextNotes(action),
      ]
      checks = [
        'Observer l’état et la continuité des haies sur place, en distinguant les coupures réelles des limites de cartographie.',
        'Identifier les habitats et les déplacements concernés pour préciser l’intérêt d’une préservation ou d’un renforcement.',
        'Vérifier les pratiques de gestion, les usages et la compatibilité avec les milieux ouverts avant tout renforcement.',
      ]
      break
    }
    case 'A02': {
      const remblai = sourceStrings(action, 'typo', 'typo_zh').includes('Remblais')
      const regionalWater = hasRelation(action, 'Plan d’eau recouvrant SRCE')
      const inventoriedWater = hasRelation(action, 'Plan d’eau recouvrant un inventaire humide')
      const waterContext = regionalWater && inventoriedWater ? 'des espaces du réseau écologique régional et un inventaire de milieux humides'
        : regionalWater ? 'des espaces du réseau écologique régional' : 'un inventaire de milieux humides'
      if (action.level === 'A' && (regionalWater || inventoriedWater)) why = [
        `${multipleObjects('Plans d’eau pris en compte pour cette piste') ? 'Des plans d’eau identifiés recoupent' : 'Un plan d’eau identifié recoupe'} ${waterContext}.`,
        'Cette relation permet de poser une question localisée sur le fonctionnement et la préservation du milieu.',
      ]
      else if (action.level === 'B') why = [
        'Des éléments d’inventaire humide recouvrent des réservoirs de biodiversité liés à l’eau, identifiés par le schéma régional des continuités écologiques.',
        'Leur rôle potentiel dans les continuités humides mérite d’être étudié, même si la nature et le fonctionnement des habitats restent à confirmer.',
      ]
      else if (remblai) why = [
        'L’inventaire humide décrit notamment un remblai dans ce secteur.',
        'Cette indication mérite d’être vérifiée pour identifier le milieu réellement présent et son lien éventuel avec les autres milieux humides.',
      ]
      else why = [
        'Un plan d’eau ou un élément d’inventaire humide est cartographié dans ce secteur.',
        'Sa nature et son lien avec les déplacements entre milieux humides restent incertains, ce qui motive une première reconnaissance.',
      ]
      intervention = [
        'Étudier la préservation et la gestion du milieu après avoir identifié sa nature et son alimentation en eau.',
        'Une restauration ne serait examinée qu’en fonction du diagnostic hydrologique et d’un besoin confirmé dans le réseau de milieux humides.',
      ]
      interpretation = [
        'Les contours d’un inventaire ne suffisent pas à établir un fonctionnement hydrologique. L’absence de mare recensée ne prouve ni son absence réelle ni un besoin de création.',
        ...sourceContextNotes(action),
      ]
      const surveyMethods = sourceStrings(action, 'diag', 'diag_zh')
      if (surveyMethods.length) interpretation.push(`Méthodes indiquées pour l’inventaire : ${surveyMethods.join(', ')}. Une identification sur photographie et un relevé de terrain n’apportent pas la même information.`)
      checks = [
        'Identifier le milieu sur place : mare, bassin, retenue, remblai ou autre habitat, sans déduire sa nature du seul inventaire.',
        'Examiner l’alimentation en eau, son évolution saisonnière et les contraintes hydrologiques.',
        'Décrire les milieux humides voisins et confirmer l’intérêt d’une préservation ou d’une restauration avant de choisir un aménagement.',
      ]
      break
    }
    case 'A03': {
      why = action.level === 'C' ? [
        !multipleObjects('Sites de friches pris en compte pour cette piste') ? 'Un site est répertorié comme friche dans ce secteur.' : 'Des sites sont répertoriés comme friches dans ce secteur.',
        'Le lien avec un réseau de continuités écologiques n’est pas établi dans les données disponibles ; l’état des lieux et le potentiel d’accueil de la biodiversité méritent une première qualification.',
      ] : [
        !multipleObjects('Sites de friches pris en compte pour cette piste') ? 'Le site pris en compte est répertorié comme friche non reconvertie dans la source et recouvre des espaces du réseau écologique régional.' : 'Les sites pris en compte sont répertoriés comme friches non reconverties dans la source et recouvrent des espaces du réseau écologique régional.',
        'Cette relation justifie une étude localisée du devenir écologique, à confronter aux habitats présents, à l’état actuel des lieux et aux projets déjà engagés.',
      ]
      intervention = [
        'Identifier les habitats à préserver et examiner les possibilités de gestion écologique du site.',
        'Une renaturation pourrait être étudiée si elle est compatible avec la biodiversité existante, l’état des sols et le projet du site.',
      ]
      interpretation = [
        'Le statut de friche ne prouve ni une dégradation écologique ni la disponibilité du terrain. Les informations de l’inventaire doivent être actualisées.',
      ]
      const siteTypes = sourceStrings(action, 'site_type')
      if (siteTypes.length) interpretation.push(`Types de sites indiqués par la source : ${siteTypes.join(', ')}.`)
      const siteStatuses = sourceStrings(action, 'statut_source', 'site_statut')
      if (siteStatuses.length) interpretation.push(`Statuts indiqués dans l’inventaire : ${siteStatuses.join(', ')}. Un projet peut déjà concerner le site.`)
      if (['date_actualisation', 'site_actu_date'].some(key => action.source_context[key]?.includes(null))) interpretation.push('La date d’actualisation n’est pas renseignée pour une partie des informations utilisées.')
      if (action.source_context.precision_srce?.includes(null)) interpretation.push('La précision du tracé régional n’est pas renseignée dans la source.')
      checks = [
        'Vérifier le statut actuel du site, ses usages et les projets déjà engagés.',
        'Relever les habitats et la biodiversité existante, puis qualifier leur relation avec les espaces écologiques voisins.',
        'Examiner la maîtrise foncière et l’état des sols, notamment une éventuelle pollution, avant de définir des travaux.',
      ]
      break
    }
    case 'A04': {
      if (action.level === 'A') why = [
        'Des routes indiquées en service et au niveau du sol croisent des espaces cartographiés pour les continuités écologiques.',
        'Ces rencontres permettent de localiser une étude des déplacements de la faune.',
      ]
      else if (action.level === 'B') why = [
        'Des tracés de voies et d’espaces de continuité écologique se rencontrent dans ce secteur.',
        'Le type de voie et son niveau doivent être précisés pour comprendre leur effet éventuel sur les déplacements de la faune.',
      ]
      else why = [
        'Des voies en service et des espaces d’intérêt écologique sont présents dans le même secteur.',
        'Leur présence commune motive une première reconnaissance des déplacements possibles, sans relation directe établie.',
      ]
      intervention = [
        'Examiner les passages existants et les possibilités d’adapter leur gestion ou leur fonctionnement pour la faune.',
        'Un nouvel aménagement ne serait étudié qu’après confirmation des déplacements concernés et de son opportunité.',
      ]
      interpretation = [
        'Un croisement de tracés se lit dans le plan de la carte ; il ne décrit pas à lui seul les ouvrages ou les possibilités réelles de passage. Un ouvrage existant peut déjà assurer un passage, ce qui change l’intérêt d’un nouvel aménagement.',
        ...sourceContextNotes(action),
      ]
      checks = [
        'Vérifier sur place le niveau de la voie et les ouvrages ou passages déjà présents.',
        'Identifier les habitats, les espèces et les déplacements susceptibles d’être concernés.',
        'Examiner avec le gestionnaire les possibilités d’adaptation et leur faisabilité écologique et technique.',
      ]
      break
    }
  }
  if (!action.presence_only && action.spatial_relations.some(relation => /recou(?:pant|vrant)/u.test(relation))) {
    interpretation.push('Un recouvrement très faible peut être lié à la précision des contours. Sa réalité doit être contrôlée avant d’en déduire un lien écologique.')
  }
  const objectLabel = {A01:'Haies prises en compte pour cette piste', A02:'Éléments d’inventaire humide pris en compte pour cette piste',
    A03:'Sites de friches pris en compte pour cette piste', A04:'Tronçons routiers pris en compte pour cette piste'}[action.action_id]
  const relation = indicators.find(i => i.label.startsWith('Relations'))
  const objects = indicators.find(i => i.label === objectLabel)
  const highlights = [...new Set([relation, objects].filter((i): i is LocalIndicator => !!i))].slice(0, 2)
  if (!highlights.length) highlights.push(...indicators.slice(0, 2))
  const keyLimit = action.action_id === 'A01' ? (action.level === 'C' ? 'Le rôle de ces haies dans les déplacements de la faune reste à établir.' : action.spatial_relations.some(r=>r.includes('Contact')) ? 'Le contact cartographique ne démontre pas une coupure réelle de haie.' : 'Le recouvrement avec le réseau régional peut dépendre de la précision des tracés.')
    : action.action_id === 'A02' ? (sourceStrings(action, 'typo', 'typo_zh').includes('Remblais') ? 'Un remblai est signalé dans l’inventaire ; la nature humide du milieu doit être vérifiée.'
      : sourceStrings(action, 'nature', 'nature_plan_eau').some(v => /bassin|retenue/i.test(v)) ? 'Un bassin ou une retenue est signalé ; cet objet ne doit pas être assimilé à une mare.'
      : 'L’inventaire ne suffit pas à établir le fonctionnement hydrologique actuel du milieu.')
    : action.action_id === 'A03' ? 'Le statut de friche et les projets recensés doivent être actualisés avant de définir une intervention.'
    : action.level === 'C' ? 'La présence commune de voies et d’espaces écologiques ne démontre pas un croisement ni un obstacle.'
    : 'Le croisement sur la carte ne décrit ni les ouvrages existants ni les possibilités réelles de passage.'
  return { why, intervention, indicators, interpretation, checks, highlights, keyLimit }
}

export function readableNonSelection(reason: string): string {
  return reason.replace(/SRCE/g, 'schéma régional des continuités écologiques')
    .replace(/Aucun croisement canonique ni couple route en service\/schéma régional des continuités écologiques localisé ; des routes seules ou le schéma régional des continuités écologiques seul ne justifient pas cette piste/,
      'Les voies observées ne présentent pas de relation cartographique suffisante avec des espaces de continuité pour formuler cette piste')
    .replace(/Aucune haie\/interface documentée et localisable dans les sources utilisées ; absence écologique non démontrée/,
      'Les données ne localisent pas de haie ou d’interface permettant cette proposition ; cela ne prouve pas une absence de haies')
    .replace(/Aucun plan d’eau\/objet ZH ni relation humide documenté permettant cette piste ; absence écologique non démontrée/,
      'Les données ne localisent pas de milieu ou de relation humide permettant cette proposition ; cela ne prouve pas une absence de ces milieux')
    .replace(/Aucun site de friche localisé admissible ; absence écologique non démontrée/,
      'Aucun site de friche ne permet de formuler cette proposition dans les données disponibles')
}
