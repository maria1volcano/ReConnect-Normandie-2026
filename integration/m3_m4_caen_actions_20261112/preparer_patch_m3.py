"""Reproduire un exemple historique M2 dans un dossier ignoré, sans appliquer le patch."""
from pathlib import Path
import argparse
import difflib
import json
import subprocess

HERE=Path(__file__).resolve().parent
REF='94eef5b8f17dc68af22c323603ec2623b2b58ce1'
ROOT=HERE.parents[1]


def main(output):
    output=Path(output).resolve()
    assert output.is_relative_to((ROOT/'data/derived').resolve()), 'La sortie doit rester dans data/derived/ du dépôt M2'
    assert not output.exists(), 'Le dossier de sortie doit être nouveau'
    target=output/'frontend'
    changes={}
    def edit(name, transform):
        path='frontend/'+name
        original=subprocess.check_output(['git','show',REF+':'+path],cwd=ROOT).decode()
        modified=transform(original)
        assert modified!=original,name
        changes[name]=(original,modified)
    edit('vite.config.ts',lambda s:s.replace("import react from '@vitejs/plugin-react'", "import react from '@vitejs/plugin-react'\n// @ts-expect-error Middleware de revue locale, hors graphe TypeScript navigateur.\nimport { m2CaenActionsPlugin } from './m2-caen-actions-plugin.mjs'").replace('      react(),','      react(),\n      m2CaenActionsPlugin({ root: internalEnv.M2_CAEN_LOT_ROOT }),'))
    edit('src/integrations/priorityAdapter.ts',lambda s:s.replace('export interface RealGridFeatureProperties {','''export interface RealGridFeatureProperties {
  territory_id?: string
  priorite_etude_version?: string
  priorite_etude_couleur?: string
  priorite_etude_niveau?: number | null
  action_principale_id?: string | null'''))
    def adapter(s):
        before='''export function loadRealGrid(
  dataset: GridDatasetDefinition = DEFAULT_REAL_GRID_DATASET,
  priorityRecords: readonly unknown[] = [],
): Promise<RealGridData> {
  return loadGridDataset(dataset, 'REAL', priorityRecords)
}'''
        after='''export async function loadRealGrid(
  dataset: GridDatasetDefinition = DEFAULT_REAL_GRID_DATASET,
  priorityRecords: readonly unknown[] = [],
): Promise<RealGridData> {
  try {
    const response = await fetch('/__internal/m2/caen/mailles.geojson')
    if (response.ok) {
      const data = await response.json() as FeatureCollection<Geometry, RealGridFeatureProperties> & {
        scope: { grid_version: string; territory_id: string }
        classification_defaut: string; version_priorisation_etudes: string
      }
      if (data.classification_defaut !== 'priorites_etude_interventions' || data.version_priorisation_etudes !== 'caen6-priorites-etude-actions-20261112-1' ||
          data.scope.grid_version !== 'M1-CAEN-6COM-1KM2-FLAT-L93-O0-V1' || data.scope.territory_id !== 'caen_et_nord_6communes' || data.features.length !== 101 ||
          !data.features.every((f) => f.properties.territory_id === data.scope.territory_id && f.properties.priorite_etude_version === data.version_priorisation_etudes)) throw new Error('Lot d’étude Caen incompatible')
      const bounds: [[number, number], [number, number]] = [[Infinity, Infinity], [-Infinity, -Infinity]]
      function visit(value: unknown): void {
        if (!Array.isArray(value)) return
        if (typeof value[0] === 'number' && typeof value[1] === 'number') {
          bounds[0][0] = Math.min(bounds[0][0], value[0]); bounds[0][1] = Math.min(bounds[0][1], value[1])
          bounds[1][0] = Math.max(bounds[1][0], value[0]); bounds[1][1] = Math.max(bounds[1][1], value[1]); return
        }
        value.forEach(visit)
      }
      data.features.forEach((f) => { if (f.geometry && 'coordinates' in f.geometry) visit(f.geometry.coordinates) })
      if (!bounds.flat().every(Number.isFinite)) throw new Error('Emprise Caen invalide')
      const definition: GridDatasetDefinition = { key: 'caen6-actions-etude-v1', label: 'Caen et nord — études indicatives', fileName: 'mailles.geojson', gridVersion: data.scope.grid_version, bounds }
      return { featureCollection: prepareGridDataset(data, definition, 'REAL', priorityRecords).featureCollection, gridVersion: definition.gridVersion, dataset: definition }
    }
    if (![404, 503].includes(response.status)) throw new Error('Lot d’étude Caen non accepté')
  } catch (error) {
    console.warn('[M2 Caen] Lot interne non chargé, retour au pilote M1 déclaré.', error)
  }
  return loadGridDataset(dataset, 'REAL', priorityRecords)
}'''
        assert before in s
        return s.replace(before,after)
    edit('src/integrations/geojsonAdapter.ts',adapter)
    def layer(s):
        return (s.replace('  showRealGrid: boolean','  showRealGrid: boolean\n  classificationMode?: \'etudes\' | \'ecologique\'')
            .replace('  showRealGrid,','  showRealGrid,\n  classificationMode = \'ecologique\',')
            .replace("'fill-color': [","'fill-color': classificationMode === 'etudes' ? ['coalesce', ['get', 'priorite_etude_couleur'], '#9098A4'] as ExpressionSpecification : [")
            .replace('[map, realGridData])','[map, realGridData, classificationMode])'))
    edit('src/components/map/RealGridLayer.tsx',layer)
    edit('src/components/map/RegionMap.tsx',lambda s:s.replace('  onToggleRealGrid?: () => void','  onToggleRealGrid?: () => void\n  onMapReady?: () => void').replace('  onToggleRealGrid,','  onToggleRealGrid,\n  onMapReady,').replace("          setMapState('ready')","          setMapState('ready')\n          onMapReady?.()"))
    def layout(s):
        s=s.replace("import { ZoneDetail } from '../sector/ZoneDetail'","import { ZoneDetail } from '../sector/ZoneDetail'\nimport { CaenActionsDetail } from '../sector/CaenActionsDetail'")
        s=s.replace('  const activeGrid =',"  const [mapReady, setMapReady] = useState(false)\n  const [classificationMode, setClassificationMode] = useState<'etudes' | 'ecologique'>('etudes')\n  const isCaenData = realGrid?.dataset.key === 'caen6-actions-etude-v1'\n  const activeGrid =")
        s=s.replace('  return (\n    <div className="application-shell">',"  useEffect(() => { if (mapReady && isCaenData) handleZoomToPilot() }, [mapReady, realGrid?.dataset.key])\n\n  return (\n    <div className=\"application-shell\">")
        s=s.replace('<h1 id="map-title">Explorer les secteurs à examiner</h1>', '<h1 id="map-title">{isCaenData && !testModeEnabled ? "Priorités d’étude des actions écologiques" : "Explorer les secteurs à examiner"}</h1>')
        s=s.replace('''              La priorité indique un besoin de vérification préparatoire. Elle ne constitue ni un
              score écologique, ni une décision d’investissement.''','''              {isCaenData && !testModeEnabled
                ? 'Classement indicatif fondé sur les données cartographiques. Les aménagements nécessitent une validation écologique et technique avant réalisation.'
                : 'La priorité indique un besoin de vérification préparatoire, sans score écologique ni décision d’investissement.'}''')
        s=s.replace('          <div className="map-frame">','''          {isCaenData && !testModeEnabled && <label>Vue <select aria-label="Classification de la carte" value={classificationMode} onChange={(event) => setClassificationMode(event.target.value as 'etudes' | 'ecologique')}>
            <option value="etudes">Priorités d'étude des actions écologiques</option><option value="ecologique">Priorité écologique D/S</option>
          </select></label>}
          <div className="map-frame">''')
        s=s.replace('<RegionMap {...departmentState} mapRef={mapRef}', '<RegionMap {...departmentState} onMapReady={() => setMapReady(true)} mapRef={mapRef}')
        s=s.replace('<RealGridLayer map={mapRef.current}',"<RealGridLayer classificationMode={isCaenData && !testModeEnabled ? classificationMode : 'ecologique'} map={mapRef.current}")
        s=s.replace('            <PriorityLegend testModeEnabled={testModeEnabled} />','''            {isCaenData && !testModeEnabled && classificationMode === 'etudes' ? <div className="priority-legend" aria-label="Légende des priorités d'étude">
              <h3>Priorités d'étude des actions écologiques</h3><p>Indicatif</p>
              <ul>{[['#D64545', 'Rouge : priorité 1 — action à examiner en premier.'], ['#EF9229', 'Orange : priorité 2 — intervention potentielle à évaluer.'], ['#E8C84A', 'Jaune : priorité 3 — préservation ou amélioration à examiner.'], ['#9098A4', 'Gris : décision non évaluable.']].map(([color, label]) => <li key={label}><span className="legend-swatch" style={{backgroundColor: color}} />{label}</li>)}</ul>
              <small>Aucun risque confirmé ni urgence de travaux déduits.</small>
            </div> : <PriorityLegend testModeEnabled={testModeEnabled} />}''')
        s=s.replace('''              Les mesures réelles mobilisent les familles officielles TVB/SRCE, BD TOPO, OCS GE,
              BD Haie, SIPAF, Cartofriches et zones humides DREAL. Le pilote et la grille M1 restent
              provisoires ; M2 doit encore valider leur interprétation scientifique. Le mode TEST
              applique des couleurs synthétiques à la même grille M1, explicitement non validées.
              Le fond cartographique sert uniquement au repérage.''','''              {isCaenData && !testModeEnabled
                ? "Ce lot mobilise IGN BD TOPO et OCS GE, DREAL/SRCE et zones humides, ainsi que Cerema Cartofriches. La complétude écologique n'est pas attestée. Aucun inventaire SIPAF ou PRAM n'est incorporé dans ce lot. L'OCS GE reste un contexte et ne qualifie pas une continuité fonctionnelle. Le fond cartographique sert au repérage."
                : 'Les familles officielles et leur disponibilité sont détaillées dans le catalogue M1. La grille TEST et ses couleurs restent synthétiques et non validées. Le fond cartographique sert uniquement au repérage.'}''')
        before='''            <ZoneDetail
              selectedHexagonId={selectedRealHexagonId}
              testModeEnabled={testModeEnabled}
              isRealGrid={!testModeEnabled}
              gridVersion={activeGrid?.gridVersion}
              ecologicalPriority={selectedRealPriority ? priorityFromFeature(selectedRealPriority.properties) : null}
            />'''
        after='''            isCaenData && !testModeEnabled ? <CaenActionsDetail cellId={selectedRealHexagonId} gridVersion={realGrid!.gridVersion} territoryId="caen_et_nord_6communes" /> : <ZoneDetail
              selectedHexagonId={selectedRealHexagonId}
              testModeEnabled={testModeEnabled}
              isRealGrid={!testModeEnabled}
              gridVersion={activeGrid?.gridVersion}
              ecologicalPriority={selectedRealPriority ? priorityFromFeature(selectedRealPriority.properties) : null}
            />'''
        assert before in s
        return s.replace(before,after)
    edit('src/components/layout/ApplicationLayout.tsx',layout)
    for name,source in [('m2-caen-actions-plugin.mjs',HERE/'m2-caen-actions-plugin.mjs'),('src/components/sector/CaenActionsDetail.tsx',HERE/'CaenActionsDetail.tsx')]:changes[name]=('',source.read_text())
    patch=''
    for name,(old,new)in changes.items():
        p=target/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(new)
        patch+=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/frontend/'+name if old else'/dev/null',tofile='b/frontend/'+name))
    # Git accepts empty context lines without their otherwise trailing space.
    patch=''.join('\n'if line==' \n'else line for line in patch.splitlines(True))
    (output/'m3_priorites_etude_actions.patch').write_text(patch)
    compatibility=json.loads((HERE/'compatibilite_M3.json').read_text())
    assert compatibility['base_commit']==REF and compatibility['files']==list(changes)
    (output/'compatibilite_M3.json').write_text(json.dumps(compatibility,ensure_ascii=False,indent=2)+'\n')
    print('Exemple historique M2 reproduit :',len(changes),'fichiers ; aucun patch appliqué, aucune branche applicative modifiée.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True,help='Nouveau dossier sous data/derived/ du dépôt M2')
    main(parser.parse_args().output)
