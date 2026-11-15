# Préparation de publication — aucune autorisation accordée

15 novembre 2026. Le code peut être proposé à la revue. **Le parcours V2 à 205 propositions n’est pas prêt à être déployé publiquement.** Il reste explicitement local et interne.

## Trois états distincts

| État | Données et comportement |
| --- | --- |
| Revue locale protégée, 5184/8768 | 101 mailles, 205 propositions, niveaux A/B/C, quatre familles, recherche, carte et méthode complète. Activation explicite, développement et boucle locale seulement. |
| Build de production actuel | Export historiquement autorisé : 101 fiches, 404 examens de familles dont 165 pistes à étudier. Pas d’API sur le Mac, pas de données V2, pas de catégorie A/B/C V2 reconstituée. La différence est visible dans l’interface. |
| Candidature V2 préparée | 101 mailles et 205 propositions minimisées, hors des chemins servis, avec contrôles d’empreintes. Aucune publication ou activation publique possible par le préparateur. |

Les 165 pistes historiques ne sont pas les 205 propositions V2. Les 404 examens ne sont pas 404 solutions proposées. Cette différence est contrôlée dans le test du build produit, avec toutes les requêtes API bloquées.

## Candidature réellement produite

Répertoire interne : `data/derived/v2_public_candidate_mvp_20261115_01/`, ignoré par Git et non copié dans le build.

Fichiers : `grid.geojson`, `cells.json`, `metadata.json`, `methodology.json` et `candidate-manifest.json`. Ils conservent les champs nécessaires à la présentation et aux contrôles, sans géométries d’objets sources, listes de preuves, identifiants d’objets ou chemins privés. Les comptes exhaustifs bruts et les données historiques exactes restent dans les lots d’origine.

Le manifeste contient :

- `candidate_version = reconnect.public-candidate.multiactions-1` ;
- `publication_authorized = false` ;
- `approved_by = null`, `approved_at = null` ;
- les versions des données, des propositions et de la politique territoriale ;
- les empreintes du lot V2 source et de l’archive canonique ;
- les empreintes des quatre fichiers produits ;
- les comptes totaux et par famille, vérifiés contre 101/205/88/61/13 et 93/45/67.

Empreinte SHA-256 du manifeste candidat produit :
`bf9fbaa28df6b2493b70deb965a7c21c287b7be18164685aad6773452595b8d7`.

Une empreinte assure la vérification des octets ; elle n’est pas une autorisation, une signature d’un décideur ou une validation scientifique.

## Préparateur et garde-fous

`backend/prepare_v2_public_candidate.py` utilise les lecteurs scellés existants. Il n’exécute ni SIG, ni nouveau score, ni modification de M2. Il refuse :

- une destination dans le frontend ou le backend ;
- une destination extérieure à `data/derived` ;
- un chemin symbolique qui aboutit dans un répertoire servi ;
- un dossier existant, pour ne pas écraser une candidature ;
- une distribution incompatible ou la détection de champs sources privés.

Il n’accepte aucune option d’approbation ou de publication. Il ne peut pas réutiliser l’autorisation de l’ancien export. Les marqueurs scientifiques et de diffusion des réponses sources sont conservés. Le nouveau script n’est importé par aucun serveur et aucun endpoint ne sert ses fichiers.

Reproduction interne, dans un **nouveau dossier** :

```sh
RECONNECT_M2_V2_ROOT=../Datathon-normandie-2026/data/derived/m2_multiactions_experimental_v2_20261112_01/lot_experimental_v2 \
RECONNECT_M2_ZIP=../Datathon-normandie-2026/data/derived/caen_et_nord_actions_20261112_01/RECONNECT_CAEN_ET_NORD_ACTIONS_ETUDE_20261112_V1.zip \
"$QA_PYTHON" -B backend/prepare_v2_public_candidate.py --output data/derived/v2_public_candidate_revue_suivante
```

Le mécanisme existant `backend/export_public_release.py` et son autorisation historique restent inchangés. Ils ne constituent pas un exporteur approuvé de V2. Leurs tests refusant la diffusion du complément non autorisé ont été rejoués.

## Vérification du build public

`test:production-safety` vérifie les 15 ressources publiques byte pour byte, l’absence de lots ZIP/GeoPackage/bases/clefs et l’absence des versions, de l’exemple et des composants V2 dans le bundle. La recette navigateur utilise réellement le build, visite carte/méthode/catalogue et une fiche, et bloque les API : aucune dépendance au backend local n’est observée.

Les vues historiques techniques sont aussi désactivées en production, même lorsque `VITE_HISTORICAL_REVIEW=1` est fourni au build. Le parcours public ordinaire ne montre ni sélecteur de modes ni identifiants longs ou JSON brut.

La configuration Vercel existante est conservée : Vite, `npm ci`, `npm run build`, `dist`, données statiques et réécritures des pages Méthode/Catalogue. Un push de code sur une branche reliée au projet peut déclencher une prévisualisation automatique ; il n’a pas été utilisé comme moyen de test et aucun déploiement n’a été lancé.

## Ce qui est encore nécessaire pour diffuser les 205 propositions

1. Revoir la candidature exacte, sa minimisation, les droits des sources et ses usages de diffusion.
2. Obtenir une autorisation explicite liée à l’empreinte candidate, aux fichiers, au périmètre et aux versions. Ne pas modifier artificiellement les marqueurs des lots scientifiques.
3. Valider un contrat de distribution statique et son lecteur de production. Les protections actuelles du lecteur local et l’exclusion du bundle sont intentionnelles ; copier seulement les JSON dans `public` ne doit pas les contourner.
4. Réaliser une étape distincte et autorisée de raccordement de cet export approuvé : le préparateur livré ne publie pas et ne prétend pas que le contrat public V2 est déjà accepté.
5. Refaire les contrôles d’empreintes, comptes, parcours sans backend, accessibilité et absence de données sources avant l’autorisation de déploiement.

L’autorisation des données, l’acceptation du contrat public et le contrôle de la prévisualisation Vercel restent des conditions de publication. Il serait trompeur de déclarer que le build actuel diffusera les 205 propositions ou de dire qu’un push de code suffit à reproduire le parcours local en production.
