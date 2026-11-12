"""Contrôles M2 avant D/S : aucune classe écologique ni preuve inférée par défaut.

Les attestations documentaires restent des déclarations : ce module ne vérifie
ni l'identité des auteurs ni la véracité de leurs documents. Aucun accès fichier.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import date, datetime
from itertools import combinations
import json
import math
from numbers import Real
from typing import Any, Iterable, Mapping

import geopandas as gpd
from pyproj import CRS
from pyproj.exceptions import CRSError
from shapely import union_all
from shapely.geometry.base import BaseGeometry

from analysis.detect_conflicts import (
    CONTEXT_RULE_APPROVALS_ATTR, ConflictDetection, PotentialConflictRule,
    canonical_json, context_rule_matches, event_evidence_binding, identifier, validate_context_rule,
)
from analysis.indicateurs_enjeux import _coverage_geometry, _fully_covered, territory_geometry_sha256
from analysis.validate_inputs import METRIC_CRS, POLYGONS, LayerSpec, ValidationReport, validate_geodataframe

PRIORITY_METHOD_VERSION = "m2-priorites.proposal-2"
STAKES = ("fort", "moyen", "faible", "inconnu")
PRESSURES = ("obstacle_confirme", "conflit_potentiel", "croisement_detecte",
             "absence_validee", "non_concluant", "non_evalue")
APPLICABILITIES = ("oui", "non_applicable_documentee", "inconnue")
POSITIVE_SIGNALS = frozenset(PRESSURES[:3])


class PriorityInputError(ValueError):
    """Erreur bloquante à code stable ; aucun résultat de priorité partiel."""

    def __init__(self, code: str, field: str, message: str):
        self.code, self.field, self.message = code, field, message
        super().__init__(f"{code} [{field}] : {message}")


def _fail(code, field, message):
    raise PriorityInputError(code, field, message)


def _text(value, field, *, nullable=False, code="E_TYPE_INVALIDE"):
    if value is None and nullable:
        return value
    if not isinstance(value, str) or not value.strip():
        _fail(code, field, "Chaîne non vide attendue.")
    return value


def _id(value, field):
    try:
        return identifier(value)
    except (ValueError, TypeError):
        _fail("E_TYPE_INVALIDE", field, "Identifiant chaîne ou entier, sans booléen ni valeur non finie.")


def _bool(value, field):
    if type(value) is not bool:
        _fail("E_TYPE_INVALIDE", field, "Booléen strict attendu.")
    return value


def _list(value, field):
    if not isinstance(value, list):
        _fail("E_TYPE_INVALIDE", field, "Tableau attendu.")
    return value


def _unique(values, field, code):
    if len({canonical_json(v) for v in values}) != len(values):
        _fail(code, field, "Références ou identifiants dupliqués.")


def _finite_tree(value, field):
    # Ne pas passer d'abord par json_value : il convertirait les NaN en null.
    if isinstance(value, Real) and not math.isfinite(value):
        _fail("E_TYPE_INVALIDE", field, "NaN et Infinity interdits, y compris dans les métadonnées.")
    if isinstance(value, Mapping):
        for key, child in value.items():
            _finite_tree(child, f"{field}.{key}")
    elif isinstance(value, (list, tuple)):
        for child in value:
            _finite_tree(child, field)


def _period(value, field):
    """Périodes fermées de dates ISO ; aucune tolérance temporelle inventée."""
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {"debut", "fin"}:
        _fail("E_PERIODE_INVALIDE", field, "Objet debut/fin ISO requis, ou null.")
    try:
        start, end = (date.fromisoformat(_text(value[k], field)) for k in ("debut", "fin"))
    except ValueError:
        _fail("E_PERIODE_INVALIDE", field, "Dates ISO 8601 attendues.")
    if start > end:
        _fail("E_PERIODE_INVALIDE", field, "Début postérieur à la fin.")
    return start, end


def _review(value, field):
    if not isinstance(value, Mapping):
        _fail("E_TYPE_INVALIDE", field, "Attestation structurée requise.")
    for key in ("reference", "methode_id", "version", "validated_by", "validated_at"):
        _text(value.get(key), f"{field}.{key}")
    try:
        datetime.fromisoformat(value["validated_at"].replace("Z", "+00:00"))
    except ValueError:
        _fail("E_REFERENCE_INVALIDE", field, "Date de validation ISO 8601 attendue.")


@dataclass(frozen=True)
class PreparedPriorityInputs:
    """Copie contrôlée, distincte des objets de l'appelant."""

    cell: dict[str, Any]
    pilot: dict[str, Any]
    diagnostics: tuple[dict[str, Any], ...]


def _validate_assertion_control(diagnostic: Mapping) -> None:
    control = diagnostic["controle_contradictions"]
    if not isinstance(control, dict):
        _fail("E_TYPE_INVALIDE", "controle_contradictions", "Contrôle structuré requis.")
    if not isinstance(control.get("cible"), str) or control["cible"] not in {"pression", "applicabilite", "autre_affirmation"}:
        _fail("E_TYPE_INVALIDE", "controle_contradictions.cible", "Portée explicite du contrôle requise.")
    _text(control.get("portee_reference"), "controle_contradictions.portee_reference")
    if canonical_json(_id(control.get("diagnostic_id"), "controle.diagnostic_id")) != canonical_json(diagnostic["diagnostic_id"]):
        _fail("E_REFERENCE_PREUVE_INVALIDE", "controle.diagnostic_id", "Contrôle visant un autre diagnostic.")
    flag, state = control.get("contradiction_bloquante"), control.get("etat_controle")
    if not ((flag is None and state == "non_evalue") or (flag is False and state == "controle")
            or (flag is True and state == "contradiction_documentee")):
        _fail("E_TYPE_INVALIDE", "controle_contradictions", "État et conclusion du contrôle discordants.")
    if diagnostic["contradiction_bloquante"] is not flag or diagnostic["contradiction_reference"] != control.get("contradiction_reference"):
        _fail("E_REFERENCE_PREUVE_INVALIDE", "controle_contradictions", "Conclusion du diagnostic discordante du contrôle.")
    _text(control.get("contradiction_reference"), "controle.contradiction_reference", nullable=flag is not True,
          code="E_CONTRADICTION_SANS_REFERENCE")
    if flag is True and not _list(control.get("assertions_incompatibles"), "assertions_incompatibles"):
        _fail("E_REFERENCE_PREUVE_INVALIDE", "assertions_incompatibles", "Deux assertions incompatibles doivent être référencées.")
    for reason in _list(control.get("motifs_qualite"), "controle.motifs_qualite"):
        _text(reason, "controle.motifs_qualite")
    independent_ids = _list(control.get("preuve_ids_independantes"), "preuve_ids_independantes")
    for proof in independent_ids:
        _text(proof, "preuve_ids_independantes")
    _unique(independent_ids, "preuve_ids_independantes", "E_REFERENCE_PREUVE_INVALIDE")
    diagnostic_proofs = _list(diagnostic["preuve_ids"], "preuve_ids")
    for proof in diagnostic_proofs:
        _text(proof, "preuve_ids")
    if not set(independent_ids) <= set(diagnostic_proofs):
        _fail("E_REFERENCE_PREUVE_INVALIDE", "preuve_ids_independantes", "Preuve indépendante absente du diagnostic.")
    _text(control.get("independance_reference"), "independance_reference", nullable=not independent_ids)
    if control["cible"] == "applicabilite" and flag is not False and diagnostic["applicabilite"] == "non_applicable_documentee":
        _fail("E_APPLICABILITE_CONTRADICTOIRE", "applicabilite_reference",
              "La justification de non-applicabilité est contestée ; réexamen du domaine requis avant D0.")
    if flag is None and control["cible"] == "pression" and (
        (diagnostic["signal_pression"] in POSITIVE_SIGNALS and diagnostic["validite_positive"])
        or diagnostic["signal_pression"] == "absence_validee"
    ) and not independent_ids:
        _fail("E_CONTROLE_CONTRADICTION_NON_RESOLU", "controle_contradictions",
              "Une conclusion exploitable exige une preuve indépendante du contrôle non évalué.")
    if flag is None and control["cible"] == "applicabilite" and diagnostic["applicabilite"] == "oui":
        _fail("E_CONTROLE_CONTRADICTION_NON_RESOLU", "applicabilite", "L'applicabilité affectée doit rester inconnue.")


def integrate_assertion_control(
    diagnostic: Mapping, control: Mapping, *, cible: str, portee_reference: str,
    preuve_ids_independantes: list[str] | None = None, independance_reference: str | None = None,
) -> dict:
    """Passage explicite du contrôle trivalent vers l'entrée D/S.

    Sans preuve indépendante documentée, une assertion de pression affectée par
    un contrôle inconnu devient non_evalue ; la valeur initiale reste tracée.
    Le booléen inconnu reste null. Aucune règle D/S ou priorité n'est créée ici.
    """
    if not isinstance(diagnostic, Mapping) or not isinstance(control, Mapping):
        _fail("E_TYPE_INVALIDE", "controle_contradictions", "Diagnostic et contrôle structurés requis.")
    required = {"diagnostic_id", "applicabilite", "applicabilite_reference", "signal_pression",
                "validite_positive", "validite_absence", "preuve_ids", "motifs_qualite"}
    if not required <= diagnostic.keys():
        _fail("E_TYPE_INVALIDE", "diagnostic", "Champs de diagnostic explicites requis avant intégration.")
    for key, allowed in (("signal_pression", PRESSURES), ("applicabilite", APPLICABILITIES)):
        if not isinstance(diagnostic[key], str) or diagnostic[key] not in allowed:
            _fail("E_TYPE_INVALIDE", key, "Valeur catégorielle non reconnue.")
    for key in ("validite_positive", "validite_absence"):
        _bool(diagnostic[key], key)
    for key in ("preuve_ids", "motifs_qualite"):
        for value in _list(diagnostic[key], key):
            _text(value, key)
    independent_ids = [] if preuve_ids_independantes is None else _list(preuve_ids_independantes, "preuve_ids_independantes")
    result = deepcopy(dict(diagnostic))
    joined = {**deepcopy(dict(control)), "diagnostic_id": result["diagnostic_id"], "cible": cible,
              "portee_reference": portee_reference, "preuve_ids_independantes": deepcopy(independent_ids),
              "independance_reference": independance_reference,
              "entree_avant_controle": {k: deepcopy(result[k]) for k in (
                  "applicabilite", "applicabilite_reference", "signal_pression", "validite_positive", "validite_absence")}}
    result["contradiction_bloquante"] = joined.get("contradiction_bloquante")
    result["contradiction_reference"] = joined.get("contradiction_reference")
    result["controle_contradictions"] = joined
    # Contrôler d'abord la portée, les références et le schéma sans neutraliser
    # d'entrée arbitraire : seule la quarantaine documentée ci-dessous est admise.
    if joined.get("etat_controle") == "non_evalue" and joined.get("contradiction_bloquante") is None:
        if cible == "pression" and not joined["preuve_ids_independantes"]:
            if result["signal_pression"] in POSITIVE_SIGNALS | {"absence_validee"}:
                result["signal_pression"] = "non_evalue"
                result["validite_positive"] = result["validite_absence"] = False
        elif cible == "applicabilite" and result["applicabilite"] == "oui":
            result["applicabilite"] = "inconnue"
    _validate_assertion_control(result)
    result["motifs_qualite"] = sorted(set(result["motifs_qualite"]) | set(joined["motifs_qualite"]) | (
        {"controle_contradiction_non_evalue"} if joined["contradiction_bloquante"] is None else set()))
    return result


def validate_diagnostic_inputs(cell: Mapping, pilot: Mapping) -> PreparedPriorityInputs:
    """Valide le périmètre fixé avant calcul et les diagnostics déjà qualifiés.

    Ne fabrique pas de métadonnées de production. Les anciennes fixtures sont
    complétées dans les tests uniquement. Une méthode d'enjeu explicitement null
    est conservée pour D2 ; une méthode non autorisée est une erreur.
    """
    if not isinstance(cell, Mapping) or not isinstance(pilot, Mapping):
        _fail("E_PERIMETRE_INVALIDE", "pilot", "Maille et configuration pilote explicites requises.")
    cell, pilot = deepcopy(dict(cell)), deepcopy(dict(pilot))
    required_pilot = {"territory_id", "grid_version", "dataset_version", "priority_method_version",
                      "familles_attendues", "methodes_familles", "references_methodes", "decision",
                      "sources", "preuves", "motifs_versions_inconnues", "limites_applicabilite"}
    if not required_pilot <= pilot.keys():
        _fail("E_PERIMETRE_INVALIDE", "pilot", "Configuration versionnée incomplète.")
    if pilot["priority_method_version"] != PRIORITY_METHOD_VERSION:
        _fail("E_PERIMETRE_INVALIDE", "priority_method_version", "Version D/S non prise en charge.")
    _review(pilot["decision"], "pilot.decision")
    for field in ("motifs_versions_inconnues", "limites_applicabilite"):
        for value in _list(pilot[field], field):
            _text(value, field)
    expected = _list(pilot["familles_attendues"], "familles_attendues")
    if not expected or any(not isinstance(f, str) or not f.strip() for f in expected):
        _fail("E_PERIMETRE_INVALIDE", "familles_attendues", "Liste non vide de familles nommées requise.")
    _unique(expected, "familles_attendues", "E_PERIMETRE_INVALIDE")
    for key in ("territory_id", "grid_version", "dataset_version"):
        _text(pilot[key], key, nullable=True)
        if pilot[key] is None and not pilot["motifs_versions_inconnues"]:
            _fail("E_PERIMETRE_INVALIDE", key, "Version/référence inconnue à justifier explicitement.")
    methods, references = pilot["methodes_familles"], pilot["references_methodes"]
    if not isinstance(methods, dict) or set(methods) != set(expected) or not isinstance(references, dict):
        _fail("E_PERIMETRE_INVALIDE", "methodes_familles", "Méthodes autorisées pour chaque famille attendue requises.")
    for method_id, metadata in references.items():
        _text(method_id, "references_methodes")
        if not isinstance(metadata, dict):
            _fail("E_PERIMETRE_INVALIDE", "references_methodes", "Version et référence de méthode requises.")
        for key in ("reference", "version"):
            _text(metadata.get(key), f"references_methodes.{key}")
    for family, allowed in methods.items():
        if not _list(allowed, f"methodes_familles.{family}"):
            _fail("E_PERIMETRE_INVALIDE", family, "Au moins une méthode autorisée requise.")
        for method in allowed:
            _text(method, family)
            if method not in references:
                _fail("E_PERIMETRE_INVALIDE", family, "Méthode autorisée sans référence/version.")
        _unique(allowed, family, "E_PERIMETRE_INVALIDE")
    sources = {}
    for source in _list(pilot["sources"], "pilot.sources"):
        if not isinstance(source, dict) or not {"namespace", "id", "reference", "periode_reference"} <= source.keys():
            _fail("E_REFERENCE_SOURCE_INVALIDE", "pilot.sources", "Source documentée attendue.")
        _text(source["namespace"], "namespace")
        _id(source["id"], "source.id")
        _text(source["reference"], "source.reference")
        _period(source["periode_reference"], "source.periode_reference")
        identity = canonical_json([source["namespace"], source["id"]])
        if identity in sources:
            _fail("E_REFERENCE_SOURCE_INVALIDE", "sources", "Source déclarée plusieurs fois.")
        sources[identity] = source
    proofs = pilot["preuves"]
    if not isinstance(proofs, dict):
        _fail("E_REFERENCE_PREUVE_INVALIDE", "preuves", "Registre de références de preuves requis.")
    for proof_id, reference in proofs.items():
        _text(proof_id, "preuve_id")
        _text(reference, "preuve.reference")

    required_cell = {"maille_id", "study_area_m2", "familles_attendues", "diagnostics",
                     "priority_method_version", "territory_id", "grid_version", "dataset_version"}
    if not required_cell <= cell.keys():
        _fail("E_TYPE_INVALIDE", "maille", "Champs de maille explicites requis.")
    cell["maille_id"] = _id(cell["maille_id"], "maille_id")
    area = cell["study_area_m2"]
    if isinstance(area, bool) or not isinstance(area, Real) or not math.isfinite(area) or area < 0:
        _fail("E_SURFACE_INVALIDE", "study_area_m2", "Surface finie positive ou nulle requise.")
    _finite_tree(cell, "maille")
    _finite_tree(pilot, "pilot")
    sig_status = cell.get("statut_analyse")
    if sig_status is not None and sig_status not in ("analyse_effectuee", "absence_analyse", "hors_territoire"):
        _fail("E_TYPE_INVALIDE", "statut_analyse", "État de traitement SIG inconnu.")
    if sig_status == "hors_territoire" and area > 0:
        _fail("E_PERIMETRE_INVALIDE", "statut_analyse", "Surface positive incompatible avec hors_territoire.")
    cell_expected = _list(cell["familles_attendues"], "maille.familles_attendues")
    _unique(cell_expected, "familles_attendues", "E_PERIMETRE_INVALIDE")
    if sorted(cell_expected, key=canonical_json) != sorted(expected):
        _fail("E_PERIMETRE_INVALIDE", "familles_attendues", "Le périmètre pilote ne peut pas être réduit selon la maille.")
    for key in ("priority_method_version", "territory_id", "grid_version", "dataset_version"):
        if cell[key] != pilot[key] or type(cell[key]) is not type(pilot[key]):
            _fail("E_PERIMETRE_INVALIDE", key, "Référence discordante du pilote.")
    diagnostics = _list(cell["diagnostics"], "diagnostics")
    identities = set()
    required_diagnostic = {"diagnostic_id", "famille_id", "applicabilite", "applicabilite_reference",
                           "enjeu_classe", "enjeu_methode_id", "signal_pression", "validite_positive",
                           "validite_absence", "contradiction_bloquante", "contradiction_reference",
                           "motifs_qualite", "preuve_ids", "source_objects", "phenomene_id",
                           "periode_reference", "methode_famille_id"}
    for d in diagnostics:
        if not isinstance(d, dict) or not required_diagnostic <= d.keys():
            _fail("E_TYPE_INVALIDE", "diagnostics", "Diagnostic structuré complet requis, y compris les null explicites.")
        d["diagnostic_id"] = _id(d["diagnostic_id"], "diagnostic_id")
        identity = canonical_json(d["diagnostic_id"])
        if identity in identities:
            _fail("E_ID_DUPLIQUE", "diagnostic_id", "Identifiant de diagnostic déjà utilisé.")
        identities.add(identity)
        family = _text(d["famille_id"], "famille_id")
        if family not in expected:
            _fail("E_FAMILLE_HORS_PERIMETRE", "famille_id", "Famille hors du périmètre décisionnel déclaré.")
        for key, allowed in (("applicabilite", APPLICABILITIES), ("enjeu_classe", STAKES), ("signal_pression", PRESSURES)):
            if not isinstance(d[key], str) or d[key] not in allowed:
                _fail("E_TYPE_INVALIDE", key, "Valeur catégorielle non reconnue.")
        for key in ("validite_positive", "validite_absence"):
            _bool(d[key], key)
        if "controle_contradictions" in d:
            _validate_assertion_control(d)
            quality = _list(d["motifs_qualite"], "motifs_qualite")
            for reason in quality:
                _text(reason, "motifs_qualite")
            d["motifs_qualite"] = sorted(set(quality) | set(d["controle_contradictions"]["motifs_qualite"]))
        else:
            _bool(d["contradiction_bloquante"], "contradiction_bloquante")
        for key in ("applicabilite_reference", "contradiction_reference", "enjeu_methode_id"):
            _text(d[key], key, nullable=True)
        if d["phenomene_id"] is not None:
            d["phenomene_id"] = _id(d["phenomene_id"], "phenomene_id")
        method = _text(d["methode_famille_id"], "methode_famille_id")
        if method not in methods[family] or (d["enjeu_methode_id"] is not None and d["enjeu_methode_id"] not in references):
            _fail("E_METHODE_NON_AUTORISEE", "methode_famille_id", "Méthode hors des références approuvées du pilote.")
        period = _period(d["periode_reference"], "periode_reference")
        d_sources = _list(d["source_objects"], "source_objects")
        for source in d_sources:
            if not isinstance(source, dict) or set(source) != {"namespace", "id"}:
                _fail("E_REFERENCE_SOURCE_INVALIDE", "source_objects", "Couple namespace/id requis.")
            _text(source["namespace"], "source.namespace")
            source["id"] = _id(source["id"], "source.id")
            identity_source = canonical_json([source["namespace"], source["id"]])
            if identity_source not in sources:
                _fail("E_REFERENCE_SOURCE_INVALIDE", "source_objects", "Source sans référence dans le registre pilote.")
            source_period = _period(sources[identity_source]["periode_reference"], "source.periode_reference")
            if period and source_period and (period[0] < source_period[0] or period[1] > source_period[1]):
                _fail("E_PERIODE_INCOMPATIBLE", "periode_reference", "Période du diagnostic non couverte par la source.")
        _unique(d_sources, "source_objects", "E_REFERENCE_SOURCE_INVALIDE")
        d["source_objects"] = sorted(d_sources, key=canonical_json)
        for key in ("preuve_ids", "motifs_qualite"):
            for value in _list(d[key], key):
                _text(value, key)
        _unique(d["preuve_ids"], "preuve_ids", "E_REFERENCE_PREUVE_INVALIDE")
        if any(proof not in proofs for proof in d["preuve_ids"]):
            _fail("E_REFERENCE_PREUVE_INVALIDE", "preuve_ids", "Preuve sans référence identifiable dans le registre.")
        d["preuve_ids"] = sorted(d["preuve_ids"])
        d["motifs_qualite"] = sorted(set(d["motifs_qualite"]))
        if d["applicabilite"] == "non_applicable_documentee" and d["applicabilite_reference"] is None:
            _fail("E_REFERENCE_NON_APPLICABILITE", "applicabilite_reference", "Justification de domaine obligatoire.")
        if d["applicabilite"] != "non_applicable_documentee" and d["applicabilite_reference"] is not None:
            _fail("E_NON_APPLICABILITE_INCOHERENTE", "applicabilite_reference", "Référence de non-applicabilité sur un autre état.")
        if d["signal_pression"] == "absence_validee" and not d["validite_absence"]:
            _fail("E_ABSENCE_INCOHERENTE", "validite_absence", "Absence affirmée sans capacité documentaire.")
        if d["contradiction_bloquante"] and d["contradiction_reference"] is None:
            _fail("E_CONTRADICTION_SANS_REFERENCE", "contradiction_reference", "Contradiction bloquante non justifiée.")
        if d["applicabilite"] == "non_applicable_documentee" and d["signal_pression"] in POSITIVE_SIGNALS:
            _fail("E_NON_APPLICABILITE_INCOHERENTE", "signal_pression", "Signal positif hors du domaine déclaré.")
        if d["signal_pression"] in POSITIVE_SIGNALS and d["validite_positive"] and not d["preuve_ids"]:
            _fail("E_PROUVE_POSITIVE_SANS_SOURCE", "preuve_ids", "Signal positif exploitable sans preuve identifiable.")
    pilot["familles_attendues"] = sorted(expected)
    cell["familles_attendues"] = sorted(expected)
    ordered = tuple(sorted(diagnostics, key=lambda d: canonical_json(d["diagnostic_id"])))
    return PreparedPriorityInputs(cell, pilot, ordered)


def _decode(value, field, expected_type):
    if isinstance(value, str):
        try:
            value = json.loads(value, parse_constant=lambda v: _fail("E_TYPE_INVALIDE", field, f"Constante {v} interdite."))
        except json.JSONDecodeError:
            _fail("E_TYPE_INVALIDE", field, "JSON structuré invalide.")
    if not isinstance(value, expected_type):
        _fail("E_TYPE_INVALIDE", field, "Structure JSON incompatible.")
    return value


def derive_positive_evidence(
    event: Mapping, *, crs, review: Mapping | None = None,
    approved_context_rules: Iterable[PotentialConflictRule] | None = None,
) -> dict:
    """Interface de QA par événement ; sans examen documenté, capacité false.

    ``review`` atteste adéquation d'échelle, liens sources et localisation pour
    CET événement. Les preuves déjà tracées par qualify_events/règles sont lues,
    sans réimplémenter de règle scientifique de promotion.
    """
    # Les définitions approuvées viennent de l'appelant, jamais de la trace de preuve.
    # L'attribut local conserve les règles explicitement passées à apply_* ; après
    # lecture GPKG/JSON, leur registre doit être fourni à nouveau par configuration.
    inherited_rules = getattr(event, "attrs", {}).get(CONTEXT_RULE_APPROVALS_ATTR, ())
    approvals = inherited_rules if approved_context_rules is None else approved_context_rules
    registry = {}
    for rule in approvals:
        try:
            validate_context_rule(rule)
        except (ValueError, TypeError):
            _fail("E_REFERENCE_PREUVE_INVALIDE", "approved_context_rules", "Définition de règle approuvée invalide.")
        key = (rule.rule_id, rule.version)
        if key in registry:
            _fail("E_REFERENCE_PREUVE_INVALIDE", "approved_context_rules", "Règle approuvée dupliquée.")
        registry[key] = rule
    event = dict(event)
    conflict_id = _id(event.get("conflit_id"), "conflit_id")
    status = event.get("statut")
    if status not in PRESSURES[:3] + ("non_concluant",):
        _fail("E_TYPE_INVALIDE", "statut", "Statut événement inconnu.")
    geometry = event.get("geometry")
    reasons = set()
    try:
        metric = CRS.from_user_input(crs) == CRS.from_user_input(METRIC_CRS)
    except (ValueError, TypeError, CRSError):
        metric = False
    if not metric:
        reasons.add("crs_evenement_non_metrique")
    if not isinstance(geometry, BaseGeometry) or geometry.is_empty or not geometry.is_valid:
        reasons.add("geometrie_intersection_invalide")
    if event.get("territory_relation") not in {"interieur", "interieur_et_frontiere"}:
        reasons.add("localisation_interieure_non_etablie")
    if status == "non_concluant":
        reasons.add("preuve_non_concluante")
    if event.get("detection_status") not in {"intersection_detectee", "contact_detecte"}:
        reasons.add("detection_non_documentee")
    precision = event.get("precision_m")
    if event.get("precision_affichage") == "localisation_validee" and (
        isinstance(precision, bool) or not isinstance(precision, Real) or not math.isfinite(precision)
        or precision <= 0 or not isinstance(event.get("precision_reference"), str) or not event["precision_reference"].strip()
    ):
        reasons.add("contrat_precision_non_documente")
    sources = _decode(event.get("source_ids"), "source_ids", dict)
    if set(sources) != {"routes", "corridors"} or any(not isinstance(v, list) or not v for v in sources.values()):
        reasons.add("liens_sources_non_etablis")
    else:
        for role, values in sources.items():
            for value in values:
                _id(value, f"source_ids.{role}")
            _unique(values, f"source_ids.{role}", "E_REFERENCE_SOURCE_INVALIDE")
    evidence = _decode(event.get("preuves"), "preuves", list)
    _decode(event.get("observations"), "observations", dict)
    _decode(event.get("limites"), "limites", list)
    if review is None:
        reasons.add("validation_positive_en_attente")
    else:
        _review(review, "review")
        if canonical_json(_id(review.get("conflit_id"), "review.conflit_id")) != canonical_json(conflict_id):
            _fail("E_REFERENCE_PREUVE_INVALIDE", "review.conflit_id", "Examen visant un autre événement.")
        for key in ("source_links_verified", "scale_adequate", "localization_resolved"):
            if not _bool(review.get(key), f"review.{key}"):
                reasons.add({"source_links_verified":"liens_sources_non_etablis", "scale_adequate":"echelle_non_adaptee",
                             "localization_resolved":"precision_localisation_insuffisante"}[key])
        if _period(review.get("periode_reference"), "review.periode_reference") is None:
            reasons.add("periode_preuve_non_documentee")
        if "source_ids" in review:
            reviewed_sources = _decode(review["source_ids"], "review.source_ids", dict)
            def source_key(values):
                return canonical_json({role: sorted(_list(ids, "source_ids"), key=canonical_json)
                                       for role, ids in values.items()})
            if source_key(reviewed_sources) != source_key(sources):
                _fail("E_REFERENCE_SOURCE_INVALIDE", "review.source_ids", "Sources de l'examen discordantes de l'événement.")
    binding = event_evidence_binding(event) if isinstance(geometry, BaseGeometry) and geometry.is_valid and not geometry.is_empty else None
    records = []
    for item in evidence:
        if not isinstance(item, dict):
            _fail("E_REFERENCE_PREUVE_INVALIDE", "preuves", "Preuve événement structurée requise.")
        if item.get("conflit_id") != conflict_id:
            continue
        contextual = item.get("kind") == "context_rule"
        human = not contextual and item.get("target_status") == status
        if contextual:
            if status != "conflit_potentiel" or event.get("evidence_level") != "regle_contextuelle_documentee":
                reasons.add("statut_regle_contextuelle_non_autorise")
                continue
            if not all(isinstance(item.get(k), str) for k in ("rule_id", "version")):
                reasons.add("regle_contextuelle_non_approuvee")
                continue
            rule = registry.get((item["rule_id"], item["version"]))
            if rule is None:
                reasons.add("regle_contextuelle_non_approuvee")
                continue
            if any(canonical_json(item.get(k)) != canonical_json(v) for k, v in asdict(rule).items()):
                reasons.add("trace_regle_contextuelle_divergente")
                continue
            observed = _decode(event.get("observations"), "observations", dict)
            if not context_rule_matches(observed, rule):
                reasons.add("contexte_regle_non_correspondant")
                continue
        if not human and not contextual:
            continue
        if contextual and (not isinstance(item.get("context_equals"), dict) or not item["context_equals"]):
            continue
        required = ("reference", "criteria", "validated_by", "validated_at") + (("rule_id", "version") if contextual else ())
        if not all(isinstance(item.get(k), str) and item[k].strip() for k in required):
            continue
        try:
            datetime.fromisoformat(item["validated_at"].replace("Z", "+00:00"))
        except ValueError:
            continue
        if binding is None or item.get("event_binding_sha256") != binding:
            reasons.add("preuve_evenement_perimee_ou_non_liee")
            continue
        records.append(item)
    if status == "conflit_potentiel" and not records:
        reasons.add("qualification_contextuelle_non_documentee")
    if status == "obstacle_confirme":
        if event.get("evidence_level") != "preuve_externe_documentee" or not records:
            reasons.add("preuve_externe_non_documentee")
    needs_resolution = (event.get("precision_affichage") != "localisation_validee"
                        or event.get("detection_status") == "contact_detecte"
                        or bool(event.get("numeric_residue", False))
                        or any(r.get("previous_status") == "non_concluant" for r in records))
    def resolved(record):
        if not all(isinstance(record.get(k), str) and record[k].strip() for k in (
            "localization_resolution_reference", "localization_validated_by", "localization_validated_at")):
            return False
        try:
            datetime.fromisoformat(record["localization_validated_at"].replace("Z", "+00:00"))
        except ValueError:
            return False
        return True
    if needs_resolution and not any(resolved(r) for r in records):
        reasons.add("precision_localisation_insuffisante")
    valid = not reasons
    limitations = set(reasons)
    if event.get("precision_sensitivity_scope") == "source_pair":
        limitations.add("sensibilite_paire_sans_conclusion_locale")
    return {"conflit_id": conflict_id, "signal_pression": status, "validite_positive": valid,
            "source_ids": deepcopy(sources),
            "preuve_ids": [conflict_id] if valid else [], "motifs_qualite": sorted(limitations),
            "references": sorted({r["reference"] for r in records} | ({review["reference"]} if review else set())),
            "authors_authenticated_by_software": False}


def prepare_route_corridor_diagnostic(
    diagnostic: Mapping, event: Mapping, *, crs, source_namespaces: Mapping[str, str],
    review: Mapping | None = None, approved_context_rules: Iterable[PotentialConflictRule] | None = None,
) -> dict:
    """Lie explicitement les sources/événement au diagnostic avant D/S.

    L'enjeu, l'applicabilité et leur méthode viennent du diagnostic fourni ; aucun
    attribut écologique n'est classé ici. Le pilote devra encore valider ce résultat.
    """
    if not isinstance(diagnostic, Mapping) or diagnostic.get("famille_id") != "route_corridor":
        _fail("E_FAMILLE_HORS_PERIMETRE", "famille_id", "Adaptateur réservé à route_corridor.")
    if not isinstance(source_namespaces, Mapping) or set(source_namespaces) != {"routes", "corridors"}:
        _fail("E_REFERENCE_SOURCE_INVALIDE", "source_namespaces", "Espaces de noms des deux thèmes requis.")
    for value in source_namespaces.values():
        _text(value, "source_namespaces")
    qa = derive_positive_evidence(event, crs=crs, review=review, approved_context_rules=approved_context_rules)
    if set(qa["source_ids"]) != set(source_namespaces) or any(not isinstance(ids, list) or not ids for ids in qa["source_ids"].values()):
        _fail("E_REFERENCE_SOURCE_INVALIDE", "source_ids", "Identifiants des deux thèmes requis pour le diagnostic.")
    expected = {canonical_json({"namespace": source_namespaces[role], "id": value})
                for role, ids in qa["source_ids"].items() for value in ids}
    declared = _list(diagnostic.get("source_objects"), "source_objects")
    _unique(declared, "source_objects", "E_REFERENCE_SOURCE_INVALIDE")
    if {canonical_json(source) for source in declared} != expected:
        _fail("E_REFERENCE_SOURCE_INVALIDE", "source_objects", "Sources du diagnostic discordantes de l'événement.")
    result = deepcopy(dict(diagnostic))
    result.update({key: deepcopy(qa[key]) for key in ("signal_pression", "validite_positive", "preuve_ids")})
    result["motifs_qualite"] = sorted(set(_list(result.get("motifs_qualite"), "motifs_qualite")) | set(qa["motifs_qualite"]))
    result["conflit_ids"] = [qa["conflit_id"]]
    result["preuve_positive"] = qa
    return result


def derive_absence_evidence(
    detection: ConflictDetection | None, study_geometry: BaseGeometry, *, crs,
    required_sources: Mapping[str, str], domain_review: Mapping | None = None,
    territory: gpd.GeoDataFrame | None = None,
    required_categories: list[str] | None = None, required_subframes: list[str] | None = None,
) -> dict:
    """Réutilise la complétude SIG ; sépare capacité négative et absence conclue.

    La géométrie est H∩T en L93. La revue thématique et temporelle est explicite,
    versionnée et déclarative. Un événement positif n'invalide pas la CAPACITÉ.
    """
    if not isinstance(study_geometry, BaseGeometry) or study_geometry.is_empty or not study_geometry.is_valid or study_geometry.area <= 0:
        _fail("E_SURFACE_INVALIDE", "study_geometry", "Emprise étudiée polygonale non vide requise.")
    try:
        if CRS.from_user_input(crs) != CRS.from_user_input(METRIC_CRS):
            _fail("E_TYPE_INVALIDE", "crs", "Emprise attendue en EPSG:2154.")
    except (ValueError, TypeError, CRSError) as exc:
        if isinstance(exc, PriorityInputError):
            raise
        _fail("E_TYPE_INVALIDE", "crs", "CRS métrique explicite requis.")
    if not isinstance(required_sources, Mapping) or set(required_sources) != {"routes", "corridors"}:
        _fail("E_REFERENCE_SOURCE_INVALIDE", "required_sources", "Deux sources documentaires identifiées requises.")
    for role, source_id in required_sources.items():
        _text(source_id, f"required_sources.{role}")
    reasons = set()
    count = None
    if territory is None:
        reasons.add("territoire_absence_non_verifie")
    else:
        territory_report = validate_geodataframe(territory, LayerSpec("territory", POLYGONS))
        if not territory_report.ok:
            _fail("E_PREUVE_INVALIDE", "territory", "Territoire invalide.")
        study = union_all(territory.to_crs(METRIC_CRS).geometry.to_numpy())
        if not study.covers(study_geometry):
            _fail("E_PERIMETRE_INVALIDE", "study_geometry", "Emprise étudiée hors du territoire.")
        if detection is not None and detection.territory_sha256 != territory_geometry_sha256(territory):
            _fail("E_PERIMETRE_INVALIDE", "territory", "Empreinte de territoire discordante de la détection.")
    if detection is None or not detection.analysis_performed:
        reasons.add("analyse_non_effectuee")
    elif not detection.report.ok:
        _fail("E_PREUVE_INVALIDE", "detection", "Détection bloquée non réutilisable.")
    else:
        if detection.events.crs is None:
            _fail("E_TYPE_INVALIDE", "events.crs", "CRS explicite requis.")
        events = detection.events.to_crs(METRIC_CRS)
        if events.geometry.isna().any() or events.geometry.is_empty.any() or not events.geometry.is_valid.all():
            _fail("E_PREUVE_INVALIDE", "events", "Événement invalide : absence non démontrable.")
        count = len(events.loc[events.geometry.intersects(study_geometry)])
        report = ValidationReport()
        for role, evidence in (("routes", detection.route_coverage), ("corridors", detection.corridor_coverage)):
            footprint = _coverage_geometry(evidence, role, report, detection.territory_sha256)
            if evidence.source_id != required_sources[role] or not _fully_covered(study_geometry, evidence, footprint):
                reasons.add(f"couverture_{role}_non_validee")
        if not report.ok:
            _fail("E_PREUVE_INVALIDE", "coverage", "Métadonnées de couverture incohérentes.")
    if domain_review is None:
        reasons.add("couverture_thematique_temporelle_non_validee")
    else:
        _review(domain_review, "domain_review")
        # La décision doit viser cette emprise exacte, pas une maille voisine.
        from analysis.detect_conflicts import geometry_key
        if domain_review.get("scope_geometry_key") != geometry_key(study_geometry):
            reasons.add("emprise_validation_non_correspondante")
        for key in ("categories_covered", "subframes_covered"):
            if not _bool(domain_review.get(key), f"domain_review.{key}"):
                reasons.add("couverture_thematique_non_validee")
        for required, field in ((required_categories, "covered_categories"), (required_subframes, "covered_subframes")):
            if required is None:
                reasons.add("perimetre_thematique_non_declare")
                continue
            for value in _list(required, field):
                _text(value, field)
            _unique(required, field, "E_PERIMETRE_INVALIDE")
            covered = _list(domain_review.get(field), field)
            for value in covered:
                _text(value, field)
            _unique(covered, field, "E_PERIMETRE_INVALIDE")
            if not set(required) <= set(covered):
                reasons.add("couverture_thematique_non_validee")
        period = _period(domain_review.get("periode_reference"), "periode_reference")
        source_periods = domain_review.get("source_periods")
        if not isinstance(source_periods, dict) or set(source_periods) != {"routes", "corridors"}:
            _fail("E_PERIODE_INVALIDE", "source_periods", "Périodes des deux thèmes requises.")
        if domain_review.get("source_ids") != dict(required_sources):
            reasons.add("sources_validation_non_correspondantes")
        for role, source_period in source_periods.items():
            covered_period = _period(source_period, f"source_periods.{role}")
            if period is None or covered_period is None or period[0] < covered_period[0] or period[1] > covered_period[1]:
                reasons.add("periode_absence_non_couverte")
    capable = not reasons
    absence = capable and count == 0
    return {"validite_absence": capable, "absence_etablie": absence,
            "nb_evenements_observes": count,
            "signal_pression": "absence_validee" if absence else None if count else "non_evalue",
            "motifs_qualite": sorted(reasons | ({"absence_non_demontree"} if not capable else set())),
            "references": [domain_review["reference"]] if domain_review else [],
            "authors_authenticated_by_software": False}


def detect_assertion_conflicts(assertions: list[dict], *, decision_reference: str | None = None) -> dict:
    """Compare présence/absence sur la même propriété, objet, emprise et période.

    Des périodes recouvrantes différentes ne sont pas présumées équivalentes.
    Un contrôle impossible reste non_evalue (booléen null), jamais « indépendant ».
    """
    _list(assertions, "assertions")
    identities, unknown, pairs = set(), False, []
    for assertion in assertions:
        if not isinstance(assertion, dict):
            _fail("E_TYPE_INVALIDE", "assertions", "Assertion structurée requise.")
        identity = canonical_json(_id(assertion.get("assertion_id"), "assertion_id"))
        if identity in identities:
            _fail("E_ID_DUPLIQUE", "assertion_id", "Assertion dupliquée.")
        identities.add(identity)
        for key in ("propriete", "objet_id", "emprise_id", "reference", "periode_reference"):
            if key not in assertion or assertion[key] is None:
                unknown = True
        for key in ("propriete", "emprise_id", "reference"):
            _text(assertion.get(key), f"assertion.{key}", nullable=True)
        if assertion.get("objet_id") is not None:
            _id(assertion["objet_id"], "assertion.objet_id")
        _period(assertion.get("periode_reference"), "assertion.periode_reference")
        _bool(assertion.get("validee"), "assertion.validee")
        if assertion.get("conclusion") not in {"presence", "absence"}:
            _fail("E_TYPE_INVALIDE", "conclusion", "Assertion binaire présence/absence requise.")
        if not assertion["validee"]:
            unknown = True
    for left, right in combinations(assertions, 2):
        if any(a.get(k) is None for a in (left, right) for k in ("propriete", "objet_id", "emprise_id", "reference", "periode_reference")):
            continue
        if not left["validee"] or not right["validee"]:
            continue
        if any(canonical_json(left[k]) != canonical_json(right[k]) for k in ("propriete", "objet_id", "emprise_id")):
            continue
        lp, rp = _period(left["periode_reference"], "periode"), _period(right["periode_reference"], "periode")
        if lp != rp:
            if max(lp[0], rp[0]) <= min(lp[1], rp[1]):
                unknown = True
            continue
        if left["conclusion"] != right["conclusion"]:
            pairs.append({"assertion_ids": sorted([left["assertion_id"], right["assertion_id"]], key=canonical_json),
                          "references": sorted({left["reference"], right["reference"]})})
    if pairs:
        _text(decision_reference, "decision_reference", code="E_CONTRADICTION_SANS_REFERENCE")
    evaluated = len(assertions) >= 2 and not unknown
    return {"contradiction_bloquante": True if pairs else False if evaluated else None,
            "contradiction_reference": decision_reference if pairs else None,
            "etat_controle": "contradiction_documentee" if pairs else "controle" if evaluated else "non_evalue",
            "assertions_incompatibles": sorted(pairs, key=canonical_json),
            "motifs_qualite": [] if evaluated else ["controle_contradiction_incomplet"]}


def derive_applicability(decision: Mapping | None = None) -> dict:
    """Interface déclarative de domaine, désactivée sans décision documentée."""
    if decision is None:
        return {"applicabilite":"inconnue", "applicabilite_reference":None,
                "motifs_qualite":["applicabilite_non_documentee"]}
    _review(decision, "applicabilite")
    if decision.get("valeur") not in APPLICABILITIES:
        _fail("E_TYPE_INVALIDE", "applicabilite", "Valeur de domaine inconnue.")
    return {"applicabilite":decision["valeur"], "applicabilite_reference":decision["reference"]
            if decision["valeur"] == "non_applicable_documentee" else None,
            "methode_reference":dict(decision), "authors_authenticated_by_software":False, "motifs_qualite":[]}


def classify_ecological_stakes(decision: Mapping | None = None) -> dict:
    """Aucun seuil ni mapping réservoir/corridor→classe ; décision externe seule."""
    if decision is None:
        return {"enjeu_classe":"inconnu", "enjeu_methode_id":None, "motifs_qualite":["enjeu_non_documente"]}
    _review(decision, "enjeu")
    if decision.get("valeur") not in STAKES:
        _fail("E_TYPE_INVALIDE", "enjeu_classe", "Classe d'enjeu inconnue.")
    return {"enjeu_classe":decision["valeur"], "enjeu_methode_id":decision["methode_id"],
            "methode_reference":dict(decision), "authors_authenticated_by_software":False, "motifs_qualite":[]}
