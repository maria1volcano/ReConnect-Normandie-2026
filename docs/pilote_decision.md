# Décision technique provisoire du pilote — M1

Date : 3 novembre 2026  
Responsable de la recommandation technique : M1  
Statut : **GO technique provisoire M1, validation M2/M5 requise**

## Critères du PRD

Le §3.1 impose une comparaison fondée sur la couverture TVB, les routes, la finesse de l'occupation du sol, les couches R1–R4, les millésimes et la possibilité de contrôle manuel. La présence de fichiers ne suffit pas. La recommandation ci-dessous ne vaut ni validation scientifique, ni diagnostic régional, ni choix final M1/M2.

## Candidats examinés

| Candidat technique | TVB | Routes | Occupation du sol | R1–R4 | Faisabilité / limites | Avis M1 |
|---|---|---|---|---|---|---|
| **Estuaire de l'Orne compact** — bbox WGS84 `[-0.28, 49.20, -0.22, 49.26]`, soit Lambert-93 `[460989.257, 6904815.661, 465631.045, 6911663.951]` | 40/20 404 réservoirs et 17/14 534 corridors intersectent réellement le bbox ; polygones EPSG:2154 | 1 924/1 926 LineString intersectent réellement le bbox ; EPSG:4326 | 3 683/417 689 objets d'occupation et 99/31 340 zones construites intersectent réellement le bbox ; EPSG:2154 | R1 : preuves locales disponibles ; R2 : potentiellement pertinent, non vérifié ; R3 et R4 : données locales insuffisantes | Emprise compacte avec couverture P0 non vide et contrôle manuel plausible. Les quatre familles ne sont pas encore toutes démontrables | **GO technique provisoire recommandé** |
| **Calvados départemental D014** | Même TVB ; couverture départementale à mesurer | Archive BD TOPO 3.5 D014 2026-09 disponible, 372 029 398 octets | OCS GE 2023 complète inspectée | Même accès national/régional | Très bonne disponibilité P0, mais 417 689 objets OCS GE rendent le périmètre trop large pour un pilote contrôlable manuellement et pour une démonstration légère | NO-GO comme pilote compact ; conserver comme emprise source |
| **Orne / secteur Parc Normandie-Maine** | Corridors et réservoirs Basse-Normandie accessibles | BD TOPO D061 théoriquement disponible via le même service, non acquise ici | OCS GE D061 à vérifier/acquérir | Inventaire ouvert de mares 2003–2013 et exemple EPFN Orne ; données anciennes ou licence EPFN absente | Intérêt possible pour R3/R4, mais aucune inspection P0 D061 dans cette étape et couverture locale hétérogène | Réserve / second site possible après acquisition dédiée |
| **Estuaire de Seine / Normandie orientale** | Réservoirs régionaux disponibles ; la couche corridors inspectée/candidate actuelle vise surtout l'ex-Basse-Normandie | BD TOPO/OCS GE disponibles par départements mais non acquis ici | Non vérifiée dans cette étape | Sources nationales disponibles, PRAM régional | Incertitude plus forte sur le jeu de corridors et aucune preuve locale P0 réunie dans le paquet actuel | NO-GO à ce stade |

## Recommandation

Retenir **provisoirement un secteur compact de l'estuaire de l'Orne**, avec le bbox ci-dessus comme emprise de travail technique initiale. Cette recommandation repose maintenant sur des intersections géométriques réelles et non sur les seules emprises : les cinq couches P0 inspectées ont une couverture locale non vide. Elle ne démontre toutefois pas que les quatre familles d'action disposent de cas robustes.

Le contour final ne doit pas être figé avant que M2 ait :

1. confirmé la cohérence scientifique et l'échelle d'emploi des 40 réservoirs et 17 corridors locaux ;
2. vérifié qu'un ou plusieurs secteurs permettent de tester honnêtement R1–R4 ;
3. statué sur l'usage de plusieurs sites d'essai si un seul secteur compact ne couvre pas quatre cas robustes ;
4. validé la future taille de grille indépendamment de ce choix technique.

## Faisabilité actuelle R1–R4

| Famille | Classement | Éléments disponibles | Limite actuelle |
|---|---|---|---|
| R1 — franchissements faune/routes | **Evidence available for further investigation** | 1 924 tronçons routiers, 17 corridors et 40 réservoirs intersectent le bbox | Aucun croisement route-corridor ni ouvrage SIPAF n'a été calculé ; présence simultanée ≠ conflit |
| R2 — haies/bocage | **Potentially relevant but not yet verified** | BD Haie V2 est accessible et le contexte OCS GE est présent | Aucun objet BD Haie local n'a été acquis ou compté |
| R3 — friches | **Insufficient data** | Cartofriches est accessible nationalement | Aucun objet de friche local inspecté ; EPFN sans licence confirmée |
| R4 — mares/zones humides | **Insufficient data** | Inventaire DREAL zones humides accessible ; PRAM régional identifié | Aucun objet mare/zone humide local inspecté ; PRAM sur demande |

Ces classements évaluent seulement la possibilité de poursuivre l'étude. Ils ne constituent ni recommandation d'action, ni preuve d'absence lorsqu'aucun objet n'est documenté.

## Limites et dépendances

- Les corridors sont ouverts et inspectés, mais proviennent du SRCE 2014 et de la vectorisation des matrices verte/bleue ; leur fonctionnalité actuelle n'est pas démontrée.
- L'extrait BD TOPO est un flux WFS courant : les dates existent par objet, mais aucun millésime global n'est fourni dans la réponse.
- La couverture locale de SIPAF, BD Haie, Cartofriches, PRAM et zones humides n'a pas été mesurée.
- PRAM exige une demande d'extraction et une clarification des droits de redistribution.
- Le SRCE est millésimé 2014 ; sa précision ne doit pas être présentée comme équivalente à celle de BD TOPO ou OCS GE.
- Le bbox est une emprise d'acquisition, pas une délimitation écologique ou administrative validée.

**Décision demandée à M2/M5 :** GO/NO-GO sur l'estuaire de l'Orne ; validation de l'échelle SRCE ; puis définition de l'emprise scientifique finale ou d'un dispositif multi-sites si R2–R4 restent insuffisamment couverts.
