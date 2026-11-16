import { JourneyMethodPage } from '../journey/JourneyMethodPage'
import { localJourneySource } from '../../integrations/localJourneyAdapter'
export function MultiActionsMethodPage() { return <JourneyMethodPage source={localJourneySource}/> }
