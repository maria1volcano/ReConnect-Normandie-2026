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

## Commandes du projet

À ce stade, aucune commande d'installation, de lancement, de test ou de build n'existe, car aucun projet frontend ni `package.json` n'est présent. Les commandes exactes seront ajoutées après validation et initialisation de la stack à l'étape 1.

## Dépendances

Aucune dépendance ajoutée pendant la préparation.

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
- Tests applicatifs : non disponibles (aucune application ni configuration de test).
- Build de production : non disponible (aucune application ni script de build).
