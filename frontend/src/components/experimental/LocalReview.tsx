import type { AppRoute } from '../../app/router'
import { MultiActionsV2View } from './MultiActionsV2View'
import { MultiActionsMethodPage } from './MultiActionsMethodPage'

export default function LocalReview({route}: {route: AppRoute}) {
  return route === '/' ? <MultiActionsV2View/> : <MultiActionsMethodPage/>
}
