"""Acquisition officielle OCS GE Calvados, avec contrôles d'intégrité explicites."""
from __future__ import annotations
import hashlib
import argparse
import json
from pathlib import Path
import ssl
import urllib.request
import certifi

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/ocsge_caen_20261112_v1"
CTX = ssl.create_default_context(cafile=certifi.where())


def main(artificialisation=False):
    delivery_name = "livraison_artif_2023.json" if artificialisation else "livraison_2023.json"
    delivery = json.loads((RAW / delivery_name).read_text())
    entry = next(x for x in delivery["entry"] if x["id"].endswith(".7z"))
    target = RAW / entry["id"].rsplit("/", 1)[-1]
    assert not target.exists(), "Acquisition déjà présente : ne pas écraser"
    request = urllib.request.Request(entry["id"], headers={"User-Agent": "Mozilla/5.0 ReConnectNormandie/1.0"})
    size, md5, sha = 0, hashlib.md5(), hashlib.sha256()
    part = target.with_suffix(".7z.part")
    with urllib.request.urlopen(request, context=CTX, timeout=60) as response, part.open("xb") as out:
        while data := response.read(1024 * 1024):
            out.write(data); size += len(data); md5.update(data); sha.update(data)
            if size % (20 * 1024 * 1024) == 0: print(size, "octets reçus", flush=True)
    assert size == entry["link"][0]["length"], (size, "taille incomplète")
    assert md5.hexdigest() == entry["content"], "MD5 distinct du catalogue IGN"
    part.rename(target)
    result = {"status": "acquired", "producer": "IGN", "license": "lov2", "date_acquisition": "2026-11-12",
        "millésime": "2023", "url": entry["id"], "file": str(target.relative_to(ROOT)), "bytes": size,
        "md5": md5.hexdigest(), "sha256": sha.hexdigest(), "official_md5_match": True,
        "catalogue": "catalogue_artif_calvados.json" if artificialisation else "catalogue_calvados.json", "livraison": delivery_name,
        "ecological_completeness_validated": False}
    (RAW / ("acquisition_artif.json" if artificialisation else "acquisition.json")).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser();parser.add_argument("--artificialisation", action="store_true")
    main(parser.parse_args().artificialisation)
