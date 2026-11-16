# Recette de l’interface commune — 16 novembre 2026

## Verdict

**Le rendu corrigé est prêt pour une revue locale.** Le public et la revue V2 utilisent désormais les mêmes composants de carte, de recherche, de fiche, de navigation et de Méthode. Les différences restantes décrivent les deux contrats de données, sans fabriquer de niveaux ou de propositions.

**La publication des 205 propositions V2 reste non autorisée.** Aucun export expérimental n’a été copié dans les fichiers servis. Aucun commit, push, merge ou déploiement n’a été effectué pour cette correction.

Travail dans `reconnect-actions-ui`, branche `feat/integration-actions-ui`, HEAD conservé à `08ad65011eeca458d974913b8608508bd1979114`. La branche scientifique et ses calculs restent inchangés.

## 1. Cause de la divergence et audit avant correction

`Root.tsx` sélectionnait une interface entière selon l’environnement : `LocalReview` en développement V2, `App → ApplicationLayout` dans le build public. La même séparation concernait la page Méthode. Le build et ses anciens tests confirmaient cette divergence : ils exigeaient expressément l’absence de la nouvelle présentation dans la production. Une compilation réussie ne garantissait donc pas le rendu validé localement.

| Élément avant correction | Revue locale V2 | Public historique | Prévisualisation Vercel existante |
| --- | --- | --- | --- |
| Entrée Carte | `LocalReview → MultiActionsV2View` | `App → ApplicationLayout` | Le code du SHA `08ad650` emprunte la branche publique de `Root` |
| Organisation | Carte compacte, recherche commune/secteur, fiche à côté | Tableau de bord historique, panneaux et contrôles distincts | Même branche de code historique ; pas une compilation de la revue locale |
| Navigation | Carte, Méthode et sources | Carte, Méthode, Catalogue | Navigation publique attendue d’après le code déployé |
| Fiches | Pourquoi cette action ? / Solution envisageable / En savoir plus | `TerritorialZoneDetail`, `ActionStudy` et présentations historiques | Anciennes fiches attendues d’après le code |
| Méthode | `MultiActionsMethodPage`, neuf sections, trois formules, douze références | `MethodePage`, autre structure, variante historique locale | Page publique attendue d’après le code |
| Données | 101 secteurs, 205 propositions, niveaux fournis A/B/C | 101 secteurs, 404 examens familiaux dont 165 pistes, aucun A/B/C | Données historiques du build public |
| Accès réellement observé pendant cette recette | Application locale vérifiée | Build statique local vérifié | Redirection anonyme vers `https://vercel.com/login`, titre « Login – Vercel » ; aucun en-tête applicatif observable |

La dernière colonne distingue le chemin déterminé par le code du rendu réellement observable. L’application distante protégée n’a pas été déclarée visuellement validée ; aucune protection Vercel n’a été contournée.

Composants anciens du parcours public audité :

- `ApplicationLayout` orchestrait la carte, les vues historiques et les panneaux.
- `PriorityLegend`, `DocumentaryLegend` et `StudyLegend` fournissaient les légendes conditionnelles.
- `DepartmentPanel`, `ZoneDetail` avec `OCSRow`, `TerritorialZoneDetail` avec `ActionStudy` fournissaient les anciens panneaux et fiches.
- `CataloguePage` gardait son propre parcours de filtres et cartes ; `MethodePage` avait son propre contenu et pouvait charger `HistoricalMethodePage` en revue historique.
- `SiteHeader`, `RegionMap` et `RealGridLayer` étaient déjà utilisés des deux côtés. Ils sont réutilisés, avec le même en-tête et les contrôles compacts de la conception V2.

Après correction, les anciens panneaux, légendes et pages historiques ne sont plus atteints par `Root` et ne sont pas inclus comme interfaces actives du build. Leur code historique demeure dans le dépôt pour traçabilité, sans entrée utilisateur. `/catalogue` ouvre désormais la carte commune, y compris avec un secteur dans l’URL.

## 2. Corrections et séparation des responsabilités

### Présentation commune

`components/journey/JourneyView.tsx` et `JourneyMethodPage.tsx` reprennent l’organisation de la revue locale. Les icônes Lucide, la légende, l’aide aux justifications et la feuille `journey.css` sont mutualisées. Les anciens composants V2 deviennent de petites entrées vers cette présentation avec la source locale.

Les deux parcours ont un seul en-tête, le symbole PNG local transparent, les liens « Carte » et « Méthode et sources », une seule carte avec les mêmes contrôles, la recherche sans distinction d’accents et un sélecteur de secteurs lisibles. Les fiches conservent les explications, une intervention envisageable, les détails et trois vérifications, avec une seule réserve générale en bas.

La Méthode partage ses sections, les trois formules et leur provenance, les références par famille et les douze références bibliographiques. Les références scientifiques et le composant de traçabilité existants n’ont pas été modifiés. Les règles, les effectifs et l’exemple réel proviennent du contrat sélectionné ; les totaux d’inventaire propres à la revue locale restent dans son adaptateur.

### Contrats distincts

`journeyModel.ts` décrit des valeurs de présentation. Son union distingue une piste historique sans niveau et une proposition expérimentale avec le niveau reçu. Il ne fait pas passer un objet historique pour une action V2.

`localJourneyAdapter.ts` appelle les lecteurs V2 existants et conserve les 205 propositions, leur ordre, leurs niveaux et leur texte éditorial validé. Les contrôles de `multiActionsV2Adapter.ts` sont inchangés : développement, drapeau explicite, hôte loopback, vérification du contrat, des versions et des statuts. Cet adaptateur reste derrière l’import dynamique réservé au développement.

`publicJourneyAdapter.ts` lit exclusivement les deux fichiers historiques déjà publics. Il conserve uniquement les examens dont le statut reçu est `a_etudier`, sans reconstituer de propositions à partir des comptes. Les autres familles ont un état adapté. Il conserve l’ordre fourni par le contrat et ne sélectionne pas d’action principale.

Les catégories documentaires reçues sont renommées pour la lecture de la carte, avec la palette commune ; aucun classement n’est recalculé à partir des observations. La numérotation des secteurs est une présentation stable des identifiants triés, et non un résultat scientifique. Les données originales ne sont pas modifiées.

### Permissions de publication

`publicDataPolicy.ts` autorise uniquement le périmètre historique et les empreintes SHA-256 exactes de ses deux fichiers publics. Le lecteur public vérifie ces empreintes, le contrat, la grille et les totaux attendus. Une réponse remplacée ou un contrat expérimental est refusé. Une erreur reste un état d’indisponibilité avec possibilité de réessayer ; aucun repli vers une API interne ou un autre lot n’existe.

La source publique ignore les configurations de backend local. L’activation forcée des drapeaux locaux pendant le build ne lui donne accès à aucune donnée V2. Les tests de production autorisent maintenant la présentation commune et interdisent toujours les lecteurs, versions, empreintes et contenus privés ; ils interdisent également les anciennes entrées de présentation et l’ancienne URL de backend par défaut.

## 3. Différences nécessaires entre les données

| Donnée ou fonctionnalité | Public historique | Revue locale V2 |
| --- | --- | --- |
| Secteurs | 101 | 101 |
| Pistes affichées | 165 sur 404 examens de familles | 205 propositions |
| Secteurs avec / sans piste | 71 / 30 | 88 / 13 |
| Niveaux A/B/C | Aucun ; « Piste historique · justification non qualifiée » | 93 / 45 / 67, inchangés |
| Secteur 26, Colombelles / Hérouville-Saint-Clair | Trois pistes historiques, aucun niveau | Quatre propositions, niveaux A / C / A / A reçus |
| Secteur 5, Caen | Trois pistes historiques, aucun niveau | Trois propositions, niveaux B / B / A reçus |
| Liens entre propositions | Non qualifiés par le contrat historique ; aucune indépendance supposée | Signalement reçu des observations liées |
| Exemple de la Méthode | Exemple public existant de Caen, surface ≈ 0,727383 km² | Exemple local existant du secteur 26, surface ≈ 0,862230 km² |
| Couleurs | 27 rouges, 33 oranges, 9 jaunes, 32 grises | Même répartition reçue |

Libellés communs : rouge « Secteur à examiner en priorité », orange « Priorité d’examen élevée », jaune « Priorité d’examen modérée », gris « Informations insuffisantes ». Aucune classe verte. La couleur est une indication d’examen principalement routière ; elle n’exprime aucune urgence de travaux et ne détermine aucun niveau A/B/C.

Les titres, observations, conditions et ordres des pistes peuvent différer parce que les deux contrats ne décrivent pas les mêmes propositions. Ces différences ne sont pas masquées par de faux contenus V2.

## 4. Vérifications

| Contrôle | Résultat |
| --- | --- |
| TypeScript et build de production | Réussis, drapeaux V2 et revue historique forcés à 1, source publique statique |
| Contrats de priorités et actions existants | Réussis |
| Contrat V2 et explications locales | 101 fiches et 205 présentations vérifiées, niveaux et statuts inchangés, 13 états sans proposition |
| Navigateur V2 exhaustif | 101 secteurs, 205 cartes, 15 secteurs à quatre propositions, 13 sans proposition, niveaux 93/45/67 |
| Navigateur public exhaustif | 101 secteurs, 165 pistes, 30 sans piste ; familles haies 50, milieux humides 20, friches 35, franchissements 60 |
| Fonctionnement public sans backend | Réussi ; toutes les routes `/api/` sont bloquées dans le test, aucune requête API tentée |
| Navigation | Carte, Méthode et sources, ouverture d’une fiche, chargement direct et compatibilité `/catalogue` |
| Responsive | 320, 390, 768, 1024, 1440 px ; absence de débordement horizontal ou chevauchement de l’en-tête |
| Comparaison visuelle | Secteurs 26 et 5, mêmes largeurs 320/390/768/1440 ; dimensions d’en-tête, marque, navigation, carte et panneau cohérentes |
| Méthode | Trois formules avec provenance, quatre groupes de références familiales, douze références, exemple réel, détails ouverts sur mobile |
| Carte et interactions | Une carte, recherche commune/secteur, sélection et clic réel mobile, grille utilisable sans fond OSM |
| Accessibilité | Logo décoratif sans répétition du nom, proportions conservées, navigation accessible, détails utilisables au clavier, contrastes testés |
| Erreurs et permissions | Réessai de fiche locale, réponse publique altérée refusée par empreinte, réessai public fonctionnel, aucun repli interne |
| Backend inchangé | 42 tests réussis |
| Ressources servies | 15 fichiers publics identiques à leurs originaux ; aucun ZIP, GeoPackage, lot interne ou secret dans le build |
| Protection du travail existant | 45 fichiers backend/public et 1 253 fichiers scientifiques vérifiés sans changement ; lockfile préexistant conservé |
| Git | Branche et HEAD conservés ; `git diff --check` réussi ; index non modifié |

Le premier lancement backend dans le sandbox avait 40 réussites et deux erreurs d’ouverture de sockets loopback. Le même contrôle, autorisé à ouvrir ses serveurs éphémères locaux, a terminé avec 42 réussites. Une dépréciation du client HTTP de l’environnement de test subsiste. Le build conserve l’avertissement de taille de chunk MapLibre ; aucun échec de compilation.

Les anciens tests qui exigeaient la disparition de toute présentation V2 en production ont été remplacés par des assertions sur les données et permissions. `test:browser:actions` vise maintenant la recette publique commune ; les tests métier historiques `test:actions` sont conservés.

Les 1 538 tests M2 antérieurs n’ont pas été relancés : aucun calcul ni code scientifique n’a changé, et les empreintes ont été contrôlées.

### Preuves locales

[Ouvrir le comparatif visuel local](../data/derived/recette_interface_commune_20261116/comparatif.html). Les sélecteurs permettent de comparer les mêmes secteurs et largeurs.

Les captures et reçus sont conservés hors des chemins servis et ignorés par Git dans `data/derived/recette_interface_commune_20261116/` :

- `public/validation_production.json` : parcours public exhaustif sans backend.
- `local/validation_browser.json` : parcours local exhaustif et protections.
- `comparison/comparison.json` : comparaisons de géométrie et de secteurs, altération refusée, accès Vercel observé.
- `comparison/{public,local}_sector_{1,2}_{320,390,768,1440}.png` : mêmes secteurs et mêmes largeurs.
- `comparison/{public,local}_method_*.png`, `*_formulas_*.png`, `*_references_*.png` : Méthode et détails scientifiques. Les sections sont photographiées séparément pour rester lisibles.
- `comparison/vercel_current.png` : page de connexion réellement observée.
- `protection.json`, `build_manifest.json` et `fichiers_modifies.txt` : contrôle des fichiers, empreintes du build et périmètre de revue.

## 5. Limites distantes et future V2 autorisée

La consultation GitHub en lecture seule indique que la PR #5 est déjà fusionnée, au SHA `25336e6eadbef2633f9ff08ab36f29697dcd9613`, depuis le 15 novembre à 23 h 05 min 41 s UTC (16 novembre à 00 h 05 à Paris). Cette fusion est antérieure à la présente correction et n’a pas été effectuée par cette intervention. Aucun changement distant n’a été demandé. Le rendu corrigé est exclusivement local ; Vercel continue de servir sa version déjà déployée derrière sa protection d’accès.

Pour publier ultérieurement la V2 :

1. Obtenir une autorisation de diffusion explicite liée au lot minimisé, à son périmètre et à ses empreintes, avec responsable et date. La candidature existante ne vaut pas autorisation.
2. Valider le contrat public minimisé, les champs autorisés et la traçabilité des sources. Ne pas publier le lot interne brut ni utiliser les routes internes comme API publique.
3. Ajouter un adaptateur de ce contrat autorisé et une variante de permission explicite. Le même rendu commun pourra l’utiliser ; le mode local expérimental et ses protections doivent rester distincts.
4. Actualiser l’autorisation des ressources publiques, les empreintes et les tests de sécurité après cette revue, puis vérifier à nouveau les 101 secteurs et 205 propositions publiques autorisées.
5. Faire autoriser séparément les opérations Git et le déploiement, puis effectuer une recette Vercel avec accès légitime. Aucun succès de déploiement futur n’est présumé.

Le fichier `frontend/package-lock.json` était déjà modifié avant cette demande : sa modification reste intacte et exclue du périmètre proposé. Les captures, journaux et données de `data/derived/` restent exclus. Seuls les composants, adaptateurs, tests, scripts frontend et le présent rapport constituent les corrections à examiner.

## 6. Ouvrir les deux versions pour revue

- Revue locale V2 : `http://127.0.0.1:5184/`.
- Build public statique corrigé : `http://127.0.0.1:5187/`.
- Page Méthode : `/methode` sur chacun des deux serveurs.

Ces serveurs sont locaux ; aucun site distant n’a été modifié.
