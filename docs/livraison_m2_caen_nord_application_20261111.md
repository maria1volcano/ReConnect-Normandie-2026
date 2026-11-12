# Livraison M2 Caen Nord pour l’application du 12 novembre 2026

**11 novembre 2026 — transfert interne prêt, vérifié après extraction autonome.** Aucun calcul scientifique relancé. Les données, résultats et documents antérieurs sont inchangés ; ni contrat public, ni tolérance, ni règle D/S ou R1–R4 modifiés. Aucun commit, merge, push ou envoi à M4.

ZIP : [M2_CAEN_NORD_M4_INTERNE_20261111_V1.zip](../data/derived/caen_nord_5communes/transfert_m4_20261111_01/M2_CAEN_NORD_M4_INTERNE_20261111_V1.zip) (**2 684 156 octets**, 28 fichiers), accompagné de son [SHA-256 externe](../data/derived/caen_nord_5communes/transfert_m4_20261111_01/M2_CAEN_NORD_M4_INTERNE_20261111_V1.zip.sha256).

Chemin depuis la racine du dépôt :

```text
data/derived/caen_nord_5communes/transfert_m4_20261111_01/M2_CAEN_NORD_M4_INTERNE_20261111_V1.zip
```

SHA-256 du ZIP : `737c2f64bf79fad4678ffb0c7c6143c0eeae13dafe6e681b2acdcdc2e69a967e`.

**1. Diagnostic précis de la quarantaine**

| Élément | Valeur vérifiée |
| --- | --- |
| `conflit_id` | `rc_4ce22d4da9ae4d1496dbe7540ad01b39eab1bd5d0665ea8259784f873b243bdc` |
| Route source | `TRONROUT0000002334259154`, espace `BDTOPO_ROUTES` ; route à 1 chaussée, en service, position `0` |
| Corridor source | `TVB-COR-5FC3F5285AD4722F9C24`, espace `TVB_COR_BN` ; matrice fragile, SRCE 2014, sous-trame `-` |
| Géométrie | LineString XY, EPSG:2154 ; longueur **17,331072774438148 m** |
| Relation au territoire | `interieur_et_frontiere`, DE-9IM `1010F0212` ; intérieur linéaire présent mais `study.covers(event)=false` |
| Longueur extérieure cumulée | **1,2493837389962852 × 10⁻⁹ m** |
| Hausdorff vers l’intersection au territoire | **1,1301883402599254 × 10⁻⁹ m** |
| Budget numérique existant, diagonale ULP | **9,331397911231848 × 10⁻¹⁰ m** |
| Règle | `analysis.aggregate_conflicts._territory_membership` ; les deux gardes numériques sont dépassées |
| Décision | Refus maintenu, aucune géométrie ni tolérance modifiée |

```text
LINESTRING (457935.73014440783 6903626.962672654, 457935.90019415 6903616.50461352, 457939.56149044656 6903610.689613523, 457939.5614904468 6903610.689613523)
```

Le WKB complet, son empreinte, la différence au territoire et l’empreinte du code de validation sont dans [diagnostic_quarantaine.json](../data/derived/caen_nord_5communes/transfert_m4_20261111_01/M2_CAEN_NORD_M4_INTERNE_20261111_V1/rapports/diagnostic_quarantaine.json). Seul le contrôle de cet événement existant a été réappliqué ; aucune détection ou agrégation relancée.

`statut=croisement_detecte` constate la détection, sans admission automatique au lot agrégé ni qualification écologique. `numeric_residue=false` qualifie la taille totale de l’intersection selon le détecteur ; ce n’est pas un succès du contrôle d’appartenance. Le motif précis reste `event_outside_territory`. Les rapports stricts originaux demeurent bloqués ; le lot admis reste explicitement partiel avec quarantaine.

L’événement a `maille_ids=[]`, **aucun lien et aucun propriétaire canonique**. Sa maille intersectée à titre exploratoire, `NORM-G1K-FLAT-R+006425-C+000492`, porte déjà **183 observations locales et 164 exclusives**. Une inclusion naïve ferait 184 observations locales, mais n’est pas appliquée ; **la répartition 40/26 ne changerait pas**. Une autre composante admise de la même paire, `rc_2d349f551fe4b2b9646c2f4fa7e608785a686d71991e2309ee88ecae056ab746`, conserve cette paire et cette route dans les comptes globaux.

**2. Validation des comptes depuis les événements agrégés**

| Compte | Valeur | Contrôle |
| --- | ---: | --- |
| `evenements_detectes` | **3 157** | 3 156 admis + 1 en quarantaine |
| `evenements_agreges` | **3 156** | IDs uniques de `evenements` |
| `evenements_en_quarantaine` | **1** | Aucun ID commun avec les événements admis ou les liens |
| Liens événement–maille | **3 400** | Couples uniques, références résolues |
| Propriétaires canoniques | **3 156** | Exactement un par événement agrégé |
| Mailles avec observations | **40** | Au moins un lien vers `evenements` |
| Mailles sans événement observé | **26** | Jointure gauche sur les 66 mailles, zéro lien |
| Couples route–corridor / routes distinctes | **3 096 / 2 378** | Comptés depuis `source_pairs` agrégé, sources incluses résolues |

Chaque compte local et exclusif a été comparé aux liens effectivement livrés. Somme locale = **3 400**, jamais un total d’événements ; somme exclusive = **3 156**. Les 26 zéros observés ne sont pas des absences écologiques validées.

**3. Couches et champs du GeoPackage M4**

Le fichier livré est une copie **octet pour octet** de `data/derived/caen_nord_5communes/m2_caen_nord_20261111_02/m4_interne.gpkg`. SHA-256 : `49f30ecb75288ab68e8d0b536f67bca5294340fa1607b8202df2cb850b5333e4`. Intégrité SQLite, CRS, identités, versions, propriétaires et références vérifiés.

| Couche/table | Lignes | Géométrie effective / CRS | Identifiant métier après le scope |
| --- | ---: | --- | --- |
| `mailles` | 66 | MultiPolygon / EPSG:2154 | `maille_id` |
| `enjeux` | 66 | MultiPolygon / EPSG:2154 | `maille_id`, jointure 1:1 |
| `evenements` | 3 156 | LineString XY / EPSG:2154 | `conflit_id` |
| `quarantaine` | 1 | LineString XY / EPSG:2154 | `conflit_id`, sans lien officiel |
| `liens_mailles_evenements` | 3 400 | Non spatiale | `(conflit_id, maille_id)` |

Les tables `gpkg_*`, `rtree_*`, `sqlite_sequence` et le FID sont techniques. Le [FORMAT.md exhaustif](../data/derived/caen_nord_5communes/transfert_m4_20261111_01/M2_CAEN_NORD_M4_INTERNE_20261111_V1/FORMAT.md) liste **tous les champs, types physiques et effectifs de NULL**, fonds M1 compris. Le même inventaire est disponible en [JSON](../data/derived/caen_nord_5communes/transfert_m4_20261111_01/M2_CAEN_NORD_M4_INTERNE_20261111_V1/rapports/inventaire_geopackages.json).

Champs utiles pour la fiche :

- Identité et support : `maille_id`, `territory_id`, `grid_version`, `dataset_version`, `method_version`, `study_area_m2`. `contexte_mailles.json` reprend les attributs M1 `is_boundary`, `pilot_fraction`, `full_area_m2`, `clipped_area_m2` ; aucune géométrie complète ne remplace le fragment.
- Observations : `conflit_ids`, `nb_evenements_observes`, `nb_evenements_exclusifs_observes`, les quatre `nb_<statut>_observes`. `nb_evenements` reste NULL sur 66 mailles.
- Qualité : `etat_analyse`, `diagnostic`, `fiabilite`, couvertures et complétudes routes/corridors.
- Enjeux par jointure : aires observées réservoir/corridor, longueur de corridor, `enj_01_pct/status`, `enj_02_presence/status`, couvertures et champs de sensibilité.
- Priorité et actions : `priorite_etat=non_calculee`, `priorite_valeur=NULL`, `enjeu_classe=inconnu`, `actions_etat=non_calculees`. **`priorite_examen` n’est pas une colonne physique** : la vue affiche `{etat:"non_calculee",valeur:null}` à partir des deux premiers champs. Aucune recommandation R1–R4.

Pièges documentés : listes/objets en **texte JSON**, à décoder une fois ; booléens SQLite en 0/1 ; `enj_02_presence` physiquement REAL (**44 valeurs 1, 22 NULL, aucun 0**). Ne pas transformer NULL en false. `enj_01_pct`, `nb_evenements`, `priorite_valeur`, `method_version` sont NULL partout. Les précisions d’intersection et scénarios de sensibilité ne sont pas calculés.

**4. Versions et séparation du pilote initial**

Les 66 mailles et toutes les lignes métier de `m4_interne.gpkg` portent exclusivement :

```text
territory_id    = caen_nord_5communes
grid_version    = M1-CAEN-NORD-5COM-1KM2-FLAT-L93-O0-V1
dataset_version = M1-M2-CAEN-NORD-V1
method_version  = NULL
```

Clé maille : ces trois composantes renseignées + `maille_id`. Clé événement : les mêmes trois + `conflit_id`. Ne pas joindre par égalité SQL sur `method_version=NULL`. Les 14 IDs de mailles partagés avec l’ancien territoire ne permettent aucune jointure sur `maille_id` seul. Aucune ligne de l’ancienne grille `M1-CAND-1KM2-FLAT-L93-O0-V1` ni fond du pilote de 43 mailles n’est incluse.

Le territoire M1 garde son alias source `CAEN-NORD-5COM-V1`, explicitement associé au scope M2 par `manifeste_lot.json:source_scope`. Les routes/corridors/réservoirs M1 n’ont pas de `grid_version` : leur portée de livraison vient du manifeste et des empreintes, sans colonne inventée.

Les manifestes originaux M1/M2 restent inchangés sous `provenance/` et peuvent référencer des chemins de calcul non transportés. **Seul `manifeste_lot.json` résout les chemins relatifs nécessaires à l’ingestion** : 26 fichiers de charge utile avec tailles, SHA-256, origines, scope et comptes. `SHA256SUMS` protège aussi ce manifeste ; l’empreinte externe protège le ZIP entier. Aucun chemin historique du Mac n’est requis pour lire le lot.

**5. Contenu et ingestion courte pour M4**

Le GeoPackage seul ne fournit pas les fonds ni les explications de quarantaine. Le ZIP ajoute uniquement les données nécessaires, rapports, manifestes, README, format, brouillon de message et deux lecteurs Python. **Aucun cache, environnement virtuel ou temporaire.**

Fonds inclus, copies M1 inchangées : **8 539 routes MultiLineString Z**, **31 corridors MultiPolygon**, **20 réservoirs MultiPolygon**, un territoire Polygon et cinq communes MultiPolygon, tous EPSG:2154. Les attributs Z, niveau, vitesse et autres champs routiers restent du contexte, sans preuve de perméabilité ou de trafic. Les géométries découpées des 66 mailles sont déjà dans `mailles`.

Depuis le dossier du ZIP et de son SHA-256 :

```sh
LC_ALL=C shasum -a 256 -c M2_CAEN_NORD_M4_INTERNE_20261111_V1.zip.sha256
unzip M2_CAEN_NORD_M4_INTERNE_20261111_V1.zip
cd M2_CAEN_NORD_M4_INTERNE_20261111_V1
LC_ALL=C shasum -a 256 -c SHA256SUMS
python3 outils/verifier_lot.py
python3 outils/lire_fiche.py --maille NORM-G1K-FLAT-R+006425-C+000492
python3 outils/lire_fiche.py --maille NORM-G1K-FLAT-R+006424-C+000494
```

`LC_ALL=C` évite une incompatibilité de locale Perl/macOS. Les lecteurs exigent seulement Python standard ; un pilote SIG tel que GeoPandas/GDAL est requis pour les géométries. Le README donne un exemple de reprojection **en mémoire** pour une vue interne longitude/latitude, sans export public ni recalcul des liens.

Construire la carte depuis les **66 mailles**, joindre `enjeux` en 1:1, puis filtrer les événements via les liens sur `(territory_id, grid_version, dataset_version, maille_id)`. Le SQL est dans `FORMAT.md`. Garder tous les liens pour la liste locale ; `canonical_owner=1` ne sert qu’aux comptes exclusifs. Une jointure intérieure sur les liens supprimerait les 26 mailles sans observation : employer une jointure gauche. Quarantaine séparée, masquée par défaut.

La réception autonome a été testée après extraction dans un autre dossier, depuis un autre répertoire courant : empreintes valides ; fiche **183/164** ; fiche **0 observation, 0 lien** avec priorité non calculée ; maille hors lot refusée ; copie temporaire altérée refusée. [Validation de réception](../data/derived/caen_nord_5communes/transfert_m4_20261111_01/validation_reception.json).

**Un test ciblé** du verrou public passe. Les **1 418 tests** restent le résultat de l’exécution précédente, journal inclus ; la suite complète n’a pas été relancée.

**6. Message prêt à envoyer à M4 — non envoyé**

> M4 — Caen Nord est prêt pour ingestion interne pour la carte du 12 novembre.
>
> ZIP : M2_CAEN_NORD_M4_INTERNE_20261111_V1.zip, accompagné de son .zip.sha256. Vérifier l’archive, extraire, puis exécuter `python3 outils/verifier_lot.py` depuis la racine du lot. README.md et FORMAT.md donnent les relations, champs et exemples de lecture ; aucun accès à l’arborescence du Mac émetteur n’est nécessaire.
>
> Charger `donnees/m4_interne.gpkg` : 66 mailles, 3 156 événements agrégés, 3 400 liens et un propriétaire par événement. Le total détecté est 3 157 : un candidat reste en quarantaine, hors des liens et des compteurs. Les 40 mailles avec observations et 26 sans événement sont confirmées depuis les liens agrégés. Les fonds routes (8 539), corridors (31), réservoirs (20), territoire et communes sont inclus.
>
> Filtrer sur territory_id=caen_nord_5communes, grid_version=M1-CAEN-NORD-5COM-1KM2-FLAT-L93-O0-V1 et dataset_version=M1-M2-CAEN-NORD-V1, puis maille_id. Ne pas mélanger avec les 43 mailles du pilote précédent. Afficher observations locales et comptes exclusifs séparément, priorité non calculée, actions non calculées, et « absence non démontrée » dans les 26 mailles sans événement.
>
> La réserve de frontière reste documentée ; aucune géométrie ou tolérance changée. Elle ne bloque pas l’affichage interne des résultats admis. Le verrou public test_data=False reste intact : ce ZIP n’est ni un export public ni une autorisation de diffusion. L’application M4 n’étant pas dans ce dépôt, son branchement et un contrôle visuel restent à faire de votre côté. Merci de confirmer la lecture du vérificateur et de deux fiches, l’une observée et l’autre sans événement, avant la démonstration.

Copie directe : [MESSAGE_M4.md](../data/derived/caen_nord_5communes/transfert_m4_20261111_01/M2_CAEN_NORD_M4_INTERNE_20261111_V1/MESSAGE_M4.md).

**7. Blocages pour l’affichage demain**

- **Lecture interne : aucun blocage de données constaté.** La réserve isolée ne bloque pas la consultation des 66 mailles et 3 156 événements admis. Une carte descriptive doit conserver les inconnues et les limites.
- **Application : branchement restant côté M4.** Ce dépôt ne contient pas de frontend, serveur ou chargeur M4. L’import et le contrôle visuel réel dans l’application n’ont donc pas été effectués ; le paquet testé ne vaut pas déploiement.
- **Diffusion publique : verrou inchangé.** `test_data=False` reste refusé. Une carte publique passant par ce contrat exige la validation M1/M2/M4 du format et des droits, puis un changement approuvé. Aucun faux `test_data=True` pour des données réelles, aucun exporteur public ajouté.
- **Priorités et actions : non calculées.** Aucune couleur rouge/orange/jaune ou recommandation R1–R4. Si les mailles sont grises, libeller « priorité non calculée ». Zéro observation reste « absence non démontrée » ; aucun seuil écologique dérivé des croisements.
