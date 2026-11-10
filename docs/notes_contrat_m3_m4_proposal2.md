# ReConnect Normandie — Évolution proposée du contrat M2 → M3/M4

**Version proposée :** `m2-m4.proposal-2` (à confirmer avec M3/M4).  
**Statut :** information de coordination du 3 novembre 2026, **pas une modification du contrat existant** `m2-m4.proposal-1`.

## Champs à réserver sur les fiches de mailles

| Champ proposé | Type prévu | Signification |
|---|---|---|
| `priorite_examen` | objet `{etat, valeur}` | `etat` = `non_calculee`, `calculee`, `indeterminee`, `hors_territoire`; `valeur` = `elevee`, `moderee`, `faible` ou `null`. Valeur non nulle uniquement si `calculee`. |
| `couverture_synthese` | `complete`, `partielle` ou `null` | **Complétude décisionnelle** des diagnostics attendus, non garantie d'exhaustivité spatiale des couches SIG. `null` pour hors territoire ou non calculé. |
| `regle_appliquee` | `S0`, `S1`, `S2`, `S3`, `S4` ou `null` | Règle de synthèse exécutée, pas score caché. |
| `diagnostic_ids_justificatifs` | tableau d'identifiants uniques | Diagnostics ayant conduit à la priorité retenue. |
| `diagnostic_ids_non_evalues` | tableau d'identifiants uniques | Diagnostics à résultat `indetermine`, y compris `signal_non_qualifie` avec couverture complète. |
| `motifs_limites` | tableau de codes normalisés | Inconnues de données, contradiction, interprétation non qualifiée, familles manquantes et autres limites. |

**À conserver :** `maille_id`, `grid_version`, `method_version`, `dataset_version`, `statut_analyse`, `diagnostics[]`, `indicateurs`, `qualite`, `conflit_ids[]`, `action_ids[]` et géométrie CRS84 selon droits. Pas de conversion des tableaux en chaînes JSON. Les codes D précis, les objets source et les références de preuve restent dans `fiches_zones.json` (version M2) ; ce dernier doit aussi pouvoir identifier les familles attendues absentes.

**Attention état `aucun_signal` :** il signifie seulement qu'aucun signal entrant dans les règles validées du périmètre n'a été détecté avec les preuves négatives nécessaires. Une priorité faible ne signifie jamais « faible biodiversité ». Le mode exact d'affichage (`aucun_signal` parmi les états de diagnostic plutôt qu'une nouvelle catégorie de priorité) est à valider avec M3.

## Relations et compatibilité

- `conflits.geojson` reste **distinct** de `mailles.geojson`, avec liaison `conflit_id ↔ maille_id` et géométrie pouvant être `null` pour raisons de diffusion.
- `fiches_zones.json` contient les diagnostics détaillés, sources, périodes, preuve de fiabilité, règle D/S et associations calculées.
- `catalogue_actions.json` conserve 12 fiches M5 et des `action_id` compatibles.
- M2 spécifie les quatre règles R1–R4 ; M4 implémente le moteur des actions. Pas de classement artificiel par efficacité.
- Tant que les schémas M4 n'ont pas été validés, **ne pas modifier les schémas `m2-m4.proposal-1` en place**, ni produire de GeoJSON de production.
- Prévoir des tests des deux versions (`proposal-1` non-régression et `proposal-2` sur fixtures synthétiques), une migration versionnée et un contrat d'API explicite.

## Points à confirmer avec M3/M4

1. Stockage de `priorite_examen` (`{etat,valeur}` recommandé), traitement de `null` et du hors-territoire.
2. Affichage cartographique **simple** : couleurs élevée/modérée/faible/indéterminée, et un libellé limité à la portée scientifique de la carte.
3. Badge « évaluation partielle » pour une maille dont `couverture_synthese=partielle` ; aucun détail des calculs imposé sur la carte.
4. Au clic : problèmes rencontrés, liste **non classée par efficacité** d'actions regroupées par pertinence et conditions, courte explication « pourquoi ? ».
5. Géométries de conflits masquées par défaut, exposition contrôlée des données sensibles et relations plusieurs-à-plusieurs.
6. Version commune et stable des identifiants `diagnostic_id`, `conflit_id`, `maille_id` et `action_id`.

Ce document est une proposition technique ; les noms définitifs des propriétés et chemins de `fiches_zones.json` doivent être approuvés par l'équipe avant publication.

## Implémentation interne disponible au 3 novembre 2026

`analysis/prepare_priority_inputs.py` contrôle la configuration pilote, les
diagnostics et les preuves amont. `analysis/evaluate_priorities.py` exécute D0–D10a
puis S0–S4. Ce moteur pur renvoie une priorité **interne** catégorielle (`elevee`,
`moderee`, `faible`, `indeterminee`, ou null pour S0), avec la version distincte
`priority_method_version=m2-priorites.proposal-2`. Il ne modifie ni les deux schémas
GeoJSON actuels, ni `analysis/export_m2_contract.py`, ni `docs/api_contract_m2_m4.md`.
Aucun export proposal-2 ou fichier public n'est activé.

Pour une future migration, l'adaptateur M3/M4 devra transformer explicitement :

| Résultat interne | Objet futur proposé `priorite_examen` |
| --- | --- |
| `elevee`, `moderee`, `faible` | `{etat: calculee, valeur: <catégorie>}` |
| `indeterminee` | `{etat: indeterminee, valeur: null}` |
| S0 | `{etat: hors_territoire, valeur: null}` |
| Étape D/S non exécutée | `{etat: non_calculee, valeur: null}` |

Transmettre aussi `couverture_synthese`, `regle_appliquee`,
`diagnostic_ids_justificatifs`, `diagnostic_ids_non_evalues`, `motifs_limites`,
`priority_method_version` et le périmètre déclaré. `couverture_synthese=complete`
ne peut pas être substitué aux preuves de couverture SIG dans `qualite`.

Les détails internes conservent `diagnostics[]`, `familles_manquantes`,
`regles_diagnostics`, `motifs_principaux_diagnostics`, `liens_diagnostics`,
`source_objects`, `phenomene_id`, les références et les entrées normalisées.
Les recoupements n'entraînent aucun bonus de priorité, et l'absence de lien connu
reste `relation_non_etablie`. Ces informations sont candidates au dossier interne
M2 / `fiches_zones.json`, sous réserve des droits ; elles ne sont pas toutes publiques.

**Point de représentation à confirmer :** les deux index par diagnostic sont des
dictionnaires Python à clés typées. JSON ne préserve pas une clé entière distincte
d'une clé chaîne de même écriture (`1` / `"1"`). Pour la future sérialisation,
utiliser les enregistrements typés de `diagnostics[]` ou une représentation de
couples explicitement convenue ; ne pas convertir silencieusement les identifiants.

**Clarification des motifs :** les 38 fixtures conservent les motifs concluants
D5–D9 et D0 dans `motifs_principaux_diagnostics`, et réservent `motifs_limites` aux
limites QA, motifs d'indétermination et motifs synthétiques. L'implémentation suit
ces attentes sans modifier les oracles. Cette précision doit accompagner la revue
de la formulation « union des motifs principaux » de la table.

Les comparaisons de contradictions sans métadonnées suffisantes produisent un état
non évalué, pas une absence certifiée de contradiction. Les classes d'enjeu et
l'applicabilité sont des décisions externes documentées ; aucune classification
automatique n'est activée. Les validations d'auteurs restent déclaratives.

Le [compte rendu local](verification_m2_priorites.md) détaille les tests. Les
conventions de triage et leur application à des données réelles restent à approuver.
La future migration demandera des tests de schéma proposal-2 et une revue des
champs publics. Le catalogue M5 et le moteur d'actions M4 n'ont pas été modifiés.

## Audit correctif : représentation JSON et états distincts

`prepare_priority_result_json()` dans `analysis/export_priority_results.py`
fournit une représentation interne sans perte, identifiée par
`priority_result_format_version=m2-priorites.internal-json-1`. Cette fonction pure
n'écrit aucun fichier et ne remplace ni schéma public ni contrat GeoJSON. Les
index Python gardent leurs clés typées ; seule la copie JSON les transforme :

```json
{
  "regles_diagnostics": [
    {"diagnostic_id": "1", "regle_D": "D7"},
    {"diagnostic_id": 1, "regle_D": "D5"}
  ],
  "motifs_principaux_diagnostics": [
    {"diagnostic_id": "1", "motif_principal": "pression_observee_enjeu_moyen"},
    {"diagnostic_id": 1, "motif_principal": "conflit_etaye_enjeu_fort"}
  ]
}
```

L'adaptateur refuse les clés non textuelles dans les autres objets et les valeurs
non finies, sans conversion silencieuse. Les deux index doivent utiliser cette
forme tableau s'ils sont sérialisés ; cette représentation proposée reste à
approuver avec M3/M4. La priorité devient explicitement l'objet `{etat,valeur}`
décrit dans le tableau de migration ci-dessus.

Trois informations sont désormais séparées dans le résultat interne :

| Champ | Portée |
| --- | --- |
| `statut_analyse` | État SIG fourni en entrée (`analyse_effectuee`, `absence_analyse`) ou `null` si inconnu ; `hors_territoire` pour S0 |
| `etat_calcul_priorite` | `calculee`, `indeterminee` ou `hors_territoire`, selon D/S ; `non_calculee` reste à l'orchestrateur quand D/S n'est pas exécuté |
| `couverture_synthese` | Complétude décisionnelle `complete`, `partielle` ou `null` pour S0, jamais une couverture SIG |

Une surface positive sans diagnostic produit S4, priorité indéterminée et couverture
partielle. Elle ne permet pas d'inférer un état SIG ; celui-ci reste `null` s'il
n'est pas fourni. Un état SIG explicitement fourni peut être conservé sans
diagnostic de priorité disponible. Ceci corrige l'ancien `analyse_effectuee`
systématique du moteur D/S. Le futur contrat devra accepter cet inconnu ou utiliser
un champ SIG distinct ; **aucune modification de proposal-1** n'est effectuée.

Les détails conservent le contrôle trivalent, sa cible, ses références et la trace
avant intégration. Une preuve indépendante peut soutenir un signal fiable malgré
un contrôle inconnu, tout en maintenant la couverture partielle lorsqu'il affecte
la décision. Les nouvelles preuves de qualification exigent une empreinte d'état
et, pour les règles contextuelles, un registre approuvé distinct. Les anciennes
traces sans empreinte ne sont pas réutilisables automatiquement par la QA renforcée.

Les références et champs privés de la représentation interne ne constituent pas
une liste d'autorisation publique. Les droits et validations M1/M2, puis la revue
M3/M4 restent nécessaires avant toute chaîne réelle de diffusion.
