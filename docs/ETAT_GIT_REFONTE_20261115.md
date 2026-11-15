# État Git pour la revue de la refonte

> Rapport historique de la phase précédente. État final et corrections : [dossier MVP](FINALISATION_MVP_20261115.md).

15 novembre 2026. Aucun fichier ajouté à l’index, aucun commit, push, merge ou déploiement.

## Worktree applicatif

Branche `feat/integration-actions-ui`, HEAD `b2c7287`. La table inclut tous les fichiers modifiés ou non suivis, et distingue les changements de cette intervention des changements préexistants conservés.

| État Git | Fichier | Intervention |
| --- | --- | --- |
| ` M` | `backend/server.py` | Modifié pendant la refonte |
| ` M` | `frontend/package-lock.json` | Préexistant, conservé inchangé |
| ` M` | `frontend/package.json` | Modifié pendant la refonte |
| ` M` | `frontend/src/app/Root.tsx` | Modifié pendant la refonte |
| ` M` | `frontend/src/components/layout/SiteHeader.tsx` | Préexistant, conservé inchangé |
| ` M` | `frontend/src/components/map/RealGridLayer.tsx` | Modifié pendant la refonte |
| ` M` | `frontend/src/components/map/RegionMap.tsx` | Modifié pendant la refonte |
| ` M` | `frontend/src/components/sector/TerritorialZoneDetail.tsx` | Préexistant, conservé inchangé |
| `??` | `backend/multiactions_v2.py` | Modifié pendant la refonte |
| `??` | `backend/tests/test_multiactions_v2_local.py` | Modifié pendant la refonte |
| `??` | `docs/ETAT_GIT_REFONTE_20261115.md` | Nouveau rapport |
| `??` | `docs/INTEGRATION_MULTIACTIONS_V2_LOCALE_20261112.md` | Préexistant, conservé inchangé |
| `??` | `docs/REFONTE_FINALE_20261115.md` | Ajout pendant la refonte |
| `??` | `frontend/RECETTE_LISIBILITE_20261113.md` | Préexistant, conservé inchangé |
| `??` | `frontend/scripts/smoke-action-family-visuals.cjs` | Préexistant, conservé inchangé |
| `??` | `frontend/scripts/smoke-multiactions-v2.cjs` | Modifié pendant la refonte |
| `??` | `frontend/scripts/verify-action-presentations.mjs` | Modifié pendant la refonte |
| `??` | `frontend/scripts/verify-multiactions-v2.mjs` | Modifié pendant la refonte |
| `??` | `frontend/scripts/verify-production-safety.mjs` | Ajout pendant la refonte |
| `??` | `frontend/src/components/experimental/ActionFamilyIcon.tsx` | Préexistant, conservé inchangé |
| `??` | `frontend/src/components/experimental/JustificationLevels.tsx` | Préexistant, conservé inchangé |
| `??` | `frontend/src/components/experimental/LocalReview.tsx` | Ajout pendant la refonte |
| `??` | `frontend/src/components/experimental/MultiActionsMethodPage.tsx` | Modifié pendant la refonte |
| `??` | `frontend/src/components/experimental/MultiActionsV2View.tsx` | Modifié pendant la refonte |
| `??` | `frontend/src/components/experimental/TerritorialPriorityLegend.tsx` | Ajout pendant la refonte |
| `??` | `frontend/src/components/experimental/action-family-icons.LICENSE.txt` | Préexistant, conservé inchangé |
| `??` | `frontend/src/components/experimental/multiActionsV2.css` | Modifié pendant la refonte |
| `??` | `frontend/src/integrations/actionFamilyVisuals.ts` | Préexistant, conservé inchangé |
| `??` | `frontend/src/integrations/actionPresentation.ts` | Modifié pendant la refonte |
| `??` | `frontend/src/integrations/multiActionsV2Adapter.ts` | Modifié pendant la refonte |
| `??` | `frontend/src/integrations/territorialPresentation.ts` | Ajout pendant la refonte |

## Worktree scientifique

Branche `feat/m2-multi-actions`, HEAD `66a4723`. Les fichiers suivants étaient déjà non suivis au début ; leurs empreintes sont inchangées. Aucun nouveau traitement, export ou changement scientifique n’a été ajouté.

```text
?? analysis/auditer_multiactions_caen.py
?? analysis/moteur_multiactions_experimental.py
?? analysis/moteur_multiactions_experimental_v2.py
?? analysis/verifier_audit_multiactions_caen.py
?? docs/audit_methodologique_m2_multiactions_20261112.md
?? docs/contrat_m2_m4_m3_multiactions_experimental_v1.md
?? docs/contrat_m2_m4_m3_multiactions_experimental_v2.md
?? docs/matrice_problemes_actions_m2_multiactions_20261112.json
?? docs/plan_validation_m2_multiactions_20261112.json
?? docs/proposition_contrat_m2_multiactions_v2.schema.json
?? docs/rapport_m2_multiactions_experimental_20261112.md
?? docs/rapport_m2_multiactions_experimental_v2_20261112.md
?? docs/schema_m2_multiactions_experimental_v1.json
?? docs/schema_m2_multiactions_experimental_v2.json
?? tests/test_audit_multiactions_caen.py
?? tests/test_moteur_multiactions_experimental.py
?? tests/test_moteur_multiactions_experimental_v2.py
```

## Index et données sensibles

- Index Git vide dans les deux worktrees.
- Aucun ZIP, GeoPackage, export interne, fichier `.env`, clé privée ou base locale dans les fichiers non suivis non ignorés.
- Les captures et reçus sont ignorés sous `data/derived/refonte_finale_ui_20261115/`.
- Les 15 ressources publiques, les lots scellés, les fichiers M2 et le lockfile sont inchangés depuis le début de cette refonte.
- Le lockfile conserve son changement préexistant de quatre marqueurs `peer` retirés : à examiner séparément, sans changement de version de dépendance.
- La note historique de lisibilité contient des chemins personnels et doit être écartée d’un ajout destiné au public ou neutralisée à l’étape autorisée.

## Références distantes et conflit

- `origin/main` local : `cb6856f`, référence non rafraîchie pendant cette intervention.
- `main` distant consulté en lecture seule : `14f6c7f`, deux nouveaux commits.
- Tête distante de la PR #5 : `b2c7287`, identique au HEAD local applicatif.
- Comparaison distante : branche deux commits en avance et deux en retard.
- Simulation textuelle en dossier temporaire : un conflit dans `frontend/src/styles/global.css` ; zéro conflit textuel dans `Root.tsx` et `CataloguePage.tsx`.
- Extraction distante de styles dans `frontend/src/styles/doc-pages.css` à préserver lors de la réconciliation future.
- Aucune résolution, mise à jour de référence, fusion ou modification distante exécutée.

La procédure de préparation sans push et les limites scientifiques figurent dans [REFONTE_FINALE_20261115.md](REFONTE_FINALE_20261115.md).
