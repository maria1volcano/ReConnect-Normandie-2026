import { lazy, Suspense, useEffect } from 'react'
import { App } from './App'
import { isV2Enabled } from '../integrations/multiActionsV2Adapter'
import { useRoute } from './router'
import { MethodePage } from '../pages/MethodePage'
import { CataloguePage } from '../pages/CataloguePage'
import '../styles/doc-pages.css'

export function Root() {
  const route = useRoute()

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [route])

  // Keep legacy entry points inside the local reading journey while the
  // explicit experimental gates remain enforced by the adapter.
  if (isV2Enabled() && LocalReview) return <Suspense fallback={<p role="status">Chargement de la carte…</p>}><LocalReview route={route}/></Suspense>

  if (route === '/methode') return <MethodePage />
  if (route === '/catalogue') return <CataloguePage />
  return <App />
}

// Only the experimental data adapter and its private editorial values are DEV-only.
// Both sources render the same shared presentation components.
const LocalReview = import.meta.env.DEV ? lazy(() => import('../components/experimental/LocalReview')) : null
