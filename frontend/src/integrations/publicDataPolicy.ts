/** The already-public historical snapshot only. Updating this allowlist requires a
 * separate publication review; a local V2 flag never authorizes a public dataset. */
export const PUBLIC_DATA_POLICY = {
  kind: 'historical_public',
  directory: 'data/caen-6com/',
  files: {'grid.geojson': 'b4a2f48aed0a028725964c7ec5b4dd0a45eb8568807be29b4debeba32d8a777b','cells.json': '320601dea9f28c0dd710e7f143d4ed0ddae4c8277e219b6b8bffd33fd6273a38'},
  cells: 101, investigations: 404, leads: 165,
  territory: 'caen_et_nord_6communes',
  grid: 'M1-CAEN-6COM-1KM2-FLAT-L93-O0-V1',
  dataset: 'M1-CAEN-ET-NORD-20261111-V1',
  label: null,
} as const

/** Jeu affiché : grille unique sur Caen et 21 communes voisines, calculée par
 * `analysis/etendre_mailles.py perimetre22` (même chaîne, mêmes règles, limites IGN
 * ADMIN EXPRESS). Un seul jeu = aucun hexagone coupé entre deux fichiers. Le lot
 * historique ci-dessus reste la référence de contrôle et le repli en cas d'erreur.
 * Tout recalcul impose de mettre à jour ces empreintes (docs/EXTENSION_MAILLES.md). */
export const PUBLIC_DISPLAY_DATASET = {
  kind: 'historical_public',
  directory: 'data/caen-22com/',
  files: {'grid.geojson': 'ebaedc31040de86de5dc99e4a0e845f9589d151eab1705e5b86dd536c440d2a1','cells.json': 'f3d9456e807197d42f54e66a6a8c9a54a300c73286fcb2bbf8283c95d4a0e23c'},
  cells: 185, investigations: 740, leads: 284,
  territory: 'caen_perimetre_22communes',
  grid: 'M1-CAEN-22COM-1KM2-FLAT-L93-O0-V1',
  dataset: 'M1-CAEN-22COM-20261120-V1',
  label: 'perimetre22',
} as const

export type PublicDatasetPolicy = typeof PUBLIC_DATA_POLICY | typeof PUBLIC_DISPLAY_DATASET
