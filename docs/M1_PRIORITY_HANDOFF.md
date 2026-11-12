# M1 — Priority-readiness handoff to M2

Date: 10 November 2026  
Status: **technical enrichment complete; scientific interpretation remains with M2**

## Purpose and non-claims

This package exposes source attributes and evidence-quality flags needed to review the 1,069 road–ecological-matrix crossing events. It does not calculate a priority score, confirm ecological conflict, measure passage effectiveness, or assign red, orange, or yellow classes. The 43 real cells remain indeterminate until M2 validates its scientific rules.

The existing grid, `maille_id`, `grid_version`, elementary measurements, and established M1 output schemas are unchanged.

## New deliverables

| Path | Schema and use |
|---|---|
| `data/processed/routes_enriched.gpkg`, layer `routes_enriched`, EPSG:2154 | Internal spatial road layer, 1,924 features, joined by `route_id` |
| `data/processed/route_attributes_enriched.csv` | Deterministic attribute companion for the same 1,924 `route_id` values; no geometry |
| `data/processed/cell_data_quality.csv` | Exactly 43 rows, joined to the grid by `maille_id` + `grid_version` |
| `data/processed/sipaf_context.json` | Non-sensitive SIPAF source/schema context and pilot count |
| `data/processed/priority_enrichment_report.json` | Counts, hashes, library versions, grid integrity digest, null rule and output paths |

The reproducible generator is `analysis/enrich_priority_readiness.py`; validation is in `analysis/test_priority_readiness.py`.

## Enriched road schema

`routes_enriched.gpkg` and the CSV companion contain:

- Provenance/key: `source_id`, `route_id` (`cleabs` in the raw source).
- Existing M1 attributes: `categorie`, `importance`, `nombre_voies`, `largeur_chaussee`, `date_modification`.
- Recovered source attributes: `position_sol`, `precision_planimetrique_m`, `methode_acquisition_planimetrique`, `statut_objet`, `contexte_urbain`, `vitesse_moyenne_vl_source`, `acces_vehicule_leger`, `acces_pieton`, `sens_circulation`, `classement_administratif`, `numero_route`.
- Interpretation guard: `attribute_scope=source_attributes_not_ecological_barrier_evidence`.
- The GeoPackage additionally contains `geometry`; the CSV joins to the unchanged processed road geometry using `route_id`.

Nulls are preserved. In the pilot, category, importance, ground position, planimetric precision/method, status, urban flag, source speed, and light-vehicle access are populated for all 1,924 processed features. Lane count and carriageway width are NULL for 644 features. Source speed is a BD TOPO attribute, not observed traffic or ecological barrier severity.

## Cell-quality schema

Identity and geometry context:

- `maille_id`, `grid_version`
- `cell_area_m2`, `full_area_m2`, `pilot_fraction`, `is_boundary`
- `ocs_coverage_fraction`

Road availability:

- `road_object_count`
- For each of `categorie`, `importance`, `nombre_voies`, `largeur_chaussee`, `position_sol`, `precision_planimetrique_m`, `methode_acquisition_planimetrique`, `statut_objet`, `contexte_urbain`, `vitesse_moyenne_vl_source`, and `acces_vehicule_leger`:
  - `road_<field>_available_count`
  - `road_<field>_completeness_fraction`

The completeness fraction is NULL, not zero, when no mapped road intersects the cell.

SRCE evidence:

- `srce_reference_year`, `srce_age_status`, `srce_precision_status`
- `reservoir_object_count`, `reservoir_subtrame_available_count`, `reservoir_subtrames`, `reservoir_subtrame_status`
- `corridor_object_count`, `corridor_class_available_count`, `corridor_classes`, `corridor_subtrame_available_count`, `corridor_subtrames`, `corridor_subtrame_status`

All mapped local corridors have a class, but their source `sous_trame` value is `-`; this is represented as unknown/NULL rather than as an ecological category. Cells with no mapped reservoir or corridor use an explicit `not_applicable_no_mapped_*` status, not a claim of real-world absence.

Inventory and provenance:

- `bdhaie_inventory_status`, `sipaf_inventory_status`, `cartofriches_inventory_status`, `wetland_inventory_status`, `pram_inventory_status`, `epfn_inventory_status`
- `inventory_completeness_conclusion`
- `provenance_refs`

## Provenance and corrections

- Roads: official IGN BD TOPO V3 WFS extract in `data/raw/bdtopo_routes/routes_orne_estuaire_bbox.geojson`; raw SHA-256 remains recorded in `sources.json` and the existing processing report.
- SRCE: DREAL Normandie 2014 reservoirs and Basse-Normandie corridors.
- SIPAF: `data/raw/sipaf/Tous_les_PAF.gpkg`, national continuous inventory, EPSG:2154, mixed Point/LineString/Polygon geometry.
- Grid/land cover: existing M1 grid and OCS GE 2023 outputs.

`docs/quality_report.md` now uses the authoritative Lambert-93 bbox from `m1_processing_report.json`: `[460989.257242, 6904815.661232, 465631.045140, 6911663.950544]`. `sources.json` now records SIPAF EPSG:2154 and its verified geometry/schema. Both are metadata corrections only.

## SIPAF interpretation

The local SIPAF file contains 2,457 national records and zero registered records intersecting the pilot. Useful future internal fields include UUID/ID, passage name, structure category/type, specificity, crossed infrastructure, hydraulic status, positioning, dates, dimensions, and source.

SIPAF is non-exhaustive. Zero registered records is not proof that the pilot has no local crossing structure and provides no evidence about effectiveness. No SIPAF record-level or sensitive taxonomic data was added to public assets.

## Remaining evidence limitations

- SRCE is from 2014; `precision_source` is not populated and local corridor sub-trame is unknown.
- A mapped corridor or reservoir does not prove present-day ecological functionality.
- BD TOPO hierarchy and source speed do not provide traffic volume, mortality, fencing, permeability, noise/light, or species use.
- SIPAF, BD Haie, and Cartofriches are non-exhaustive; wetland inventories are heterogeneous.
- PRAM and EPFN remain unavailable in the current measurements.
- Very small clipped boundary cells require an M2 eligibility/reliability rule.

## Decisions required from M2

1. Which SRCE classes/sub-trames constitute adequate ecological evidence, and is a corridor with unknown sub-trame classifiable?
2. Is the SRCE scale and unknown local source precision acceptable for interpreting individual crossings?
3. Which road categories and source attributes are admissible, and which require traffic or field evidence?
4. Which missing attributes force an indeterminate result?
5. How must possible culverts/bridges be handled when SIPAF has no registered pilot record?
6. What minimum `pilot_fraction` or cell area is eligible for classification?
7. What independent reliability gate must pass before any non-gray class is assigned?

## Candidate manual review procedure for 3–5 cells

1. M2 selects 3–5 cells from its 29 cells with detected crossings, including contrasting road categories and at least one low-information or boundary case. Selection is purposeful review, not a ranked M1 score.
2. Join crossing events to `cell_data_quality.csv` on `maille_id` + `grid_version` and to road attributes on `route_id`.
3. Inspect original road, corridor, and reservoir geometries at source-appropriate scale; check clipping/boundary effects and event deduplication.
4. Record corridor class/sub-trame state, road attribute availability, SRCE age/precision, and inventory limitations for every event.
5. Apply M2's documented reliability gate before its decision table. Missing essential evidence yields `indeterminate`.
6. Manually document counter-evidence and uncertainty; do not infer effectiveness from proximity or absence from SIPAF.
7. Retain at least one no-crossing/non-conclusive control among the reviewed examples when testing the rule behavior.

These deliverables support scientific review and explainability; they do not by themselves validate ecological priority classifications.
