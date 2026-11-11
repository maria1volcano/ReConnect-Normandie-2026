import { execFile } from 'node:child_process'
import { existsSync } from 'node:fs'
import { join } from 'node:path'
import { promisify } from 'node:util'

const execFileAsync = promisify(execFile)
const gridVersion = 'M1-CAND-1KM2-FLAT-L93-O0-V1'
const cellIdPattern = /^NORM-G1K-FLAT-R[+-]\d{6}-C[+-]\d{6}$/

function isLoopback(address) {
  return address === '127.0.0.1' || address === '::1' || address === '::ffff:127.0.0.1'
}

function sendJson(response, status, payload) {
  response.statusCode = status
  response.setHeader('Content-Type', 'application/json; charset=utf-8')
  response.setHeader('Cache-Control', 'no-store, private')
  response.setHeader('X-Content-Type-Options', 'nosniff')
  response.end(JSON.stringify(payload))
}

function sqlString(value) {
  return `'${value.replaceAll("'", "''")}'`
}

async function queryCell(root, cellId, configuredSqlitePath) {
  const maillesPath = join(
    root,
    'data',
    'derived',
    'm2_frontiere_20261109_01',
    'data',
    'derived',
    'branche_mailles.gpkg',
  )
  const enjeuxPath = join(
    root,
    'data',
    'derived',
    'm2_reel_20261109_01',
    'data',
    'derived',
    'enjeux_m1_reels.gpkg',
  )
  const gridPath = join(
    root,
    'data',
    'derived',
    'm2_frontiere_20261109_01',
    'data',
    'processed',
    'grille_pilote.gpkg',
  )

  if (![maillesPath, enjeuxPath, gridPath].every(existsSync)) {
    throw new Error('M2 internal GeoPackages are unavailable')
  }

  const sqlite = configuredSqlitePath || process.env.M2_SQLITE_PATH || (process.platform === 'win32' ? 'sqlite3.exe' : 'sqlite3')
  const query = `
    ATTACH DATABASE ${sqlString(enjeuxPath.replaceAll('\\', '/'))} AS enjeux;
    ATTACH DATABASE ${sqlString(gridPath.replaceAll('\\', '/'))} AS grille;
    SELECT
      m.maille_id,
      g.grid_version,
      m.nb_evenements_observes,
      (SELECT COUNT(DISTINCT l.conflit_id) FROM liens_mailles_conflits l WHERE l.maille_id=m.maille_id) AS distinct_events,
      (SELECT COUNT(*) FROM liens_mailles_conflits l WHERE l.maille_id=m.maille_id) AS relationships,
      (SELECT COUNT(*) FROM liens_mailles_conflits l WHERE l.maille_id=m.maille_id AND l.canonical_owner=1) AS canonical_owners,
      m.routes_completeness_status,
      m.corridors_completeness_status,
      e.enj_01_pct,
      e.enj_01_status,
      e.enj_02_presence,
      e.enj_02_status
    FROM mailles_conflits m
    JOIN enjeux.indicateurs_enjeux e USING(maille_id)
    JOIN grille.grille_pilote g USING(maille_id)
    WHERE m.maille_id=${sqlString(cellId)};
  `
  const { stdout } = await execFileAsync(sqlite, ['-readonly', '-json', maillesPath, query], {
    encoding: 'utf8',
    maxBuffer: 1024 * 1024,
    windowsHide: true,
  })
  const rows = JSON.parse(stdout || '[]')
  if (rows.length !== 1) throw new Error('M2 cell is missing or ambiguous')
  return rows[0]
}

export function m2InternalDevPlugin(options = {}) {
  return {
    name: 'm2-internal-dev-only',
    apply: 'serve',
    configureServer(server) {
      server.middlewares.use(async (request, response, next) => {
        const pathname = new URL(request.url || '/', 'http://127.0.0.1').pathname
        const match = pathname.match(/^\/__internal\/m2\/cells\/([^/]+)$/)
        if (!match) return next()

        if (request.method !== 'GET') return sendJson(response, 405, { status: 'method_not_allowed' })
        if (!isLoopback(request.socket.remoteAddress)) {
          return sendJson(response, 403, { status: 'unavailable' })
        }

        const root = options.root || process.env.M2_INTERNAL_ROOT
        if (!root) return sendJson(response, 503, { status: 'unavailable', reason: 'not_configured' })

        const cellId = decodeURIComponent(match[1])
        if (!cellIdPattern.test(cellId)) return sendJson(response, 400, { status: 'invalid_cell_id' })

        try {
          const row = await queryCell(root, cellId, options.sqlitePath)
          if (
            row.grid_version !== gridVersion ||
            row.nb_evenements_observes !== row.distinct_events ||
            row.distinct_events !== row.relationships ||
            row.routes_completeness_status !== 'unknown' ||
            row.corridors_completeness_status !== 'unknown' ||
            row.enj_01_pct !== null ||
            row.enj_01_status !== 'unknown_coverage'
          ) {
            throw new Error('M2 cell summary violates the audited contract')
          }

          return sendJson(response, 200, {
            schemaVersion: 'm2-m4.internal-cell-summary-1',
            dataNature: 'reelle',
            diffusion: 'interne_revue_uniquement',
            cellId: row.maille_id,
            gridVersion: row.grid_version,
            observations: {
              status: 'geometric_detection',
              qualification: 'geometrie_2d',
              distinctEventCount: row.distinct_events,
              relationshipCount: row.relationships,
              canonicalOwnerCount: row.canonical_owners,
            },
            indicators: {
              enj01: { availability: 'unknown', value: null, status: row.enj_01_status },
              enj02: {
                availability: row.enj_02_presence === 1 ? 'observed' : 'unknown',
                value: row.enj_02_presence === 1 ? true : null,
                status: row.enj_02_status,
              },
            },
            coverage: { routes: 'unknown', corridors: 'unknown', completeness: 'unknown' },
            science: {
              priority: 'not_calculated',
              actions: 'not_calculated',
              validation: 'pending',
              limitations: [
                'Observations géométriques non qualifiées écologiquement.',
                'La complétude des couvertures sources n’est pas attestée.',
                'Un zéro observé ne démontre pas une absence écologique.',
              ],
            },
          })
        } catch (error) {
          server.config.logger.warn(`[m2-internal] ${error instanceof Error ? error.message : String(error)}`)
          return sendJson(response, 503, { status: 'unavailable' })
        }
      })
    },
  }
}
