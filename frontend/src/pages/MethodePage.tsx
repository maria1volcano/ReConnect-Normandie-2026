import { JourneyMethodPage } from '../components/journey/JourneyMethodPage'
import { publicJourneySource } from '../integrations/publicJourneyAdapter'
export function MethodePage() { return <JourneyMethodPage source={publicJourneySource}/> }
