import { JourneyView } from '../journey/JourneyView'
import { localJourneySource } from '../../integrations/localJourneyAdapter'
export function MultiActionsV2View() { return <JourneyView source={localJourneySource}/> }
