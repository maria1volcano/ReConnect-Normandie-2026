# ReConnect Normandie — recette de lisibilité

> Rapport historique de la phase précédente. État final et corrections : [dossier MVP](../docs/FINALISATION_MVP_20261115.md).

13 novembre 2026. Intervention limitée au frontend local du worktree `reconnect-actions-ui`.

La fiche conserve une lecture complète : nom, icône Lucide et justification, deux à trois phrases sur les observations et leur intérêt écologique, puis une à deux phrases sur l’intervention à étudier. Les indicateurs chiffrés, leur interprétation et trois vérifications propres à chaque famille restent accessibles dans « En savoir plus ». Une seule réserve scientifique générale apparaît au bas de la fiche.

Les explications des milieux humides distinguent désormais précisément le recouvrement d’un réservoir de biodiversité et les relations d’un plan d’eau avec les inventaires. Les détails expliquent les comptes d’objets et de relations, les recouvrements très faibles, les méthodes d’inventaire et les projets déjà recensés sur les friches. Les données et les classements reçus ne sont pas modifiés.

La carte reste unique et neutre. La légende et la page « Méthode et sources » partagent les mêmes explications des niveaux A/B/C, sans traduction en urgence ou priorité de travaux. L’ancienne adresse `/catalogue` reste dans ce parcours lorsqu’il est explicitement activé. Les données détaillées et les classifications historiques sont conservées dans les ressources techniques. Le thème sombre et les contrastes sont cohérents sur la page Méthode.

## Vérifications réussies

| Contrôle | Résultat |
| --- | --- |
| Mailles chargées, présentées et parcourues dans Chrome | 101 |
| Pistes présentées et comparées à la réponse API dans Chrome | 205 |
| Secteurs sans proposition | 13 |
| Niveaux A / B / C inchangés | 93 / 45 / 67 |
| Vérifications par solution dans les détails | 3 |
| Texte principal explicatif | 83 mots au maximum |
| Largeurs vérifiées, carte et méthode | 320, 390, 768, 1024 et 1440 px |
| Clic réel sur une maille en mobile, cadrage conservé | Réussi |
| Ouverture des détails au clavier | Réussie |
| Erreur de chargement d’une fiche et réessai | Réussis |
| Mauvaise version de données | Rejetée |
| Ancien parcours réintroduit par `/catalogue` en mode expérimental | Non |
| Activation expérimentale dans le build de production, même avec le drapeau | Refusée |
| Erreurs JavaScript / requêtes de page externes | 0 / 0 |
| Contraste minimal des textes des sections Méthode | 11,36:1 |
| TypeScript et build final | Réussis |

Les tests existants de priorités et d’actions sont également passés. Le test `test:action-presentations` vérifie les explications et l’absence de mutation des 101 réponses. Le test navigateur V2 parcourt maintenant toutes les mailles et cartes, en complément de six cas représentatifs détaillés.

Commandes frontend principales :

```sh
npm run test:priorities
npm run test:actions
RECONNECT_V2_API_URL=http://127.0.0.1:8768 npm run test:multiactions-v2
RECONNECT_V2_API_URL=http://127.0.0.1:8768 npm run test:action-presentations
PLAYWRIGHT_MODULE_PATH=${HOME}/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core \
  RECONNECT_V2_PREVIEW_URL=http://127.0.0.1:5185 \
  RECONNECT_UI_QA_DIR=/tmp/reconnect-ui-qa-20261113-results \
  npm run test:browser:multiactions-v2
VITE_M2_MULTIACTIONS_V2=1 VITE_M4_API_BASE_URL=static \
  npm run build -- --outDir /tmp/reconnect-ui-final-build-20261113
```

Les reçus JSON et captures se trouvent dans `/tmp/reconnect-ui-qa-20261113-results/`. Le contrôle complémentaire de la page Méthode est reproductible avec `/tmp/reconnect-method-qa-20261113.cjs`. Les fichiers de recette temporaires ne sont pas publiés.

## Préservation

Le contrôle des empreintes avant/après porte sur 1 603 fichiers existants des deux worktrees, hors Git, dépendances, caches et builds. Seuls huit fichiers existants du frontend ont changé ; le composant de légende partagée et cette note sont les deux ajouts. Les changements antérieurs de l’utilisateur sont préservés.

Les résultats M2, classements, calculs, contrats, données publiques, backend, adaptateur V2 et lockfile sont inchangés. Les protections de développement local, de boucle locale, de version et de publication restent actives. Aucun commit, push, merge ou déploiement n’a été effectué.

Le build conserve l’avertissement existant sur la taille du module MapLibre. Il n’empêche pas la compilation.

Accès local de revue : http://127.0.0.1:5184/ ; API existante : http://127.0.0.1:8768/health.
