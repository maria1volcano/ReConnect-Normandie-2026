import { JourneyView } from '../components/journey/JourneyView'
import { publicJourneySource } from '../integrations/publicJourneyAdapter'
export function App() { return <JourneyView source={publicJourneySource}/> }
