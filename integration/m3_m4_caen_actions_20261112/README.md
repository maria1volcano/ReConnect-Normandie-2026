# Références M2 — priorités indicatives d’étude des actions

**Statut : exemples historiques et interfaces internes M2, sans application automatique.**
Ces fichiers accompagnent la livraison du 12 novembre 2026. Ils ne sont branchés
ni au frontend ni au backend de production. Le schéma normalisé M2 documente les
décisions internes ; il ne remplace pas un contrat public ni le catalogue M5.

L’intégration applicative réelle est distincte : PR #5 sur
`feat/integration-actions-ui`. Cette sauvegarde ne modifie ni cette branche ni sa
PR. **Ne pas réappliquer le patch historique sur `main` ou sur la PR #5.**

## Exemple M3 figé

Le patch, `CaenActionsDetail.tsx` et le plugin local illustrent le raccordement
contre `feat/m3-frontend-reconnect-v61`, commit
`94eef5b8f17dc68af22c323603ec2623b2b58ce1`. Cette compatibilité ne vaut pas pour le
code applicatif actuel. Les anciens patches V1/V2 ne doivent pas être empilés.
`compatibilite_M3.json` enregistre la base, les huit fichiers et l’absence
d’application automatique. Les codes de règles visibles dans cet exemple ne
remplacent pas la présentation retenue par M3/M4 dans l’application.

Pour reproduire uniquement cet exemple depuis le dépôt M2 :

```bash
python3 -B integration/m3_m4_caen_actions_20261112/preparer_patch_m3.py --output data/derived/revue_exemple_m3_caen
```

Le dossier doit être nouveau et rester sous `data/derived/`, ignoré par Git.
Le générateur lit le commit figé avec `git show`, écrit une copie et un patch
dans ce dossier, puis s’arrête. Il ne fait ni checkout, ni application de patch,
ni accès en écriture à une branche applicative. Aucun résultat scellé n’est repris.
Une adaptation ultérieure nécessite une revue explicite par M3/M4 du code réel.

## Exemple M4 et relations du lot

`m4_caen_actions_router.py` est un routeur de référence facultatif, non enregistré
automatiquement dans une application. Le plugin M3 ne sert qu’en développement.
Ils nécessitent une configuration volontaire de `M2_CAEN_LOT_ROOT` hors des
répertoires publics et une écoute sur `127.0.0.1`. Les clients externes et les
en-têtes de proxy sont refusés. Ne pas les exposer par un reverse proxy public.

Leurs endpoints de référence sont sous `/__internal/m2/caen/` : six fichiers
JSON/GeoJSON internes et `/fiches/{maille_id}?grid_version=...&territory_id=...`.
Une mauvaise portée ou une version opérationnelle différente renvoie 409 ; une
maille absente 404. Aucun ZIP, GeoPackage, chemin libre ou exporteur public n’est
exposé. Ce mécanisme ne remplace pas les routes réellement utilisées par M4.

Dans le lot, les fichiers complémentaires sont :

- `demo_interne/priorites_etude_interventions.json` : 101 décisions, action
  principale, options, justifications, préconditions et copie distincte de D/S.
- `demo_interne/pistes_investigation_trace.json` : 165 pistes d’origine, identifiants
  stables, pointeurs, empreintes et rôle actuel.

Jointure obligatoire : **(`territory_id`, `grid_version`, `maille_id`)**.
Les événements sont reliés par `conflit_id` dans cette même portée. Les 5 336
événements admis, leurs géométries et les comptes exclusifs ne sont pas recalculés.
L’événement en quarantaine reste exclu des comptes et de l’affichage.

## Sémantique à conserver

- `decision_interventions.action_principale` et `.actions_complementaires`
  définissent la sélection ; `options_actions` conserve les non-sélections motivées.
- `a_instruire_indicatif` concerne l’étude. Les statuts scientifiques des
  `actionResult` restent `non_evaluable / A2`, sans promotion implicite.
- `action_ids` des mailles et `action_ids_a_etudier` des fiches contiennent A04
  dans les 60 rouges/orange et [] ailleurs. Leurs anciennes valeurs restent dans
  `action_ids_pistes_historiques` et `action_ids_a_etudier_reference_v2`.
- `actions` conserve les descriptions historiques pour audit. Ce champ seul n’est
  pas une liste de recommandations. Les 165 pistes restent traçables ; 105 ne sont
  pas activées en restauration. Les huit pistes R3 en gris ne choisissent rien.
- Les neuf jaunes orientent vers la préservation sans fiche M5 inventée. Les
  32 grises restent non évaluables, même en présence de végétation OCS GE.
- La priorité indicative et D/S restent séparées ; aucun risque confirmé, urgence,
  bénéfice comparé ou travaux validé n’est déduit. `test_data=False` et les verrous
  de publication restent inchangés. Ce lot et ces serveurs de revue sont internes.

## Scellement et preuves locales

`analysis/sceller_priorites_actions_caen.py` refuse un lot déjà scellé avant toute
écriture. Les journaux M3 doivent être fournis sous `M2_VALIDATION_LOG_ROOT`
(ou dans le répertoire de sortie M2 par défaut) : `build_M3_actions.log` et
`tests_M3_priorities.log`. Aucun chemin temporaire de poste n’est imposé et aucune
preuve manquante n’est remplacée par un journal fictif. Ne pas relancer une livraison
scellée pour sauvegarder son code dans Git.
