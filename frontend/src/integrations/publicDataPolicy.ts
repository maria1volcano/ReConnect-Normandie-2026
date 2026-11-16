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
} as const
