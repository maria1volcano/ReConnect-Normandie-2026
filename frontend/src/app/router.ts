import { useEffect, useState } from 'react'

export const ROUTES = ['/', '/methode', '/catalogue'] as const
export type AppRoute = (typeof ROUTES)[number]

function splitTarget(target: string): { path: string; suffix: string } {
  const q = target.indexOf('?')
  if (q === -1) return { path: target, suffix: '' }
  return { path: target.slice(0, q), suffix: target.slice(q) }
}

export function normalizePath(pathname: string): AppRoute {
  const clean = pathname.replace(/\/+$/, '') || '/'
  return (ROUTES as readonly string[]).includes(clean) ? (clean as AppRoute) : '/'
}

export function currentRoute(): AppRoute {
  return normalizePath(window.location.pathname)
}

export function navigate(to: AppRoute | string): void {
  const { path, suffix } = splitTarget(to)
  const target = normalizePath(path) + suffix
  if (`${window.location.pathname}${window.location.search}` !== target) {
    window.history.pushState({}, '', target)
  }
  window.dispatchEvent(new PopStateEvent('popstate'))
}

export function linkClickHandler(to: string) {
  return (event: { preventDefault: () => void }) => {
    event.preventDefault()
    navigate(to)
  }
}

export function useRoute(): AppRoute {
  const [route, setRoute] = useState<AppRoute>(currentRoute)
  useEffect(() => {
    const onPop = () => setRoute(currentRoute())
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])
  return route
}
