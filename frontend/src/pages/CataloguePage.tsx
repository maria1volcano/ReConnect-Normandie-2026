import { JourneyCataloguePage } from '../components/journey/JourneyCataloguePage'
import { publicJourneySource } from '../integrations/publicJourneyAdapter'
export function CataloguePage() { return <JourneyCataloguePage source={publicJourneySource}/> }
