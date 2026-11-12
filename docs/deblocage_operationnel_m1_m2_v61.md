# Déblocage opérationnel M1 → M2 — 8 novembre 2026

**Prêt à poursuivre dès réception des géométries et approbation du correctif numérique.** Le correctif reste proposé ; aucun fichier préexistant, branche de travail ou contrat n'a été modifié. Aucun calcul réel, sauvegarde, clone/worktree, merge, commit, push ou message à M1 n'a été exécuté.

**V** = vérifié ; **R** = recommandé ; **H** = interprétation/décision restante. [Plan détaillé, commandes et critères de réception](deblocage_m1_m2_v61/plan_detaille.md). Aucun audit A–J, statistique CSV ou scénario de résolution antérieur n'a été relancé.

## 1. Diagnostic géométrique exact

**V.** M1 reste sur `fc76d6230994af9aef27f42bb42e0374cd0c8251` après fetch : aucun changement depuis l'audit. Les deux entrées utilisées correspondent exactement à ce commit. Toutes les **903 paires distinctes** ont été intersectées en EPSG:2154, sans arrondi ni réparation.

| Résultat | GeoJSON M1 reprojeté | Grille régénérée en mémoire |
| --- | ---: | ---: |
| Paires disjointes | 806 | 806 |
| Contacts sans surface, tous LineString | 76 | 75 |
| Paires surfaciques, toutes Polygon | **21** | **22** |
| Aire maximale d'intersection | **8,6669331333 × 10⁻⁷ m²** | **5,7779554222 × 10⁻⁷ m²** |
| Somme des aires d'intersection | **4,8447351432 × 10⁻⁶ m²** | **4,7423968688 × 10⁻⁶ m²** |
| Somme des aires des mailles moins aire de l'union | **4,8391520977 × 10⁻⁶ m²** | **4,5113265514 × 10⁻⁶ m²** |

**V/H.** Les intersections positives existent donc dans les coordonnées flottantes, dès la génération : le rejet n'est pas une simple erreur de soustraction. Leurs largeurs équivalentes maximales `2A/P` sont d'environ **1,397 nm** et **0,931 nm**, comparables à l'espacement des flottants en Y (**0,931 nm**). Ce sont des micro-chevauchements topologiques d'origine numérique fortement étayée ; aucun défaut plus ample n'est détecté. `2A/P` n'est pas une largeur maximale garantie. Les deux mesures globales diffèrent aussi par leurs opérations d'overlay/aire ; elles ne sont pas interchangeables, notamment en présence de recouvrements triples. [Limites de précision expliquées par GEOS](https://libgeos.org/usage/faq/).

## 2. Correctif et tests

**R.** [Diff proposé, non appliqué](deblocage_m1_m2_v61/grid_overlap.proposition.patch) : limiter le changement au contrôle de grille et à un helper. Garder `grid_overlap`, la constante `1e-6 m²`, les géométries et la garde de lacune. Ajouter des contrôles par paire et un avertissement pour les résidus acceptés.

Le prototype calcule `δ = hypot(max ULP(X), max ULP(Y))`, un budget local `B_ij = δ × périmètre polygonal de l'intersection + πδ²`, et un budget global `δ × somme des périmètres + somme des ULP des aires + ULP de l'aire d'union`. Refuser une paire si son aire dépasse **min(1e-6, B_ij)** ; refuser aussi un excès global dépassant **max(1e-6, B_global)**. Ici `δ ≈ 9,3314e-10 m`, `B_global ≈ 1,18282e-4 m²` ; chaque paire doit satisfaire sa propre garde, indépendamment de ce budget global.

**H.** C'est une convention d'ingénierie dérivée de la résolution machine, **pas une borne certifiée de l'erreur GEOS**. Elle doit être approuvée avant activation. Aucun coefficient écologique ni constante agrandie n'est introduit ; aucun snap automatique n'est proposé.

**V.** Le prototype et le validateur exact proposé, exécuté en copie temporaire, concordent sur **16 contrôles ciblés** : grilles M1, permutation, contacts/disjonction, vrais chevauchements, duplication, contenance, triple recouvrement, petits recouvrements sous le plafond mais non numériques, déplacement M1 de 1 mm, garde de lacune et deux configurations. Les deux grilles passent avec avertissement ; les chevauchements des contre-exemples restent refusés. `git apply --check` réussit. Après approbation, intégrer ces cas aux tests et vérifier les chemins SIG/frontières/rattachements. [Preuves et reproduction](deblocage_m1_m2_v61/README.md).

## 3. Paquets à obtenir

**V.** Les six GPKG restent absents de Git et de notre projet local ; aucune conclusion sur l'ordinateur de M1.

- **Minimal :** réservoirs, corridors et routes ; grille GPKG ou génération pure figée ; contour exact retourné par `generate_grid()`, sans changer la construction du rectangle ; manifeste des fichiers reçus avec tailles/SHA-256, couches, CRS, champs/types, versions et droits.
- **Complémentaire :** sols et zones construites ; bruts/extraits figés utilisés par les mesures ; haies, SIPAF, Cartofriches et zones humides nécessaires et transmissibles ; couvertures par thème/emprise/période et dictionnaires TVB. PRAM/EPFN ne bloquent pas le démarrage.

**R.** Si M1 ne transmet pas le GPKG de grille, le produire ultérieurement dans la copie isolée avec ses deux couches et vérifier les empreintes déjà auditées ; exporter séparément le contour exact. Aucun téléchargement actualisé ne remplace le snapshot.

## 4. Configurations et premiers calculs internes

**V.** [Configuration enjeux](deblocage_m1_m2_v61/config_enjeux.proposition.json) et [configuration conflits](deblocage_m1_m2_v61/config_conflits.proposition.json) acceptées par les véritables parseurs M2. Mappings documentés : grille `maille_id`, routes `route_id/categorie`, corridors `objet_id/classe_corridor`, EPSG:2154. Leurs valeurs/types restent à vérifier dans les couches reçues.

**R.** Couvertures conservées `unknown` ; aucun niveau/ouvrage, dictionnaire de sous-trames, précision métrique ou validateur inventé. Après réception et correctif approuvé : valider les entrées, lancer `run_enjeux.py`, puis `run_conflicts.py` avec les chemins/couches et sorties nouvelles du [plan d'exécution](deblocage_m1_m2_v61/plan_detaille.md). La méthode non encore désignée reste NULL ; le paquet déclaré `M1-V1` est relié au commit et aux empreintes.

Contrôler ensuite les couples/lots avec `verify_artifact_pair()` et `verify_conflict_bundle()` ; comparer par maille les aires étudiées/réservoirs/corridors aux colonnes CSV correspondantes, en expliquant les arrondis. Préserver `liens_mailles_conflits`, toutes les frontières et un propriétaire canonique par événement ; nombre distinct global ≠ somme des comptes locaux. Un compte de routes n'est pas un compte d'événements.

## 5. Travaux immédiats

**V, réalisés :** paires mesurées, correctif préparé et testé hors production, configurations parsées, commandes/contrôles et demande M1 prêts. **R, étape suivante :** approuver puis appliquer le correctif dans la copie isolée et préparer les exports grille/contour. Les calculs réels attendent les trois couches sources. ENJ-01 reste NULL sans complétude validée ; croisement ≠ obstacle, corridor SRCE ≠ fonctionnalité actuelle, absence d'observation ≠ absence écologique.

## 6. Décisions scientifiques restantes

**H.** Valider la convention numérique et le contour/version ; identifier la méthode géométrique ; approuver les nomenclatures, couvertures, classes d'enjeu et qualifications lorsque les preuves existent. Les priorités restent inconnues sans méthode approuvée. Ne pas activer R2/R4 sans leurs faits/méthodes. Ces décisions n'empêchent pas le descriptif interne. Aucun contrat M4 ni protection `test_data=False` n'est modifié ou contourné.

## 7. Intégration Git sécurisée, non exécutée

**V.** Branche M2 inchangée ; deux fichiers suivis modifiés (`detect_conflicts.py`, `methode_m2.md`), fichiers essentiels non suivis et caches ignorés conservés. Les empreintes des **86 fichiers préexistants**, ignorés compris, sont inchangées. Aucune collision entre chemins modifiés dans les commits des deux branches, ni entre chemins M1 suivis et M2 non suivis ; ce n'est pas un essai de merge. M1 impose pandas 3.1.0, M2 pandas <3 : environnements séparés nécessaires ; Python déclaré M1 est aussi à clarifier (handoff 3.14+, rapports 3.12).

**R.** Après autorisation séparée : suspendre les écritures ; sauvegarder intégralement le répertoire avec `.git`, cachés/non suivis/ignorés, permissions/liens ; vérifier la restitution et les empreintes. Créer une copie indépendante à HEAD M2, intégrer M1 seulement dans cette copie, puis rejouer les travaux sauvegardés sans remplacer son `.git`, en contrôlant les collisions et suppressions. Recevoir les GPKG, appliquer le correctif approuvé, tester et revoir le diff avant tout report. L'original et sa sauvegarde restent intacts ; aucun reset/clean/stash n'est nécessaire. Un patch ou bundle seul ne sauvegarde pas tous les travaux.

## 8. Message à M1 proposé, non envoyé

> Bonjour, nous travaillons toujours sur `fc76d6230994af9aef27f42bb42e0374cd0c8251`. Peux-tu transmettre les fichiers figés `reservoirs.gpkg`, `corridors.gpkg` et `routes.gpkg`, avec couches, champs/types, CRS et manifeste tailles/SHA-256 lié à cette livraison ? Ils ne sont pas accessibles dans Git ou notre copie locale ; nous ne présumons pas de leur absence chez toi.
>
> Ton GPKG de grille convient aussi ; sinon nous pouvons le générer depuis le code figé, avec le contour exact. Merci de signaler toute différence de contour/version et de compléter uniquement les informations de droits manquantes sur les fichiers transférés.
>
> En complément : sols/zones construites, bruts ou extraits figés effectivement utilisés (haies, SIPAF, Cartofriches, zones humides lorsque transmissibles), dictionnaires TVB et éventuelles preuves de couverture non déjà livrées. PRAM/EPFN ne bloquent pas ce premier lancement. Aucun nouveau téléchargement actualisé n'est demandé pour remplacer ces fichiers.
