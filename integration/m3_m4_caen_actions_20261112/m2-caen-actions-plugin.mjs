import { readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'

const VERSION = 'caen6-priorites-etude-actions-20261112-1'
const loopback = (address) => ['127.0.0.1', '::1', '::ffff:127.0.0.1'].includes(address)
const allowed = new Set(['mailles.geojson', 'conflits.geojson', 'fiches_zones.json', 'actions_resultats.json', 'priorites_etude_interventions.json', 'pistes_investigation_trace.json'])

export function m2CaenActionsPlugin({ root } = {}) {
  const cache = new Map()
  const load = (file) => {
    const path = join(root, 'demo_interne', file), modified = statSync(path).mtimeMs
    if (cache.get(file)?.modified !== modified) {
      const data = JSON.parse(readFileSync(path, 'utf8'))
      cache.set(file, { modified, data, byCell: data.fiches ? new Map(data.fiches.map((f) => [f.maille_id, f])) : null })
    }
    return cache.get(file)
  }
  return { name: 'm2-caen-actions-local', apply: 'serve', configureServer(server) {
    server.middlewares.use((req, res, next) => {
      const url = new URL(req.url ?? '/', 'http://localhost'), prefix = '/__internal/m2/caen/'
      if (!url.pathname.startsWith(prefix)) return next()
      const send = (status, body) => {
        res.statusCode = status
        res.setHeader('Content-Type', 'application/json; charset=utf-8')
        res.setHeader('Cache-Control', 'no-store, private')
        res.setHeader('X-Content-Type-Options', 'nosniff')
        res.end(JSON.stringify(body))
      }
      const address = server.httpServer?.address()
      if (!address || typeof address === 'string' || !loopback(address.address) || !loopback(req.socket.remoteAddress) ||
          req.headers.forwarded || req.headers['x-forwarded-for'] || req.headers['sec-fetch-site'] === 'cross-site') return send(403, { error: 'local_review_only' })
      if (req.method !== 'GET') return send(405, { error: 'read_only' })
      if (!root) return send(503, { error: 'lot_not_configured' })
      try {
        const tail = url.pathname.slice(prefix.length)
        const fiches = load('fiches_zones.json')
        if (fiches.data.version_priorisation_etudes !== VERSION || fiches.data.classification_defaut !== 'priorites_etude_interventions') return send(409, { error: 'wrong_operational_version' })
        if (allowed.has(tail)) return send(200, load(tail).data)
        if (tail.startsWith('fiches/')) {
          if (url.searchParams.get('grid_version') !== fiches.data.scope.grid_version || url.searchParams.get('territory_id') !== fiches.data.scope.territory_id) return send(409, { error: 'scope_mismatch' })
          const fiche = fiches.byCell.get(decodeURIComponent(tail.slice('fiches/'.length)))
          return fiche ? send(200, fiche) : send(404, { error: 'cell_not_found' })
        }
        return send(404, { error: 'unknown_internal_resource' })
      } catch {
        return send(503, { error: 'invalid_internal_lot' })
      }
    })
  } }
}
