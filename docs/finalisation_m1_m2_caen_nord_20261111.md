# Caen Nord — finalisation du complément M1 dans le lot M2

**11 novembre 2026.** Le lot final comporte **66 fiches JSON provisoires**, les sorties SIG M2 préservées, les nouvelles observations IGN et des pistes d’investigation traçables. Il est autonome pour la consultation interne et la transformation vers le futur schéma M4. Le frontend existant n’a pas été refait. Le catalogue M5 et le schéma effectif M4, confirmés absents par le demandeur, n’ont pas été inventés.

**Version unique à transmettre maintenant** : [M2_CAEN_NORD_FINAL_M1_M2_20261111_V1.zip](../data/derived/caen_nord_5communes/final_m1_m2_20261111_01/M2_CAEN_NORD_FINAL_M1_M2_20261111_V1.zip) et son [fichier SHA-256](../data/derived/caen_nord_5communes/final_m1_m2_20261111_01/M2_CAEN_NORD_FINAL_M1_M2_20261111_V1.zip.sha256).

```text
data/derived/caen_nord_5communes/final_m1_m2_20261111_01/M2_CAEN_NORD_FINAL_M1_M2_20261111_V1.zip
```

Taille : **3,901,363 octets**, **56 fichiers**. SHA-256 : `e9b08b7f3e5879b20e8655850ce1dad783616a18c7eac2c8e96da6aad2726df5`.

**Complément reçu et contrôlé**

Le dossier annoncé `data/raw/m1_complement_caen_nord_20261111/` n’existait pas initialement. Le lot a été retrouvé sur le Mac dans `/Users/ouissal.c/Documents/LIVRAISON_M1_COMPLEMENT_CAEN_NORD_20261111/sorties_m1_complement/`, puis ses six fichiers ont été copiés au chemin attendu : GeoPackage, CSV, manifeste et trois pages WFS. Aucun environnement virtuel de cette livraison externe n’a été copié.

Les empreintes du GeoPackage, du CSV et des pages IGN concordent avec le manifeste. L’archive M1 de référence porte la même empreinte que celle du calcul M2 initial. Les pages WFS sont en EPSG:2154, leurs IDs ne se répètent pas entre pages. Le GeoPackage contient deux couches réelles : **733 haies MultiLineString** et **4 plans d’eau MultiPolygon**, géométries valides, non vides, IDs `source_id_m1_complement` et `cleabs` uniques par couche.

Les **66 lignes CSV** sont uniques sur `(grid_version, maille_id)` et se joignent bijectivement aux 66 mailles M2. Les surfaces de support concordent avec l’arrondi M1 ; les 132 mesures et compteurs locaux haies/plans d’eau ont été comparés aux intersections géométriques des mêmes supports. Le contrôle à 0,5001e-6 unité vérifie le CSV écrit à six décimales ; il ne crée aucune tolérance écologique ni modification du budget de frontière M2.

| Observation | Objets distincts | Relations locales | Mailles avec observation | Limite |
| --- | ---: | ---: | ---: | --- |
| Haies | **733** | **815** | **48** | 18 mailles à zéro observé, sans absence démontrée ; 66 675,857458 m selon le CSV |
| Plans d’eau | **4** | **5** | **4** | 3 `Retenue`, 1 `Réservoir-bassin` ; 78 408,530039 m² selon le CSV |
| Mares explicitement référencées | **0** selon le filtre M1 | 0 | 0 | Recherche sur `nature=Mare`, sans inventaire écologique exhaustif ni absence démontrée |
| Friches | NULL | Non calculées | Non évalué | Source non chargée, sans zéro imputé |
| Zones humides | NULL | Non calculées | Non évalué | Source non chargée, sans zéro imputé |

Les sommes de relations ne sont pas des nombres d’objets indépendants. La couverture `presence_observee_non_exhaustive` et les précisions/dates sources restent attachées aux observations ; aucune exhaustivité écologique n’est validée. Le statut source `Validé` des plans d’eau ne les qualifie pas en mares écologiques.

**SIG M2 préservé et enrichissement des 66 fiches**

Le GeoPackage M4 et les fonds routes/corridors/réservoirs/territoire sont copiés à l’identique. Le détecteur et l’agrégateur routes–corridors n’ont pas été relancés. Les comptes restent **3 157 détectés, 3 156 agrégés, 1 en quarantaine**, **3 096 couples, 2 378 routes distinctes**, **3 400 liens**, **40 mailles avec événements et 26 sans**. Le candidat en quarantaine n’est intégré à aucun événement de fiche ou piste R1 ; sa géométrie, son refus et les rapports stricts sont conservés.

Les fiches ajoutent les métriques et IDs des haies/plans d’eau, leurs attributs source, la qualité et les lacunes. Elles relient également les objets routes/corridors/réservoirs de contexte par une portion géométrique de dimension positive dans la maille. Ces nouveaux liens servent à consulter les sources ; ils ne créent pas de pression ou rupture fonctionnelle.

Les versions restent séparées :

```text
territory_id = caen_nord_5communes
grid_version = M1-CAEN-NORD-5COM-1KM2-FLAT-L93-O0-V1
dataset_version = M1-M2-CAEN-NORD-V1
complement_dataset_version = m1-caen-nord-complement-1
method_version = NULL
```

Les jointures conservent le scope et les identifiants métier. Le territoire M1 garde son alias `CAEN-NORD-5COM-V1`, explicitement relié au scope M2 par le manifeste. Les 14 identifiants communs au pilote historique ne permettent aucune jointure par maille seule ; aucun résultat de l’ancien territoire n’est mélangé au lot.

**Actions : évaluations des préconditions, pistes et recommandations**

Les règles et profils existants `m2-actions.spec-proposal-1`, révision `audit-2`, sont inchangés. **264 dossiers (66 × 4 familles)** ont été examinés : entrées au profil `normalizedInput`, faits incomplets `pendingEvidence`, résultats au profil `actionResult`. A0 et A1 ne correspondent pas aux faits déclarés ; la première règle A2 conclut `non_evaluable` : domaine inconnu et aucune méthode familiale approuvée fournie. Les résultats n’attestent aucune preuve positive, aucun contrôle de contradiction exclue ou avis d’expert inventé.

| Famille / identifiant connu | Diagnostic réellement disponible | Pistes documentaires | Résultat formel d’action |
| --- | --- | ---: | --- |
| R1 / **A04** | Croisements XY agrégés et contexte routier ; pistes sur voies en service, avec relation intérieure au territoire | **40 mailles** | 66 non évaluables ; sous-trame, qualité adaptée, contexte de perméabilité et méthode manquants |
| R2 / **A01** | Haies localisées, métriques et attributs observés ; contexte bocager consultable | **48 mailles** | 66 non évaluables ; aucune lacune topologique ou fonctionnelle documentée, aucune plantation depuis une densité |
| R3 / **A03** | Source friches non chargée | **0** | 66 non évaluables, aucune non-applicabilité ou absence supposée |
| R4 / **A02** | Plans d’eau localisés, nature et contexte à qualifier ; aucune mare attestée automatiquement | **4 mailles** | 66 non évaluables ; réseau humide, isolement, hydrologie et méthode non documentés |

**92 pistes documentaires sur 51 mailles ; 15 mailles sans piste locale étayée par ces observations.** Elles préparent une revue, elles ne sont ni une sortie A6 `conditionnelle` ni une recommandation de travaux. Les quatre dossiers ne signifient pas quatre règles activées. Les références A01–A04 sont les identifiants connus conservés, sans contenus de fiches M5 fabriqués.

Bilan : **0 recommandation étayée, 0 action conditionnelle validée, 0 travail recommandé, 264 actions non évaluables**. Cette non-évaluation ne signifie pas qu’aucune action ne serait nécessaire. Une preuve positive locale contrôlée pourrait ultérieurement permettre une étude sans exiger l’exhaustivité universelle des inventaires ; les méthodes/domaines et faits essentiels doivent être réellement satisfaits.

La priorité écologique reste **indéterminée sur les 66 fiches**, avec motifs explicites. Le champ formel `priorite_examen` reste `non_calculee`, valeur NULL, et la règle S vaut NULL : aucune configuration D/S approuvée n’a été simulée. L’ancien GeoPackage garde son état historique `actions_etat=non_calculees` ; l’audit des préconditions A2 est dans le JSON enrichi, sans recommandation calculée. Aucun niveau d’enjeu ne provient de la seule présence de corridor ou du nombre de croisements.

**Fichiers exacts du transfert**

| Fichier dans le ZIP | Utilisation |
| --- | --- |
| `fiches_zones.json` | Les 66 fiches provisoires : synthèse, observations, diagnostics, actions, pistes, sources, limites, priorité |
| `schema_fiches_provisoires.json` | Schéma interne de ce JSON, explicitement distinct du schéma réel M4 en attente |
| `actions_entrees.json`, `actions_resultats.json` | 264 entrées/résultats aux profils existants, sans statut favorable fabriqué |
| `references_actions.json` | Quatre appariements connus, pas un faux catalogue de 12 fiches |
| `donnees/m4_interne.gpkg` | Anciennes sorties validées et quarantaine, octet pour octet |
| `donnees/complement_mailles.gpkg` | 66 mailles complémentaires et 820 liens objets, sans modifier le GPKG M4 |
| `donnees/couches_m1_complement.gpkg`, `donnees/indicateurs_complement_66_mailles.csv` | Complément source original ; mêmes empreintes |
| Autres GPKG de `donnees/` | Routes, corridors, réservoirs et territoire du lot initial |
| `README.md`, `FORMAT_JSON_PROVISOIRE.md`, `ADAPTATION_M4.md` | Lecture et transformation future vers l’application existante |
| `rapports/`, `provenance/`, `specification/` | Contrôles, bilans, manifestes, pages IGN originales et règles inchangées |
| `manifeste_lot.json`, `SHA256SUMS` | Résolution relative du lot et empreintes ; aucun chemin du Mac nécessaire à la lecture |
| `MESSAGE_M4.md` | Message prêt à envoyer, non envoyé |

Le lot ne contient aucun cache, environnement virtuel ou fichier temporaire. [README complet](../data/derived/caen_nord_5communes/final_m1_m2_20261111_01/M2_CAEN_NORD_FINAL_M1_M2_20261111_V1/README.md) ; [bilan chiffré machine](../data/derived/caen_nord_5communes/final_m1_m2_20261111_01/M2_CAEN_NORD_FINAL_M1_M2_20261111_V1/rapports/bilan_final.json).

**Recette et suite M5/M4**

Après extraction, lancer `python3 outils/verifier_final.py`, puis par exemple `python3 outils/lire_fiche.py --maille NORM-G1K-FLAT-R+006428-C+000490`. Les outils lisent le JSON/SQLite avec Python standard. La lecture après extraction autonome a été vérifiée sur une maille mixte, une maille avec eau mais aucun événement et une maille sans piste. Une copie altérée est refusée. [Preuve de réception](../data/derived/caen_nord_5communes/final_m1_m2_20261111_01/validation_reception_finale.json).

Les 66 fiches et 264 profils d’action passent leurs schémas ; les contre-épreuves refusent une promotion A2 vers `conditionnelle` et une priorité calculée inventée. **342 tests ciblés passent** ; les 1 418 tests du SIG initial restent un résultat antérieur, sans suite complète relancée.

**Prêt :** données, jointures, provenance, diagnostics descriptifs, préconditions R1–R4, pistes et JSON provisoire autonome. **En attente de M5 :** le catalogue officiel et ses 12 fiches réelles. **En attente de M4 :** son schéma/exemple effectivement accepté, pour écrire une transformation versionnée et valider l’import dans l’application déjà fonctionnelle. Cette transformation ne nécessitera pas de relancer le SIG. Aucun format frontend supposé ni déploiement prétendu.

Le verrou de diffusion reste inchangé : `test_data=False` refusé, aucun faux `test_data=True` pour les données réelles, aucun export public parallèle `mailles.geojson`/`conflits.geojson`. Aucun commit, push ou merge. Les résultats et documents antérieurs sont conservés.
