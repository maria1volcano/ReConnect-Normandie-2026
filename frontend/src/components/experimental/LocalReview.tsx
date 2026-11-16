import type { AppRoute } from '../../app/router'
import { MultiActionsV2View } from './MultiActionsV2View'
import { MultiActionsMethodPage } from './MultiActionsMethodPage'
import { JourneyCataloguePage } from '../journey/JourneyCataloguePage'
import { localJourneySource } from '../../integrations/localJourneyAdapter'

export default function LocalReview({route}: {route: AppRoute}) {
  if (route === '/catalogue') return <JourneyCataloguePage source={localJourneySource}/>
  return route === '/methode' ? <MultiActionsMethodPage/> : <MultiActionsV2View/>
}
