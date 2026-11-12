# Plan d'acquisition M1 — étape 1

Date de vérification : 3 novembre 2026. Ce plan prépare l'étape 2 sans choisir le pilote, télécharger d'archive lourde ni conclure sur la qualité interne des fichiers.

## Ordre d'acquisition P0

1. **TVB/SRCE DREAL Normandie**
   - Récupérer d'abord les réservoirs, corridors Basse-Normandie et cours d'eau depuis leurs fiches data.gouv/DREAL indiquées dans `inventaire_sources.csv`.
   - Méthode : télécharger les archives publiées et conserver les fichiers bruts intacts avec URL finale, date, taille et empreinte SHA-256. Conserver aussi le GetCapabilities WFS comme preuve secondaire.
   - Attendu : Shapefile, couverture Normandie ou Basse-Normandie. CRS, géométries, sous-trames, identifiants et échelle restent à inspecter.
   - Blocage : licence des corridors Basse-Normandie à confirmer avant toute redistribution.

2. **BD TOPO 3.5 — routes**
   - Interroger `https://data.geopf.fr/telechargement/resource/BDTOPO?zone=D014&format=GPKG&page=1&limit=50`, puis choisir le dernier paquet trimestriel départemental D014 ou le paquet « thème transport » approprié.
   - Préférer GeoPackage Lambert-93 et l'édition trimestrielle à BD TOPO Express pour ses contrôles supplémentaires.
   - Extraire ultérieurement `troncon_de_route` et les classes d'ouvrages utiles. Relever le millésime exact, la taille et les champs disponibles avant de figer le mapping M1→M2.

3. **OCS GE**
   - Interroger l'API Géoplateforme avec le filtre D014 : `https://data.geopf.fr/telechargement/capabilities?lang=fre&zone=D014&format=GPKG&page=1&limit=50`.
   - Sélectionner un GeoPackage EPSG:2154 et noter le millésime exact. Ne pas supposer que l'annonce nationale de deux millésimes garantit le millésime souhaité dans le Calvados.
   - Inspecter en Step 2 les nomenclatures couverture/usage, les doublons éventuels de bordure et les métadonnées du paquet.
   - Utiliser CORINE Land Cover uniquement si OCS GE est réellement indisponible, en documentant la baisse de résolution.

## Sources R1–R4

- **R1 — SIPAF** : récupérer le GeoPackage direct `https://passagesfaune.fr/geonature/api/media/exports/schedules/Tous_les_PAF.gpkg` ou l'API `https://passagesfaune.fr/geonature/api/exports/api/2`. Licence Ouverte 2.0. Ne pas interpréter l'absence d'un ouvrage comme une absence réelle ; respecter le floutage taxonomique.
- **R2 — BD Haie V2 2024** : utiliser la fiche officielle `https://www.data.gouv.fr/datasets/bd-haie`, identifier l'export départemental ou la couche WFS pertinente et préférer EPSG:2154. Ne pas comparer directement V1 et V2, produites selon des méthodes différentes.
- **R3 — Cartofriches** : télécharger en priorité `friches-surfaces.gpkg` depuis `https://www.data.gouv.fr/datasets/sites-references-dans-cartofriches`. Licence Ouverte 2.0, 67,1 Mo annoncés. Filtrer la Normandie seulement après inspection. Compléter par l'EPFN uniquement après confirmation écrite de la licence et du mode d'accès.
- **R4 — zones humides/mares** : récupérer l'inventaire DREAL `https://www.data.gouv.fr/datasets/zones-humides-normandie`; demander au CEN Normandie les droits et une extraction PRAM adaptée au futur pilote. L'inventaire local du Parc Normandie-Maine peut servir de repli dans son emprise, mais il date de 2003–2013.

## Procédure pratique pour le premier échantillon réel (Step 2)

1. Créer un registre d'acquisition : `source_id`, URL finale, horodatage, taille, SHA-256, licence, paquet/millésime et nom du fichier brut.
2. Télécharger uniquement un département ou un extrait raisonnable de chaque P0, sans écraser les archives sources.
3. Décompresser dans un espace brut séparé ; ne pas modifier les fichiers reçus.
4. Lire métadonnées, couches, CRS, emprise, schéma, nombres d'objets et géométries sans encore harmoniser.
5. Confirmer avec M2 les champs requis et comparer la couverture des candidats avant toute décision de pilote.
6. Signaler immédiatement une licence absente, une archive inaccessible ou une couverture insuffisante. Ne jamais remplacer une valeur inconnue par zéro.
