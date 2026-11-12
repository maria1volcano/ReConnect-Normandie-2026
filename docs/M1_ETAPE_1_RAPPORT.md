# M1 — Rapport de vérification de l'étape 1

Date : 3 novembre 2026

## Résultat

L'inventaire préliminaire de 17 candidats a été repris et restructuré avec des colonnes séparant catalogue, ressource, accès, limites, preuve et cycle de vie. Aucun jeu n'est déclaré téléchargé, inspecté, harmonisé ou validé. Les seuls statuts employés sont `ACCESSIBLE` lorsqu'une voie officielle de téléchargement/service est confirmée et `CANDIDAT` lorsque l'accès, la licence ou la ressource exacte reste à établir.

## Corrections principales

- Remplacement du lien INPN TVB national cassé par les couches régionales DREAL pertinentes ; la ligne nationale redondante n'est pas conservée.
- Séparation des dates de publication, versions produit et années de référence quand l'information est disponible.
- Confirmation de la Licence Ouverte 2.0 pour les réservoirs SRCE, BD TOPO, SIPAF, BD Haie, Cartofriches, zones humides DREAL et l'inventaire local de mares.
- Ajout des voies d'acquisition Géoplateforme pour BD TOPO et OCS GE sans prétendre qu'un paquet D014 a déjà été téléchargé.
- Remplacement de l'EPFN comme seule piste R3 par Cartofriches comme source nationale ouverte, tout en conservant l'EPFN comme complément candidat.
- Ajout de l'inventaire DREAL des zones humides comme source R4 ouverte ; PRAM demeure candidat soumis à demande et clarification des droits.
- Suppression des affirmations non étayées sur CRS, géométrie, format ou champs ; elles restent `A VERIFIER` jusqu'à inspection réelle.

## Vérifications acquises

- **P0 TVB** : les fiches officielles DREAL/data.gouv annoncent des ressources Shapefile/WFS pour réservoirs, corridors et cours d'eau. La ressource directe des réservoirs est identifiée. Le millésime scientifique reste 2014 malgré des republications en 2024.
- **P0 routes** : BD TOPO 3.5 est accessible via l'API de téléchargement IGN, en paquets GeoPackage notamment. L'édition trimestrielle 2026-09 est annoncée ; la classe route et ses attributs doivent être confirmés dans le paquet choisi.
- **P0 sols** : OCS GE est diffusée par l'IGN en GeoPackage et EPSG:2154 en métropole. Le millésime exact disponible pour D014 doit être obtenu via l'API lors de l'étape 2.
- **R1** : SIPAF propose CSV, GeoPackage et API JSON en accès public sous Licence Ouverte 2.0.
- **R2** : BD Haie V2 mars 2024 est nationale, linéaire et ouverte ; V1/V2 ne sont pas directement comparables.
- **R3** : Cartofriches offre un GeoPackage ouvert de 67,1 Mo mais non exhaustif et hétérogène.
- **R4** : les zones humides DREAL sont ouvertes ; les données PRAM nécessitent une demande et des droits à clarifier.

## Incertitudes et blocages pour l'étape 2

1. Licence des corridors SRCE Basse-Normandie non confirmée dans les éléments consultés.
2. CRS, schémas attributaires, validité des géométries et couverture réelle de toutes les couches restent non inspectés.
3. Paquet et millésime OCS GE D014 à sélectionner via l'API ; ne pas choisir un pilote avant cette vérification.
4. Extraction PRAM et droits de redistribution à demander au CEN Normandie.
5. Données EPFN : aucune ressource sur la fiche vérifiée et licence non spécifiée.
6. Les inventaires SIPAF, Cartofriches, mares et zones humides sont incomplets ou hétérogènes ; une absence d'objet ne constitue pas une absence sur le terrain.

## Périmètre respecté

Aucune archive SIG n'a été téléchargée. Aucun pilote, traitement, harmonisation, grille ou conclusion scientifique n'a été produit. Les liens et métadonnées ont été vérifiés sur les portails officiels et la documentation des producteurs ; leur contenu interne sera contrôlé seulement après acquisition autorisée en étape 2.
