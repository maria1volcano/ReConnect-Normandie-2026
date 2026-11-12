# Audit des 32 mailles grises et triage documentaire V2 — 12 novembre 2026

La proposition V2 conserve les 101 mailles et toutes les décisions scientifiques : **27 rouges, 33 orange, 41 jaunes, zéro gris documentaire**, contre 27/33/9/32 initialement. **Les 101 priorités écologiques restent indéterminées.** La disparition du gris exploratoire décrit une présence cartographique mieux documentée, pas une qualification écologique acquise.

Le nouveau lot est `data/derived/caen_et_nord_triage_20261112_01/RECONNECT_CAEN_ET_NORD_TRIAGE_DOCUMENTAIRE_V2_20261112.zip`, avec `.zip.sha256` et `validation_extraction_v2.json`. Il reste interne et ne remplace pas V1. Le README, les règles versionnées et les vérificateurs sont intégrés au ZIP.

## Diagnostic initial et comparaison

Les 32 anciennes V4 n'ont aucune paire linéaire route–matrice retenue et aucune surface positive SRCE de matrice/réservoir dans leur propre emprise. V1–V3 ne mobilisaient donc aucun signal suffisant. Pourtant **12 ont déjà des haies**, deux de ces 12 des objets de l'inventaire ZH, et 11 ont des sites Cartofriches. Trente contiennent des routes ; deux n'en ont aucune observation. Vingt ne comportent aucun objet haie/eau/ZH dans les sources initiales : cela ne démontre aucune absence écologique. **25 des 32 sont partielles**. Les données et géométries proviennent des six communes réellement acquises ; l'exhaustivité des haies sur Caen n'est pas supposée.

Les motifs V4 exacts, catégories/attributs/longueurs routières, haies, eau, SRCE, ZH, friches, couverture, voisins, distances, précision et données nécessaires figurent dans `rapports/audit_grises_32.csv` et `.json`. La comparaison des 101, les objets justificatifs et limites sont dans `comparaison_101.csv` et `.json`. Aucune observation attestant une absence n'a été créée.

| Initiale → proposée | Rouge | Orange | Jaune | Gris |
| --- | ---: | ---: | ---: | ---: |
| Rouge (27) | 27 | 0 | 0 | 0 |
| Orange (33) | 0 | 33 | 0 | 0 |
| Jaune (9) | 0 | 0 | 9 | 0 |
| Gris (32) | 0 | 0 | 32 | 0 |

## Sources nouvelles et mesures

Deux livraisons officielles IGN ont été récupérées : **OCS GE 2023** et **OCS GE Artificialisation 2023**, département 014, EPSG:2154, Licence Ouverte 2.0. Chaque archive a la taille annoncée et le MD5 officiel : respectivement 138 290 682 et 122 971 095 octets. SHA-256 et provenance dans `provenance/ocsge_sources.json`. Le catalogue officiel distingue les couches complètes des différentiels ; le millésime choisi est 2023, pas la date de publication 2025 ou de téléchargement 2026.

Pour chaque produit : 38 369 objets lus dans la BBOX, **19 231 retenus** sur le territoire, identifiants uniques, **aucune géométrie invalide** dans la sélection source et aucune réparation. Les deux produits décrivent les mêmes objets ; leurs comptes ne sont pas additionnés. Toute l'emprise est couverte ; les résidus locaux sont ≤ 7,79e-8 m², inférieurs au budget M2 préexistant de 1e-6 m². Les codes et usages sont vérifiés avec la nomenclature CSV de la livraison. Cette couverture géométrique n'atteste aucune complétude écologique.

Les **101 mailles** ont de nouvelles observations de polygones végétalisés/aquatiques ; **les 32 anciennes grises ont chacune une couverture végétalisée OCS GE positive**. Sont fournis : surfaces en m² par code CS et US, classes arborées/arbustives/herbacées/aquatiques et statuts officiels artif/non artif. Aucune surface humide n'est déduite de l'OCS GE ; ce champ reste NULL. Les surfaces végétalisées désignent des polygones de classe dominante, pas une mesure de couvert végétal pur. Elles comprennent cultures et espaces d'ornement ; sept cas nouveaux sont exclusivement herbacés parmi les classes végétales. Végétalisé et artificialisé peuvent se recouper et ne doivent pas être additionnés.

Références primaires : [métadonnées IGN OCS GE](https://www.data.gouv.fr/datasets/ocs-ge), [métadonnées IGN Artificialisation](https://www.data.gouv.fr/datasets/ocs-ge-artificialisation), [API de téléchargement IGN](https://cartes.gouv.fr/aide/fr/guides-utilisateur/utiliser-les-services-de-la-geoplateforme/telechargement/). Les descriptifs officiels et la nomenclature sont conservés dans le lot ; leurs concepts décrivent le sol et ses usages, sans attestation de fonctionnalité.

## Évolution proposée, portée scientifique et voisinage

**V1/V2/V3 sont conservées. V3b est réservée aux anciennes V4**, sans incertitude technique critique, avec présence locale valide de haie IGN, plan d'eau IGN ou polygone OCS GE végétalisé/aquatique. Les classes CS et les conditions exactes sont dans `METHODE_TRIAGE_V2.md` et `provenance/table_triage_exploratoire_v2.json`. Routes, artificialisation, sols nus, friches seules, objets ZH ambigus et voisins seuls ne déclenchent pas V3b. Les constantes numériques M2 existantes excluent seulement les résidus ; aucun seuil écologique, de densité, de nombre d'objets ou cible de couleurs n'a été introduit.

Cette extension est défendable **au niveau documentaire uniquement**, avec une légende jaune élargie « éléments cartographiés à documenter ». Elle ne valide ni habitat naturel, ni continuité fonctionnelle, ni valeur écologique, ni urgence. Les 32 changements sont soutenus par **1 708 justificatifs locaux** recalculés contre les géométries fournies. Les données ne permettent toujours pas de calculer une priorité D/S.

Les six voisines du lattice M1 sont recherchées pour les 32, sans tampon choisi. Les objets partagés et uniquement voisins sont séparés ; les distances sont mesurées parmi les objets acquis découpés au territoire, avec leurs précisions ou NULL. Une présence uniquement voisine n'est jamais reportée dans la maille. Un minimum nul peut être un simple contact de frontière. Une continuité de dessin cartographique n'établit pas une continuité fonctionnelle. L'OCS GE a une précision globale décrite comme métrique, sans chiffre inventé par objet ; les haies portent 3 m, les autres inconnues restent NULL.

## Détail des 32 changements

Tous passent de V4/gris à V3b/jaune par présence locale OCS GE végétalisée. Les 12 haies préexistantes contribuent aussi lorsque présentes. Colonnes de surfaces/longueurs ci-dessous arrondies pour lecture ; valeurs exactes, usages et identifiants dans les CSV/JSON. Les suffixes désignent les identifiants complets `NORM-G1K-FLAT-R+…-C+…`.

| Maille | Surface m² | Fraction | Routes m | Haies m | Végétalisé OCS m² | Arboré m² | ZH observés |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R+006421-C+000489 | 99120 | 0.0991 | 3618 | 93 | 27715 | 1772 | 0 |
| R+006421-C+000490 | 85788 | 0.0858 | 3322 | 0 | 32685 | 2791 | 0 |
| R+006421-C+000491 | 55768 | 0.0558 | 2110 | 0 | 13137 | 0 | 0 |
| R+006422-C+000490 | 648399 | 0.6484 | 20555 | 0 | 168640 | 22707 | 0 |
| R+006422-C+000491 | 309762 | 0.3098 | 8192 | 0 | 78055 | 1572 | 0 |
| R+006423-C+000485 | 55126 | 0.0551 | 1551 | 108 | 30694 | 5216 | 0 |
| R+006424-C+000485 | 441443 | 0.4414 | 12284 | 53 | 225566 | 2977 | 0 |
| R+006424-C+000486 | 975273 | 0.9753 | 22258 | 0 | 327306 | 36634 | 0 |
| R+006424-C+000487 | 1000000 | 1.0000 | 21737 | 0 | 313086 | 46826 | 0 |
| R+006424-C+000494 | 21231 | 0.0212 | 836 | 133 | 5697 | 89 | 0 |
| R+006424-C+000495 | 105681 | 0.1057 | 1241 | 0 | 92390 | 0 | 0 |
| R+006425-C+000485 | 275800 | 0.2758 | 6871 | 420 | 186860 | 38133 | 0 |
| R+006425-C+000486 | 998567 | 0.9986 | 20181 | 0 | 322187 | 38228 | 0 |
| R+006425-C+000494 | 809445 | 0.8094 | 17715 | 0 | 326830 | 21410 | 0 |
| R+006425-C+000495 | 1000000 | 1.0000 | 8738 | 1164 | 726838 | 18616 | 0 |
| R+006425-C+000496 | 305993 | 0.3060 | 1074 | 512 | 263872 | 1454 | 0 |
| R+006426-C+000489 | 1000000 | 1.0000 | 22580 | 0 | 254036 | 48610 | 0 |
| R+006426-C+000490 | 1000000 | 1.0000 | 30601 | 0 | 301026 | 76747 | 0 |
| R+006426-C+000495 | 548899 | 0.5489 | 7024 | 216 | 363099 | 656 | 0 |
| R+006426-C+000496 | 480568 | 0.4806 | 1179 | 0 | 480568 | 0 | 0 |
| R+006427-C+000489 | 628356 | 0.6284 | 16896 | 0 | 208684 | 52225 | 0 |
| R+006427-C+000490 | 1000000 | 1.0000 | 22106 | 0 | 184503 | 30556 | 0 |
| R+006428-C+000488 | 70761 | 0.0708 | 1107 | 0 | 42263 | 12990 | 0 |
| R+006428-C+000489 | 1549 | 0.0015 | 0 | 0 | 986 | 0 | 0 |
| R+006430-C+000494 | 1000000 | 1.0000 | 7837 | 1741 | 900569 | 9392 | 0 |
| R+006430-C+000495 | 1000000 | 1.0000 | 16402 | 3874 | 789712 | 53390 | 2 |
| R+006431-C+000494 | 931004 | 0.9310 | 2676 | 2754 | 928448 | 16221 | 2 |
| R+006431-C+000495 | 454358 | 0.4544 | 1357 | 162 | 454347 | 0 | 0 |
| R+006432-C+000494 | 171790 | 0.1718 | 447 | 0 | 171790 | 0 | 0 |
| R+006432-C+000496 | 27534 | 0.0275 | 0 | 0 | 27534 | 0 | 0 |
| R+006435-C+000497 | 239206 | 0.2392 | 5332 | 0 | 77681 | 2562 | 0 |
| R+006435-C+000498 | 653177 | 0.6532 | 14313 | 0 | 152366 | 9486 | 0 |

Les ZH de R+006430-C+000495 sont des friches/cultures photo-interprétées ; celles de R+006431-C+000494 ont typologie et qualité non définies. Elles ne sont pas traitées comme des habitats humides confirmés. Les plans d'eau et mares initialement non observés dans les 32 ne deviennent pas artificiellement présents. Les données OCS GE aquatiques restent distinctes.

## Invariants, livraison et contrôles

Les géométries et clés des 101 mailles sont identiques. **5 336 événements admis, une quarantaine, 60 mailles avec événements / 41 sans, 404 résultats R1–R4 non évaluables, 165 pistes, zéro recommandation : inchangés.** Aucun détecteur routes–matrices ni règle scientifique n'a été relancé ou modifié. Les anciens champs de décision et observations des fiches sont contrôlés individuellement ; les fichiers canoniques et actions sont inchangés par SHA-256.

**1 437 tests réussis**, dont 19 contrôles de la nouvelle condition documentaire ; 40 avertissements existants consignés. Build TypeScript/Vite réussi dans une copie temporaire de M3. Navigation Chrome vérifiée sur une ancienne grise de Caen : jaune V3b, détail OCS GE ouvert, vue D/S séparée, erreur de portée refusée, aucune erreur JavaScript. Captures et rapports dans `rapports/`. Le ZIP final est extrait dans un dossier neuf et vérifié avec le script autonome ; reçu `validation_extraction_v2.json` à côté du ZIP.

M4 peut ingérer les mêmes quatre fichiers internes, complétés par les nouveaux champs, avec les mêmes jointures `(territory_id, grid_version, maille_id)`. La version de grille reste `M1-CAEN-6COM-1KM2-FLAT-L93-O0-V1`. Les versions du socle M2, du complément 2023 et du triage V2 sont distinctes dans le manifeste. Une adaptation additionnelle de deux fichiers M3 met à jour la légende et les observations au clic ; elle s'applique après le patch Caen initial. Instructions exactes : `README.md` du ZIP. Aucun frontend d'équipe n'a été modifié ni déployé.

Les **300 fichiers préexistants protégés** restent identiques à l'état observé au début de cette tâche. L'archive V1 annoncée n'était plus présente à son chemin lors de cet audit ; les 92 fichiers de son dossier décomposé correspondent tous au manifeste V1 et n'ont pas été modifiés. La classification V1 est conservée explicitement dans la nouvelle version. Aucun ZIP antérieur n'a été écrasé. L'incident de place disque a été résolu en traitant les couches successivement et en supprimant les seules nouvelles extractions/écritures partielles ; les archives officielles vérifiées et tous les travaux antérieurs sont conservés.

Le lot est **interne uniquement** : licences et attributions conservées, aucun inventaire de coordonnées d'espèces sensibles acquis, aucun attribut de propriétaire/contact ajouté. Le verrou `test_data=False`, les contrats publics et règles D/S/R1–R4 sont inchangés. Aucun commit, push ou merge. L'absence de gris documentaire ne supprime **aucune des 101 indéterminations écologiques** ni les validations humaines/méthodes encore nécessaires.

Rejeu documentaire autonome facultatif, avec les dépendances SIG déjà consignées : `python reproduction/recalculer_triage_v2.py --output /chemin/vers/un_nouveau_resultat.json` depuis la racine extraite. Ce script recalcule les intersections des seules couches haies/eau/OCS GE avec les 101 mailles et vérifie les classes, sans recalculer les événements M2 ni exécuter D/S ou R1–R4.
