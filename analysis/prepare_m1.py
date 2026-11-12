"""Prepare the real M1 P0 layers for M2 without performing scientific analysis."""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pyogrio
import pyproj
import shapely
from pyproj import Transformer
from shapely import make_valid, normalize, to_wkb, transform as shapely_transform
from shapely.geometry import box


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
PILOT_BBOX_WGS84 = (-0.28, 49.20, -0.22, 49.26)
TARGET_CRS = "EPSG:2154"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def find_one(base: Path, pattern: str) -> Path:
    matches = sorted(base.rglob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {pattern!r} below {base}, found {len(matches)}")
    return matches[0]


def text(series: pd.Series) -> pd.Series:
    return series.astype("string").replace({"": pd.NA})


def null_column(index: pd.Index) -> pd.Series:
    return pd.Series(pd.NA, index=index, dtype="string")


def semantic_digest(frame: gpd.GeoDataFrame, id_column: str) -> str:
    digest = hashlib.sha256()
    ordered = frame.sort_values(id_column, kind="stable")
    attribute_columns = sorted(c for c in ordered.columns if c != "geometry")
    for _, row in ordered.iterrows():
        attrs = {c: None if pd.isna(row[c]) else str(row[c]) for c in attribute_columns}
        digest.update(json.dumps(attrs, sort_keys=True, ensure_ascii=False).encode("utf-8"))
        digest.update(to_wkb(normalize(row.geometry), hex=False, include_srid=False))
    return digest.hexdigest().upper()


def geometry_ids(frame: gpd.GeoDataFrame, prefix: str) -> pd.Series:
    """Create stable IDs when a source field is only a class label, not an identifier."""
    values = []
    attribute_columns = sorted(c for c in frame.columns if c != "geometry")
    for _, row in frame.iterrows():
        digest = hashlib.sha256()
        attrs = {c: None if pd.isna(row[c]) else str(row[c]) for c in attribute_columns}
        digest.update(json.dumps(attrs, sort_keys=True, ensure_ascii=False).encode("utf-8"))
        digest.update(to_wkb(normalize(row.geometry), hex=False, include_srid=False))
        values.append(f"{prefix}-{digest.hexdigest()[:20].upper()}")
    return pd.Series(values, index=frame.index, dtype="string")


def repair_clip(frame: gpd.GeoDataFrame, pilot, expected_dimension: str) -> tuple[gpd.GeoDataFrame, dict]:
    if frame.crs is None:
        raise RuntimeError("Input layer has no CRS")
    frame = frame.to_crs(TARGET_CRS).copy()
    invalid_before = int((~frame.geometry.is_valid).sum())
    if invalid_before:
        frame.loc[~frame.geometry.is_valid, "geometry"] = frame.loc[
            ~frame.geometry.is_valid, "geometry"
        ].map(make_valid)

    clipped = gpd.clip(frame, pilot, keep_geom_type=False)
    empty_after_clip = int((clipped.geometry.is_empty | clipped.geometry.isna()).sum())
    clipped = clipped.loc[~(clipped.geometry.is_empty | clipped.geometry.isna())].copy()

    invalid_after_clip = int((~clipped.geometry.is_valid).sum())
    if invalid_after_clip:
        clipped.loc[~clipped.geometry.is_valid, "geometry"] = clipped.loc[
            ~clipped.geometry.is_valid, "geometry"
        ].map(make_valid)

    dimension_types = {
        "polygon": {"Polygon", "MultiPolygon"},
        "line": {"LineString", "MultiLineString"},
    }[expected_dimension]
    unexpected = ~clipped.geometry.geom_type.isin(dimension_types)
    unexpected_count = int(unexpected.sum())
    if unexpected_count:
        # Boundary-only contacts are not analysis-ready source objects. They are counted explicitly.
        clipped = clipped.loc[~unexpected].copy()

    stats = {
        "input_bbox_candidates": int(len(frame)),
        "invalid_before": invalid_before,
        "repaired_before_clip": invalid_before,
        "empty_after_clip": empty_after_clip,
        "invalid_after_clip": invalid_after_clip,
        "repaired_after_clip": invalid_after_clip,
        "non_target_dimension_dropped": unexpected_count,
        "output_features": int(len(clipped)),
    }
    return clipped, stats


def write_layer(frame: gpd.GeoDataFrame, path: Path, layer: str, id_column: str, stats: dict) -> dict:
    if path.exists():
        path.unlink()
    frame.to_file(path, layer=layer, driver="GPKG", engine="pyogrio", index=False)
    reopened = gpd.read_file(path, layer=layer, engine="pyogrio")
    result = {
        **stats,
        "path": path.relative_to(ROOT).as_posix(),
        "layer": layer,
        "crs": reopened.crs.to_string(),
        "geometry_types": sorted(reopened.geometry.geom_type.unique().tolist()),
        "invalid_output": int((~reopened.geometry.is_valid).sum()),
        "null_geometry_output": int(reopened.geometry.isna().sum()),
        "duplicate_ids": int(reopened[id_column].duplicated().sum()),
        "fields": list(reopened.columns),
        "semantic_sha256": semantic_digest(reopened, id_column),
    }
    if result["output_features"] != len(reopened):
        raise RuntimeError(f"Reopened count differs for {layer}")
    return result


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    transformer = Transformer.from_crs("EPSG:4326", TARGET_CRS, always_xy=True)
    pilot = shapely_transform(box(*PILOT_BBOX_WGS84), transformer.transform, interleaved=False)
    pilot_bounds = tuple(round(v, 6) for v in pilot.bounds)

    reservoir_shp = find_one(RAW / "tvb_srce_normandie" / "extracted" / "dataset", "*.shp")
    corridor_shp = find_one(
        RAW / "tvb_srce_normandie" / "corridors_basse_normandie" / "extracted" / "dataset", "*.shp"
    )
    roads_geojson = RAW / "bdtopo_routes" / "routes_orne_estuaire_bbox.geojson"
    occupation_gpkg = find_one(RAW / "ocsge_d014_2023" / "extracted", "OCCUPATION_SOL.gpkg")
    constructed_gpkg = find_one(RAW / "ocsge_d014_2023" / "extracted", "ZONE_CONSTRUITE.gpkg")

    source_files = {
        "reservoir_archive": RAW / "tvb_srce_normandie" / "reservoirs_srce_normandie_source.zip",
        "corridor_archive": RAW / "tvb_srce_normandie" / "corridors_basse_normandie" / "corridors_srce_basse_normandie_source.zip",
        "roads_geojson": roads_geojson,
        "ocsge_archive": RAW / "ocsge_d014_2023" / "OCS-GE_2-0__GPKG_LAMB93_D014_2023-01-01.7z",
    }
    source_hashes = {key: sha256(path) for key, path in source_files.items()}
    bbox = pilot.bounds

    layers: dict[str, dict] = {}

    source = gpd.read_file(reservoir_shp, bbox=bbox, engine="pyogrio")
    clipped, stats = repair_clip(source, pilot, "polygon")
    reservoirs = gpd.GeoDataFrame(
        {
            "source_id": "TVB_RES_NORM",
            "objet_id": text(clipped["ID_RESV"]),
            "objet_source_id": text(clipped["ID_SRCE"]),
            "nom": text(clipped["NOM_RESV"]),
            "sous_trame": text(clipped["MILMAJ_REG"]),
            "millesime": "2014",
            "precision_source": null_column(clipped.index),
        },
        geometry=clipped.geometry,
        crs=TARGET_CRS,
    )
    layers["reservoirs"] = write_layer(
        reservoirs, PROCESSED / "reservoirs.gpkg", "reservoirs", "objet_id", stats
    )

    source = gpd.read_file(corridor_shp, bbox=bbox, engine="pyogrio")
    source["_m1_objet_id"] = geometry_ids(source, "TVB-COR")
    clipped, stats = repair_clip(source, pilot, "polygon")
    corridors = gpd.GeoDataFrame(
        {
            "source_id": "TVB_COR_BN",
            "objet_id": text(clipped["_m1_objet_id"]),
            "objet_source_id": text(clipped["ID_SRCE"]),
            "libelle_source": text(clipped["ID_CORR"]),
            "classe_corridor": text(clipped["CLASS_CORR"]),
            "sous_trame": text(clipped["MILMAJ_REG"]),
            "millesime": "2014",
            "precision_source": null_column(clipped.index),
        },
        geometry=clipped.geometry,
        crs=TARGET_CRS,
    )
    layers["corridors"] = write_layer(
        corridors, PROCESSED / "corridors.gpkg", "corridors", "objet_id", stats
    )

    source = gpd.read_file(roads_geojson, bbox=PILOT_BBOX_WGS84, engine="pyogrio")
    clipped, stats = repair_clip(source, pilot, "line")
    routes = gpd.GeoDataFrame(
        {
            "source_id": "BDTOPO_ROUTES",
            "route_id": text(clipped["cleabs"]),
            "categorie": text(clipped["nature"]),
            "importance": text(clipped["importance"]),
            "ouvrage_connu": null_column(clipped.index),
            "millesime": null_column(clipped.index),
            "date_modification": text(clipped["date_modification"]),
            "nombre_voies": clipped["nombre_de_voies"],
            "largeur_chaussee": clipped["largeur_de_chaussee"],
        },
        geometry=clipped.geometry,
        crs=TARGET_CRS,
    )
    layers["routes"] = write_layer(routes, PROCESSED / "routes.gpkg", "routes", "route_id", stats)

    source = gpd.read_file(occupation_gpkg, layer="OCCUPATION_SOL", bbox=bbox, engine="pyogrio")
    clipped, stats = repair_clip(source, pilot, "polygon")
    sols = gpd.GeoDataFrame(
        {
            "source_id": "OCSGE",
            "sol_id": text(clipped["id"]),
            "couverture": text(clipped["code_cs"]),
            "usage": text(clipped["code_us"]),
            "millesime": text(clipped["millesime"]),
            "source_objet": text(clipped["source"]),
            "id_origine": text(clipped["id_origine"]),
        },
        geometry=clipped.geometry,
        crs=TARGET_CRS,
    )
    layers["sols"] = write_layer(sols, PROCESSED / "sols.gpkg", "sols", "sol_id", stats)

    source = gpd.read_file(constructed_gpkg, layer="ZONE_CONSTRUITE", bbox=bbox, engine="pyogrio")
    clipped, stats = repair_clip(source, pilot, "polygon")
    zones = gpd.GeoDataFrame(
        {
            "source_id": "OCSGE",
            "zone_id": text(clipped["id"]),
            "millesime": text(clipped["millesime"]),
        },
        geometry=clipped.geometry,
        crs=TARGET_CRS,
    )
    layers["zones_construites"] = write_layer(
        zones, PROCESSED / "zones_construites.gpkg", "zones_construites", "zone_id", stats
    )

    report = {
        "pipeline_version": "m1-step3-v1",
        "pilot_bbox_wgs84": PILOT_BBOX_WGS84,
        "pilot_bbox_epsg2154": pilot_bounds,
        "target_crs": TARGET_CRS,
        "missing_value_convention": "SQL/GeoPackage NULL; no missing value converted to zero",
        "repair_rule": "Only invalid source or clipped geometries are passed through shapely.make_valid",
        "libraries": {
            "python": platform.python_version(),
            "geopandas": gpd.__version__,
            "pyogrio": pyogrio.__version__,
            "pyproj": pyproj.__version__,
            "shapely": shapely.__version__,
        },
        "raw_sha256_before_and_after": source_hashes,
        "layers": layers,
    }
    (PROCESSED / "m1_processing_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    after = {key: sha256(path) for key, path in source_files.items()}
    if after != source_hashes:
        raise RuntimeError("A raw input changed during processing")
    print(json.dumps({name: data["output_features"] for name, data in layers.items()}, sort_keys=True))


if __name__ == "__main__":
    main()
