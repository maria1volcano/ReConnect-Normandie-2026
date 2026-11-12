"""Reprise WFS complète sur le même BBOX avec attributs utiles explicités."""
import json
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import geopandas as gpd
from shapely import union_all
from analysis.acquerir_caen_et_nord import RAW, ROOT, get, digest


def main():
    folder = RAW / "routes_reprise"
    folder.mkdir(exist_ok=False)
    bounds = union_all(gpd.read_file(RAW / "communes_6_source.geojson").geometry.to_numpy()).bounds
    fields = ["cleabs", "nature", "importance", "position_par_rapport_au_sol", "etat_de_l_objet",
              "date_modification", "nombre_de_voies", "largeur_de_chaussee", "urbain", "vitesse_moyenne_vl",
              "precision_planimetrique", "methode_d_acquisition_planimetrique", "acces_vehicule_leger", "acces_pieton",
              "sens_de_circulation", "cpx_classement_administratif", "cpx_numero", "geometrie"]
    def page(offset):
        url = "https://data.geopf.fr/wfs/ows?" + urllib.parse.urlencode({
            "SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature", "TYPENAMES": "BDTOPO_V3:troncon_de_route",
            "OUTPUTFORMAT": "application/json", "SRSNAME": "EPSG:2154", "PROPERTYNAME": ",".join(fields),
            "BBOX": ",".join(str(v) for v in bounds) + ",EPSG:2154", "COUNT": 2000, "STARTINDEX": offset})
        for attempt in range(3):
            data, final = get(url, 50)
            path = folder / f"page_{offset:06d}_attempt_{attempt}.geojson"
            path.write_bytes(data)
            try:
                payload = json.loads(data)
                assert payload["type"] == "FeatureCollection"
                assert payload.get("crs", {}).get("properties", {}).get("name", "").endswith("2154")
                assert all(f.get("geometry") for f in payload["features"])
                return payload, {"file": str(path.relative_to(ROOT)), "sha256": digest(data), "features": len(payload["features"]), "url": final}
            except (ValueError, AssertionError, KeyError):
                if attempt == 2:
                    raise
    first, meta = page(0)
    matched = int(first["numberMatched"])
    collected, pages = first["features"], [meta]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for payload, meta in pool.map(page, range(2000, matched, 2000)):
            collected.extend(payload["features"]); pages.append(meta)
            print("Routes reprise", len(collected), "/", matched, flush=True)
    ids = [f["id"] for f in collected]
    assert len(ids) == len(set(ids)) == matched
    result = {"status": "acquired", "source": "BDTOPO_V3:troncon_de_route", "producer": "IGN", "license": "lov2",
              "features": len(ids), "pages": pages, "properties_requested": fields,
              "reason_for_retry": "première acquisition interrompue après 10000 objets ; reprise complète indépendante avec les attributs utiles et pages de 2000",
              "ecological_completeness_validated": False}
    (RAW / "routes_reprise.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
