"""Acquisitions officielles bornées, originales conservées, sans inférence écologique."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
import urllib.error
import urllib.parse
import urllib.request
import zipfile

import certifi
import geopandas as gpd
from shapely import union_all

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/caen_et_nord_20261111_v1"
CTX = ssl.create_default_context(cafile=certifi.where())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def get(url, timeout=40):
    request = urllib.request.Request(url, headers={"User-Agent": "ReConnectNormandie-recherche/1.0"})
    try:
        with urllib.request.urlopen(request, context=CTX, timeout=timeout) as response:
            return response.read(), response.geturl()
    except urllib.error.HTTPError as exc:
        if exc.code == 308 and exc.headers.get("Location"):
            return get(urllib.parse.urljoin(url, exc.headers["Location"]), timeout)
        raise


def wfs(kind, typename, bounds):
    folder = RAW / kind
    folder.mkdir(exist_ok=False)
    pages, ids, features = [], set(), []
    offset = 0
    for page in range(60):
        params = {"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature", "TYPENAMES": typename,
                  "OUTPUTFORMAT": "application/json", "SRSNAME": "EPSG:2154",
                  "BBOX": ",".join(str(v) for v in bounds) + ",EPSG:2154", "COUNT": 5000, "STARTINDEX": offset}
        url = "https://data.geopf.fr/wfs/ows?" + urllib.parse.urlencode(params)
        data, final_url = get(url)
        payload = json.loads(data)
        if payload.get("type") != "FeatureCollection":
            raise ValueError("Réponse non géographique")
        if not payload.get("crs", {}).get("properties", {}).get("name", "").endswith("2154"):
            raise ValueError("CRS de réponse non déclaré EPSG:2154")
        current = payload["features"]
        current_ids = [r["id"] for r in current]
        if len(current_ids) != len(set(current_ids)) or ids.intersection(current_ids):
            raise ValueError("Pagination/identifiants répétés")
        ids.update(current_ids)
        path = folder / f"page_{page:03d}.geojson"
        path.write_bytes(data)
        pages.append({"file": str(path.relative_to(ROOT)), "url": final_url, "sha256": digest(data), "features": len(current)})
        features.extend(current)
        offset += len(current)
        matched = payload.get("numberMatched")
        print(kind, "page", page, "objets", offset, "annoncés", matched, flush=True)
        if isinstance(matched, str) and matched.isdigit():
            matched = int(matched)
        if isinstance(matched, int) and offset >= matched or not current:
            break
    else:
        raise ValueError("Pagination incomplète")
    if isinstance(matched, int) and len(features) != matched:
        raise ValueError("Effectif WFS discordant")
    return {"status": "acquired", "source": typename, "license": "lov2", "producer": "IGN",
            "features": len(features), "pages": pages, "ecological_completeness_validated": False,
            "metadata": "data/raw/caen_et_nord_20261111_v1/metadata/bd-topo-r.json"}


def national(kind, slug, preferred):
    metadata = json.loads((RAW / "metadata" / (slug + ".json")).read_text())
    resource = next(r for r in metadata["resources"] if preferred(r))
    folder = RAW / kind
    folder.mkdir(exist_ok=False)
    data, url = get(resource["url"], 90)
    suffix = ".gpkg" if resource.get("format") == "gpkg" else ".zip"
    path = folder / (kind + suffix)
    path.write_bytes(data)
    if suffix == ".zip":
        extracted = folder / "extracted"
        extracted.mkdir()
        with zipfile.ZipFile(path) as z:
            for member in z.infolist():
                if not (extracted / member.filename).resolve().is_relative_to(extracted.resolve()):
                    raise ValueError("Chemin d'archive hors dossier")
            z.extractall(extracted)
        targets = list(extracted.rglob("*.shp"))
        if len(targets) != 1:
            raise ValueError("Archive SHP ambiguë : " + str(targets))
        vector = targets[0]
    else:
        vector = path
    print(kind, "octets", len(data), "acquis", flush=True)
    return {"status": "acquired", "producer": metadata["organization"]["name"], "license": metadata.get("license"),
            "metadata": str((RAW / "metadata" / (slug + ".json")).relative_to(ROOT)),
            "resource_id": resource["id"], "url": url, "file": str(path.relative_to(ROOT)), "sha256": digest(data),
            "vector_file": str(vector.relative_to(ROOT)), "ecological_completeness_validated": False,
            "metadata_last_modified": metadata.get("last_modified")}


def main():
    report = RAW / "acquisition.json"
    if report.exists():
        raise FileExistsError("Acquisition existante : ne pas écraser")
    boundaries = gpd.read_file(RAW / "communes_6_source.geojson")
    assert len(boundaries) == 6 and set(boundaries.code_insee) == {"14118", "14060", "14076", "14167", "14327", "14488"}
    assert boundaries.crs.to_epsg() == 2154 and boundaries.is_valid.all()
    bounds = union_all(boundaries.geometry.to_numpy()).bounds
    jobs = {
        "routes": lambda: wfs("routes", "BDTOPO_V3:troncon_de_route", bounds),
        "haies": lambda: wfs("haies", "BDTOPO_V3:haie", bounds),
        "plans_eau": lambda: wfs("plans_eau", "BDTOPO_V3:plan_d_eau", bounds),
        "reservoirs": lambda: national("reservoirs", "srce-reservoirs-de-biodiversite-normandie", lambda r: r["id"] == "c6e90e56-421d-45b3-9457-1c9a19962633"),
        "corridors": lambda: national("corridors", "srce-corridors-basse-normandie", lambda r: r["id"] == "e9c69c04-02bd-459b-9821-3ffe70360aae"),
        "friches": lambda: national("friches", "sites-references-dans-cartofriches", lambda r: r.get("format") == "gpkg"),
        "zones_humides": lambda: national("zones_humides", "zones-humides-normandie", lambda r: "shapefile" in r.get("format", "")),
    }
    results = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        pending = {pool.submit(job): kind for kind, job in jobs.items()}
        for future in as_completed(pending):
            kind = pending[future]
            try:
                results[kind] = future.result()
            except Exception as exc:
                results[kind] = {"status": "failed", "error": str(exc), "ecological_completeness_validated": False}
                print(kind, "échec", str(exc), flush=True)
    results["communes"] = {"status": "acquired", "file": str((RAW / "communes_6_source.geojson").relative_to(ROOT)),
        "sha256": digest((RAW / "communes_6_source.geojson").read_bytes()), "source": "ADMINEXPRESS-COG.LATEST:commune",
        "producer": "IGN", "retrieved_utc": datetime.now(timezone.utc).isoformat(), "license": "pending_metadata_check"}
    try:
        data, url = get("https://www.data.gouv.fr/api/1/datasets/admin-express/")
        (RAW / "metadata/admin-express.json").write_bytes(data)
        meta = json.loads(data)
        results["communes"].update({"license": meta.get("license"), "metadata_url": url, "metadata_last_modified": meta.get("last_modified")})
    except Exception as exc:
        results["communes"]["metadata_error"] = str(exc)
    report.write_text(json.dumps({"retrieved_utc": datetime.now(timezone.utc).isoformat(), "bbox_epsg2154": bounds,
                                 "sources": results}, ensure_ascii=False, indent=2) + "\n")
    print("Acquisitions terminées", {k: v["status"] for k, v in results.items()}, flush=True)


if __name__ == "__main__":
    main()
