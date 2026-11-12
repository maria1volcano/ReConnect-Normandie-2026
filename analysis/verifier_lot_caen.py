"""Vérification autonome du lot extrait ; bibliothèque standard Python uniquement."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import sys


def load(path):
    def reject(value):
        raise ValueError("Nombre JSON non fini : " + value)
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject)


def verify(root):
    root = Path(root).resolve()
    manifest = load(root / "manifest.json")
    expected = manifest["files_sha256"]
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    assert actual == set(expected) | {"manifest.json", "SHA256SUMS"}, "Inventaire différent du manifeste"
    for name, fingerprint in expected.items():
        path = (root / name).resolve()
        assert path.is_relative_to(root), "Chemin hors lot"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == fingerprint, name
    lines = dict((line.split("  ", 1)[1], line.split("  ", 1)[0])
                 for line in (root / "SHA256SUMS").read_text().splitlines())
    assert set(lines) == set(expected) | {"manifest.json"}
    for name, fingerprint in lines.items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == fingerprint, name
    scope = manifest["scope"]
    cells = load(root / "demo_interne/mailles.geojson")
    conflicts = load(root / "demo_interne/conflits.geojson")
    fiches_doc = load(root / "demo_interne/fiches_zones.json")
    actions_doc = load(root / "demo_interne/actions_resultats.json")
    fiches = fiches_doc["fiches"]
    actions = actions_doc["resultats"]
    def scoped(item):
        return all(item.get(k) == scope[k] for k in ("maille_id", "grid_version", "territory_id") if k != "maille_id")
    mids = [f["properties"]["maille_id"] for f in cells["features"]]
    assert len(mids) == len(set(mids)) == manifest["counts"]["mailles"]
    assert {f["maille_id"] for f in fiches} == set(mids) and len(fiches) == len(mids)
    assert all(scoped(f) for f in fiches)
    assert actions_doc["scope"] == fiches_doc["scope"] == scope
    assert fiches_doc["classification_defaut"] == "triage_documentaire"
    assert len(actions) == 4 * len(mids)
    assert len({(a["maille_id"], a["rule_id"]) for a in actions}) == len(actions)
    assert all(a["maille_id"] in mids and a["statut"] == "non_evaluable" and a["regle_decision"] == "A2" for a in actions)
    event_ids = {f["properties"]["conflit_id"] for f in conflicts["features"]}
    assert len(event_ids) == len(conflicts["features"]) == manifest["counts"]["evenements_agreges"]
    palette = load(root / "provenance/table_triage_exploratoire.json")["legend"]
    indexed = {f["maille_id"]: f for f in fiches}
    for feature in cells["features"]:
        p = feature["properties"]; f = indexed[p["maille_id"]]; t = f["triage_documentaire"]
        assert scoped(p) and p["triage_couleur"] == palette[t["niveau"]] == t["couleur_hex"]
        assert p["triage_regle"] == t["regle"] and bool(t["motif"]) and t["validation_ecologique"] is False
        assert p["priority_category"] == "INDETERMINATE" and p["priority_method_version"] is None
        assert f["priorite_examen"] == {"etat": "non_calculee", "valeur": None}
        assert f["action_ids_valides"] == f["recommandations_validees"] == []
        assert not any(a["travaux_preconises"] for a in f["actions"])
        assert set(p["conflit_ids"]) <= event_ids
        assert p["conflit_ids"] == f["diagnostic_techniciens"]["conflit_ids"]
        assert p["nb_evenements_observes"] == len(p["conflit_ids"])
    for collection in (cells, conflicts):
        assert collection["type"] == "FeatureCollection" and "crs" not in collection
        assert collection["scope"] == scope and collection["publication_autorisee"] is False
        def coordinates(seq):
            if isinstance(seq[0], (float, int)):
                assert len(seq) == 2 and all(math.isfinite(x) for x in seq)
                assert -180 <= seq[0] <= 180 and -90 <= seq[1] <= 90
            else:
                for item in seq: coordinates(item)
        for feature in collection["features"]:
            assert scoped(feature["properties"])
            coordinates(feature["geometry"]["coordinates"])
    with sqlite3.connect((root / "rapports/mailles.gpkg").as_uri() + "?mode=ro", uri=True) as db:
        links = db.execute("SELECT conflit_id,maille_id,canonical_owner FROM liens_mailles_conflits").fetchall()
    assert len(links) == manifest["counts"]["liens"]
    assert len({(c, m) for c, m, _ in links}) == len(links)
    assert {c for c, _, _ in links} == event_ids
    assert all(c in event_ids and m in mids for c, m, _ in links)
    owners = [c for c, _, owner in links if owner]
    assert len(owners) == len(set(owners)) == len(event_ids)
    for mid in mids:
        assert {c for c, m, _ in links if m == mid} == set(indexed[mid]["diagnostic_techniciens"]["conflit_ids"])
    q = load(root / "rapports/quarantaine.validation.json")
    assert len(q["events"]) == manifest["counts"]["evenements_en_quarantaine"]
    assert event_ids.isdisjoint(e["conflit_id"] for e in q["events"])
    assert len(event_ids) + len(q["events"]) == manifest["counts"]["evenements_detectes"]
    assert sum(bool(f["diagnostic_techniciens"]["conflit_ids"]) for f in fiches) == manifest["counts"]["mailles_avec_evenements"]
    historical = root / manifest["historical"]["file"]
    assert hashlib.sha256(historical.read_bytes()).hexdigest() == manifest["historical"]["sha256"]
    return {"ok": True, "files_verified": len(lines), "mailles": len(mids), "fiches": len(fiches),
            "evenements_agreges": len(event_ids), "actions": len(actions), "liens": len(links),
            "historical_zip_preserved": True, "scope": scope}


if __name__ == "__main__":
    print(json.dumps(verify(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent),
                     ensure_ascii=False, indent=2))
