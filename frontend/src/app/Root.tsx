import { useEffect } from 'react'
import { App } from './App'
import { useRoute } from './router'
import { MethodePage } from '../pages/MethodePage'
import { CataloguePage } from '../pages/CataloguePage'

export function Root() {
  const route = useRoute()

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [route])

  if (route === '/methode') return <MethodePage />
  if (route === '/catalogue') return <CataloguePage />
  return <App />
}
