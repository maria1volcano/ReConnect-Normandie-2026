"""Contrôle de fidélité : compare le rejeu `etendre_mailles reference` au lot public publié.

    python -m analysis.comparer_reference data/derived/reference_rejouee

Sort en erreur si une couleur, une règle, le statut d'une piste R1–R4 ou un compteur
d'événements diffère. Les autres écarts (mesures) sont listés pour revue.
Les mesures flottantes sont comparées à 1e-6 près (relatif).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED = ROOT / "frontend/public/data/caen-6com"


def close(a, b):
    if isinstance(a, float) or isinstance(b, float):
        if a is None or b is None:
            return a is b
        return math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-6)
    return a == b


def diff(path, a, b, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            diff(f"{path}.{k}", a.get(k, "<absent>"), b.get(k, "<absent>"), out)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            diff(f"{path}[{i}]", x, y, out)
    elif not close(a, b):
        out.append((path, a, b))


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("replay", type=Path)
    args = parser.parse_args(argv)
    published = json.loads((PUBLISHED / "cells.json").read_text())
    replay = json.loads((args.replay / "cells.json").read_text())
    assert set(published) == set(replay), "Identifiants de mailles différents"
    differences = []
    for mid in sorted(published):
        diff(mid, published[mid], replay[mid], differences)
    # Critique = ce qui change la carte ou les pistes : couleur/règle, statut des pistes, événements M2.
    critical = [d for d in differences if ".documentary." in d[0] or d[0].endswith(".lead_status") or "event_count" in d[0]]
    by_field = {}
    for path, *_ in differences:
        field = path.split(".", 1)[1]
        field = "".join(ch for ch in field if not ch.isdigit())
        by_field[field] = by_field.get(field, 0) + 1
    report = {"mailles": len(published), "ecarts_total": len(differences), "ecarts_critiques": len(critical),
              "ecarts_par_champ": by_field, "exemples": [list(map(str, d)) for d in differences[:10]]}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    (args.replay / "comparaison_reference.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return 1 if critical else 0


if __name__ == "__main__":
    raise SystemExit(main())
