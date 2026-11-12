# Transmission M3 — Frontend / UX

## Références Git

- Branche de travail : `feat/m3-frontend-reconnect-v61`
- Branche source : `main` au commit `d7056ef` (alignée avec `origin/main` lors de l'audit)
- Dépôt distant de référence : `origin` (`ReConnect-Normandie-2026`)
- État initial : propre, sans modification locale non commitée
- Politique : aucun commit, push, merge, rebase ou Pull Request sans autorisation explicite

## Audit initial — préparation

### Architecture détectée

Le dépôt contient une arborescence partagée initiale, mais aucune implémentation applicative :

- `analysis/` : réservé aux analyses, vide hors `.gitkeep`
- `backend/` : réservé au backend M4, vide hors `.gitkeep`
- `catalogue/` : réservé au catalogue M5, vide hors `.gitkeep`
- `data/{raw,processed,derived,public}/` : espaces de données, vides hors `.gitkeep`
- `frontend/` : espace M3, vide hors `.gitkeep`
- `tests/` : espace de tests partagé, vide hors `.gitkeep`
- `docs/` : documentation partagée

Aucun framework frontend, gestionnaire de paquets, fichier de verrouillage, script de lancement/test/build ou version d'outillage n'est défini à ce stade. Aucun frontend existant ne doit donc être remplacé. Les répertoires hors `frontend/` et ce document sont considérés comme appartenant aux autres responsabilités de l'équipe.

### Structure frontend retenue pour M3

Structure issue des sections 8 et 10.3 du PRD, à créer à l'étape 1 :

```text
frontend/
├── public/
├── src/
│   ├── app/                 # composition, routes et providers
│   ├── components/
│   │   ├── map/             # RegionMap, HexGridLayer, emprise pilote
│   │   ├── sector/          # ZoneDetail, ConflictsPanel, ActionSuggestions
│   │   ├── legend/          # PriorityLegend et états d'analyse
│   │   └── ui/              # composants accessibles réutilisables
│   ├── features/            # orchestration des parcours métier M3
│   ├── integrations/        # adaptateurs M2, M4 et M5
│   ├── hooks/               # état et interactions
│   ├── types/               # contrats TypeScript partagés côté frontend
│   ├── styles/              # tokens et styles globaux
│   └── test/                # configuration et utilitaires de tests
└── package.json             # React + TypeScript + Vite + MapLibre GL JS
```

Principe d'intégration : les données externes seront consommées via des adaptateurs typés afin de ne pas embarquer dans M3 les calculs SIG M2, les règles scientifiques R1–R4, le backend M4 ou le contenu éditorial M5.

### Direction UX retenue

- Problème : rendre un prédiagnostic territorial immédiatement compréhensible par un élu, tout en laissant un technicien vérifier provenance, qualité, dates, méthode et limites.
- Direction visuelle : système Organic, avec surfaces sable/avoine, palette sauge-mousse-terre cuite, typographie humaniste, angles de 16 à 32 px et mouvement doux.
- Interaction distinctive : la fiche secteur se déploie depuis la sélection cartographique sans masquer la localisation de la maille.
- Discipline de contenu : les fixtures portent en permanence la mention « Données de démonstration — TEST » et ne sont jamais présentées comme un résultat scientifique réel.

### Contraintes scientifiques d'affichage

- La carte affiche `priorite_examen` comme priorité de vérification préparatoire, jamais comme obligation d'investissement, rendement ou score écologique.
- `indeterminee`, `analyse_non_realisee`, `aucun_signal` et `donnees_insuffisantes` restent visuellement et textuellement distincts ; une valeur absente n'est jamais convertie en zéro.
- La couleur n'est jamais le seul canal : chaque priorité possède un libellé textuel et des explications consultables.
- Une maille peut cumuler plusieurs diagnostics, pressions, conflits et actions ; les étiquettes ne sont pas exclusives.
- Les événements de conflit restent distincts des mailles. La coprésence dans une maille n'est jamais présentée comme un croisement confirmé.
- Les niveaux autorisés sont « Croisement cartographique détecté », « Conflit potentiel à vérifier », « Obstacle documenté » et « Données insuffisantes pour conclure ».
- Les actions sont présentées sans classement d'efficacité, selon `etayee_pour_examen`, `conditionnelle`, `non_retenue_par_regle` ou `non_evaluable`.
- Hors pilote, la navigation régionale reste possible mais affiche clairement « Analyse non réalisée ».
- Aucune géométrie sensible, donnée naturaliste ponctuelle sensible, clé ou donnée interdite de diffusion n'est chargée côté client.

## Suivi par étape

### Préparation — audit et branche

Fonctionnalités réalisées :

- audit Git et structurel unique du dépôt ;
- création de la branche locale M3 ;
- proposition d'une architecture frontend sans initialisation ni dépendance ;
- lecture ciblée du PRD V6.1, sections 7, 8, 10.3 et annexe B3 ;
- verrouillage des états UX, contrats M2/M4/M5 et garde-fous scientifiques M3.

Fichiers créés :

- `docs/M3_HANDOFF.md`

Fichiers modifiés : aucun fichier existant.

Le PRD Markdown fourni par l'utilisateur est non suivi par Git et n'a pas été modifié par M3.

### Étape 1 — structure visuelle et carte principale

Fonctionnalités réalisées :

- initialisation React + TypeScript + Vite dans `frontend/` ;
- `ApplicationLayout` responsive avec identité ReConnect Normandie et emplacements non interactifs Catalogue / Méthode ;
- `RegionMap` MapLibre centré sur la Normandie, zoom, attribution, état de chargement et repli explicite si le fond OpenStreetMap est indisponible ;
- emplacements sans données pour la future limite du pilote et les futures mailles M2 ;
- `PriorityLegend` distinguant élevée, modérée, faible, indéterminée et zone non analysée par couleur, motif et texte ;
- `ZoneDetail` dans un panneau latéral desktop et une section adaptée au mobile, avec l'état initial « Sélectionnez un secteur » ;
- zone discrète « Sources et limites », navigation clavier et respect de `prefers-reduced-motion` ;
- chargement dynamique de MapLibre afin de réduire le bundle JavaScript initial ;
- aucun score, calcul scientifique ou donnée écologique fictive ajouté.

Correction après validation visuelle : MapLibre 6 ne trouvait pas son worker ESM dans la configuration Vite et émettait `Worker failed to load`. `RegionMap` fournit désormais explicitement `maplibre-gl-worker.mjs?worker&url` via `setWorkerUrl`. Le fond OpenStreetMap ne nécessite aucune clé API ; une tuile représentative et les tuiles du viewport ont répondu HTTP 200. Une erreur MapLibre générique n'est plus traitée immédiatement comme une panne globale : le repli reste déclenché si aucun premier rendu complet n'est obtenu sous dix secondes.

Fichiers créés :

- `frontend/.gitignore`
- `frontend/index.html`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/tsconfig.json`
- `frontend/vite.config.ts`
- `frontend/src/vite-env.d.ts`
- `frontend/src/main.tsx`
- `frontend/src/app/App.tsx`
- `frontend/src/components/layout/ApplicationLayout.tsx`
- `frontend/src/components/map/RegionMap.tsx`
- `frontend/src/components/legend/PriorityLegend.tsx`
- `frontend/src/components/sector/ZoneDetail.tsx`
- `frontend/src/styles/global.css`
- `docs/screenshots/M3_step1.png`

Fichier modifié : `docs/M3_HANDOFF.md`.

### Étape 3 — Fiche de diagnostic écologique

### Résumé

Implémentation complète du panneau de diagnostic écologique pour les mailles hexagonales sélectionnées. La fiche affiche :

- En-tête avec identifiant de maille, badge TEST si applicable, et statut d'analyse
- Section priorité d'examen avec indicateur coloré et explication
- Section "Pourquoi ce secteur est-il signalé ?" avec enjeux écologiques, pressions humaines et conflits potentiels
- Indicateurs environnementaux (accordéon technique)
- Qualité et fiabilité des données avec niveau, couverture, échelle et années
- Sources et limites (accordéon technique) avec références de sources
- Note explicative pour les données TEST

### Architecture des données

**Types étendus (`frontend/src/types/hexagon.ts`) :**
- `DiagnosticDetail` : structure complète du diagnostic
- `SourceReference` : métadonnées des sources de données

**Adaptateur de données (`frontend/src/integrations/geojsonAdapter.ts`) :**
- `loadZoneDiagnostic(maille_id, isTestMode)` : charge les diagnostics depuis fichier TEST ou API M4
- En mode TEST : lit depuis `diagnostics-test.json`
- En mode normal : prêt pour intégration API M4

**Fixture TEST (`frontend/public/data/diagnostics-test.json`) :**
- Quatre diagnostics complets pour TEST-HEX-001 à TEST-HEX-004
- Chaque diagnostic contient priorité, explication, enjeux, pressions, conflits, indicateurs, qualité et sources
- Toutes les valeurs marquées `test_data: true`

### États supportés

- **Calculée** : Diagnostic complet avec priorité et indicateurs
- **Données insuffisantes** : Priorité indéterminée, indicateurs non disponibles
- **Analyse non réalisée** : Aucun diagnostic disponible
- **Chargement** : État de chargement affiché
- **Erreur** : Message d'erreur si échec du chargement
- **Disponible** : Pour hexagons sans diagnostic en mode TEST

### Progression de l'information

**Pour un élu :**
- Priorité et explication courte
- Principales pressions
- Fiabilité des données
- Avertissements importants

**Pour un technicien :**
- Indicateurs détaillés (accordéon)
- Références de sources (accordéon)
- Années des données
- Version de méthode
- Limitations scientifiques

### Comportement interactif

- Sélection d'une maille → chargement automatique du diagnostic
- Changement de maille → mise à jour sans rechargement de carte
- Désactivation mode TEST → effacement diagnostic TEST, retour panel normal
- Sélection département → affichage DepartmentPanel (préséance hexagon > département)
- Indicateurs et sources dans accordéons pour éviter surcharge visuelle

### Dépendances M2/M4

**Données TEST actuelles :**
- Diagnostics stockés dans `diagnostics-test.json`
- Priorités, enjeux, pressions et indicateurs fictifs
- Sources fictives avec identifiants TEST

**Attente pour intégration réelle :**
- Diagnostics M2 avec priorités validées
- Indicateurs quantitatifs réels
- Références de sources authentiques (IGN, SIPAF, BD Haie, etc.)
- Méthode version M2
- Intégration API M4 `GET /zones/{maille_id}`

### Fichiers créés/modifiés

**Nouveau :**
- `frontend/public/data/diagnostics-test.json` : fixture diagnostics TEST

**Modifiés :**
- `frontend/src/types/hexagon.ts` : types DiagnosticDetail, SourceReference
- `frontend/src/integrations/geojsonAdapter.ts` : fonction loadZoneDiagnostic
- `frontend/src/components/sector/ZoneDetail.tsx` : réécriture complète
- `frontend/src/components/layout/ApplicationLayout.tsx` : passage testModeEnabled
- `frontend/src/styles/global.css` : styles panel diagnostic
- `docs/M3_HANDOFF.md` : documentation Étapes 2 et 3

### Limitations connues

- Les hexagons TEST présentent un chevauchement visuel dans certaines vues (défaut Step 2 non résolu)
- Pas de calculs écologiques réels en frontend
- Pas de recommandations d'actions complètes (Step 4)
- Sources TEST fictives, pas de métadonnées réelles

### Étape 4 — Conflits potentiels et pistes d'actions

Fonctionnalités réalisées :

- `ConflictsPanel` affiche zéro, un ou plusieurs conflits potentiels avec niveau d'évidence, méthode de détection, sources et limites ; les états chargement, erreur, données manquantes et analyse non réalisée sont prévus ;
- `ActionSuggestions` affiche les familles R1–R4 fournies par les données, leurs conflits liés, conditions de vérification, sources, limites et statut de pertinence, sans exécuter de règle scientifique dans le frontend ;
- intégration dans `ZoneDetail` selon le parcours priorité → explication → conflits → actions → indicateurs → qualité/sources ;
- annulation des chargements devenus obsolètes lors d'un changement rapide de maille ou de mode ;
- fixture séparée `conflicts-actions-test.json`, marquée `test_data: true`, couvrant plusieurs conflits/actions, un cas unitaire, un état « aucun documenté » et un état non évaluable ;
- accordéons clavier natifs, statuts textuels et cartes compactes compatibles avec le panneau liquid-glass défilable.

Dépendances restantes :

- **M2** : livrer et valider `conflits.geojson`, les qualifications scientifiques, les règles R1–R4 et les formulations/limites définitives ;
- **M4** : confirmer le contrat API/export, implémenter le moteur R1–R4 et exposer zones, conflits, actions et erreurs structurées ;
- **M5** : livrer `catalogue_actions.json` et le module des douze fiches ; ce catalogue n'est pas recréé dans Step 4.

Les contenus TEST démontrent uniquement les états UX. Ils ne constituent ni des observations officielles, ni des impacts confirmés, ni des recommandations de travaux.

Fonctionnalités réalisées :

- types TypeScript pour les données hexagonales et la zone pilote (`PriorityExamen`, `StatutAnalyse`, `EvidenceLevel`, `ActionStatut`, `HexagonFeatureProperties`, `PilotBoundaryProperties`) ;
- adaptateur GeoJSON (`geojsonAdapter.ts`) pour charger `mailles.geojson` et `pilot-boundary.geojson` avec gestion gracieuse des erreurs et données manquantes ;
- composant `HexGridLayer` MapLibre intégrant la grille hexagonale avec hover, sélection et états visuels basés sur `priorite_examen` ;
- couche de limite pilote dans `RegionMap` avec style distinct (hachures marron) et affichage explicite de l'état de validation ;
- intégration de la sélection hexagonale dans `ApplicationLayout` avec précédence sur la sélection départementale ;
- fixtures TEST clairement étiquetées (`test_data: true`) pour la zone pilote et les mailles de diagnostic ;
- conservation complète des interactions départementales existantes (hover, clic, zoom, retour) ;
- message explicite « DONNÉES TEST — NON VALIDÉES » affiché pour les données de test.

Architecture de sélection :

1. Hexagone sélectionné → `ZoneDetail` (fiche maille) ;
2. Sinon département sélectionné → `DepartmentPanel` ;
3. Sinon → vue régionale / `ZoneDetail` par défaut.

Couche pilote :

- Style distinct des limites administratives (couleur marron #8B7355, hachures) ;
- État visible dans l'interface : « Zone pilote en attente de validation » ou « DONNÉES TEST — NON VALIDÉES » ;
- Prêt à recevoir des données validées de M1/M2 sans modification du code.

Couche hexagonale :

- Couleurs de priorité correspondant à `PriorityLegend` (élevée, modérée, faible, indéterminée) ;
- `feature-state` pour hover/selection sans mutation des données ;
- Nettoyage approprié des sources, couches et event handlers ;
- Compatible avec l'instance MapLibre existante (pas de rechargement).

Données utilisées :

- `public/data/pilot-boundary.geojson` : fixture TEST avec 4 mailles près de l'estuaire de l'Orne ;
- `public/data/mailles.geojson` : fixture TEST avec 4 hexagones illustrant les 4 niveaux de priorité PRD.

Pas de données réelles : les exports M1/M4 ne sont pas encore disponibles. L'interface affiche explicitement l'état d'attente.

Fichiers créés :

- `frontend/src/types/hexagon.ts` : définitions de types PRD V6.1
- `frontend/src/integrations/geojsonAdapter.ts` : adaptateur de chargement GeoJSON
- `frontend/src/components/map/HexGridLayer.tsx` : couche hexagonale MapLibre
- `frontend/public/data/pilot-boundary.geojson` : fixture TEST pilote
- `frontend/public/data/mailles.geojson` : fixture TEST mailles

Fichiers modifiés :

- `frontend/src/components/map/RegionMap.tsx` : ajout couche pilote, ref mapRef partagé, mode TEST toggle, labels TEST
- `frontend/src/components/layout/ApplicationLayout.tsx` : intégration état hexagon, HexGridLayer, gestion mode TEST
- `frontend/src/components/sector/ZoneDetail.tsx` : implémentation fiche diagnostic complète
- `frontend/src/components/map/HexGridLayer.tsx` : couleurs hexagones améliorées, labels, visibilité mode TEST
- `frontend/src/styles/global.css` : styles badges, toggle TEST, labels hexagons, panel diagnostic
- `frontend/src/types/hexagon.ts` : types étendus pour DiagnosticDetail, SourceReference
- `frontend/src/integrations/geojsonAdapter.ts` : ajout loadZoneDiagnostic pour TEST
- `docs/M3_HANDOFF.md` : documentation Étapes 2 et 3

Tests et validations :

- `npm run typecheck` : réussi (TypeScript 7.0.2)
- `npm run build` : réussi (Vite 8.3.5)
- Serveur de développement : démarré sur `http://127.0.0.1:5174/` (5173 occupé)
- Interactions départementales préservées : hover, clic, zoom, retour fonctionnels
- Couche pilote visible avec message explicite
- Couche hexagonale chargée avec colors par priorité
- Sélection hexagon prend précédence sur département
- Aucun crash si GeoJSON manquant

Dépendances M1/M2/M4 pour la suite :

- M1 : grille hexagonale stable avec `maille_id` en Lambert-93, exportée en WGS84
- M2 : `mailles.geojson` avec `priorite_examen`, `statut_analyse`, diagnostics réels
- M4 : API endpoints ou confirmation que l'approche GeoJSON statique est suffisante

## Commandes du projet

Depuis `migration-reconnect/frontend/` :

```powershell
npm.cmd install
npm.cmd run dev -- --host 127.0.0.1 --port 5173
npm.cmd run typecheck
npm.cmd run build
npm.cmd run preview
```

URL de développement : `http://127.0.0.1:5173/`.

## Dépendances

- `react@19.3.1` et `react-dom@19.3.1` : interface composable M3 ;
- `maplibre-gl@6.16.0` : carte WebGL demandée par le PRD ;
- `vite@8.3.5` et `@vitejs/plugin-react@6.1.2` : serveur et build léger ;
- `typescript@7.0.2`, `@types/react@19.3.0` et `@types/react-dom@19.3.0` : contrats frontend stricts.

Les versions exactes sont verrouillées dans `package-lock.json`. Aucune bibliothèque de composants ou de gestion d'état n'a été ajoutée.

## Interfaces attendues

Contrats de référence extraits du PRD, à valider avec l'équipe au jalon prévu :

- M2 — `mailles.geojson` : FeatureCollection RFC 7946 en WGS84/CRS84 avec `maille_id`, `grid_version`, `statut_analyse`, `priorite_examen`, `diagnostics[]`, `indicateurs`, `qualite`, `conflit_ids[]`, `action_ids[]` et `method_version` ;
- M2 — `conflits.geojson` : `conflit_id`, `type`, `evidence_level`, `source_ids[]`, `maille_ids[]`, `precision_affichage`, `limites[]` et géométrie généralisée ou omise si nécessaire ;
- M2 — `fiches_zones.json` : diagnostics, indicateurs, périodes, fiabilité et associations d'actions ;
- M4 — routes attendues : `GET /health`, `/zones?bbox=...`, `/zones/{maille_id}`, `/conflits?maille_id=...`, `/actions`, `/actions/{action_id}` et `/sources`, avec erreurs JSON 404/422 ;
- M5 — `catalogue_actions.json` et futur module React autonome Catalogue / Méthode ; les mêmes `action_id` doivent relier le catalogue aux résultats M2.

M3 affichera et orchestrera ces données sans recalculer leur logique métier ou scientifique.

Les adaptateurs frontend accepteront d'abord des fichiers statiques TEST, puis l'API M4 sans modifier les composants de présentation. Les fixtures devront contenir `test_data: true`; ce marqueur sera interdit dans toute donnée présentée comme réelle.

## Difficultés et limitations connues

- Le PRD V6.1 est disponible en Markdown et sert désormais de référence principale M3.
- La stack fonctionnelle est définie par le PRD : React + MapLibre. Les versions compatibles de React, TypeScript, Vite et MapLibre GL JS seront verrouillées à l'initialisation de l'étape 1.
- Aucun jeu de données, endpoint ou module M5 n'est disponible localement à ce stade.
- Le dossier parent du dépôt a une configuration Git non exploitable ; toutes les commandes doivent être exécutées depuis `migration-reconnect/`.
- Le fond OpenStreetMap nécessite un accès réseau et reste un service sans garantie de disponibilité ; l'état de repli est conservé. Aucun contour local n'est inventé en remplacement.
- Le chunk MapLibre représente environ 1 104 Ko minifiés (298 Ko gzip), son worker environ 519 Ko, et le JavaScript initial environ 227 Ko minifiés (71 Ko gzip). Ils sont séparés et l'ensemble reste sous le budget interne de 3 Mo hors tuiles.

## Intégration et fusion

Les instructions détaillées de fusion seront rédigées pendant la finalisation. Avant toute intégration, l'équipe devra vérifier la branche active, examiner les changements M3 et confirmer les contrats de données. Aucun push ni fusion n'est autorisé sans validation explicite.

Zones de conflits Git possibles :

- futurs fichiers racine de gestion des dépendances et de configuration ;
- `README.md` si plusieurs membres documentent les commandes globales ;
- `docs/` si la documentation d'intégration est centralisée ;
- contrats partagés si l'équipe les place hors de `frontend/src/types/`.

## Procédure d'annulation

La seule modification M3 de cette préparation est ce nouveau fichier non commité. Après accord explicite et vérification de son chemin, elle peut être annulée en supprimant uniquement `docs/M3_HANDOFF.md`. Le PRD fourni ne doit pas être supprimé. La branche locale ne doit pas être supprimée automatiquement. Aucun `reset --hard` ni opération destructive globale ne doit être utilisé.

## Tests et validations

- `git status` initial : propre sur `main`.
- Branche active après préparation : `feat/m3-frontend-reconnect-v61`.
- PRD ciblé relu : sections 7, 8, 10.3 et annexe B3, avec contrôle des contraintes scientifiques des sections 3 à 6.
- `npm.cmd run typecheck` : réussi avec TypeScript 7.0.2.
- `npm.cmd run build` : réussi avec Vite 8.3.5.
- Serveur de développement : réponse HTTP 200 sur `http://127.0.0.1:5173/`.
- Vérification visuelle desktop 1440 × 1000 : fond OpenStreetMap réel rendu sur la Normandie, structure, lisibilité, légende et panneau contrôlés ; capture dans `docs/screenshots/M3_step1.png`.
- Vérification réseau navigateur : tuiles initiales et tuiles après zoom HTTP 200, aucune erreur console.
- Vérification du contrôle `+` : nouvelles tuiles demandées au niveau de zoom supérieur (8 → 9).
- Avertissement de build : chunk MapLibre supérieur à 500 Ko minifié, isolé par chargement dynamique et mesuré ci-dessus.
