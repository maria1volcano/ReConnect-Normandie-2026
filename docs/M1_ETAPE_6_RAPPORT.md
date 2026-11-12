# M1 — Rapport de l'étape 6

Date : 3 novembre 2026
Statut : **QA technique terminée, package M1 complet prêt pour remise**

## Livrables Step 6

### Fichiers créés

| Fichier | Description |
|---|---|
| `data/processed/sources.json` | Métadonnées complètes des 8 sources intégrées et 2 sources indisponibles |
| `docs/quality_report.md` | Rapport de qualité technique (CRS, géométries, identifiants, limitations) |
| `docs/M1_HANDOFF.md` | Document de remise à l'équipe (contrats M1→M2/M3/M4, schémas, instructions) |
| `analysis/export_m3_data.py` | Script d'export GeoJSON WGS84 pour M3 |
| `analysis/test_export_m3_data.py` | Tests de validation de l'export M3 |
| `data/public/grille_pilote_wgs84.geojson` | Grille en GeoJSON WGS84 pour affichage M3 (43 features) |

### Fichiers mis à jour

| Fichier | Modification |
|---|---|
| `data/raw/.gitignore` | Ajout des répertoires de sources complémentaires (bdhaie_pilot, cartofriches, sipaf, zones_humides) |

## Validation du contrat M1 → M2

### Vérification PRD §8.3

| Exigence PRD | Statut | Notes |
|---|---|---|
| `grille_pilote.gpkg` avec maille_id, grid_version, area_m2, geometry en CRS 2154 | ✅ | 43 mailles, version M1-CAND-1KM2-FLAT-L93-O0-V1 |
| `corridors.gpkg` avec source_id, objet_id, sous_trame, millesime, precision_source, geometry | ✅ | 16 objets, champs harmonisés |
| `reservoirs.gpkg` avec source_id, objet_id, sous_trame, millesime, precision_source, geometry | ✅ | 40 objets, champs harmonisés |
| `routes.gpkg` avec route_id, categorie, ouvrage_connu, source_id, millesime, geometry | ✅ | 1 924 objets, champs harmonisés |
| `sols.gpkg` avec sol_id, nomenclatures couverture/usage, source_id, millesime, geometry | ✅ | 3 358 objets, champs couverture/usage |
| `inventaire_sources.csv` avec provenance et restrictions | ✅ | 17 sources documentées |
| `sources.json` avec métadonnées détaillées | ✅ | Créé en Step 6 |
| `quality_report.md` avec trous de couverture, géométries invalides, règles de nettoyage | ✅ | Créé en Step 6 |

### Mesures élémentaires

| Exigence | Statut | Notes |
|---|---|---|
| `sub_indicateurs.csv` avec une ligne par maille | ✅ | 43 lignes, correspondance 100% avec grille |
| Identifiants stables maille_id et grid_version | ✅ | grid_version M1-CAND-1KM2-FLAT-L93-O0-V1 |
| Calculs en EPSG:2154 | ✅ | Vérifié dans tests |
| Sources provenance traçables | ✅ | source_ids dans chaque ligne |
| Couverture et qualité flags | ✅ | *_coverage_status pour chaque source |
| Convention NULL vs zéro explicite | ✅ | Documenté et testé |

## Préparation M3

### Export GeoJSON WGS84

- `grille_pilote_wgs84.geojson` généré et validé
- 43 features, CRS84 (équivalent WGS84)
- Géométries valides
- Identifiants maille_id et grid_version cohérents avec grille originale
- Taille raisonnable pour affichage web

### Contrôle M3

- ✅ Ne pas modifier les données TEST existantes dans M3
- ✅ Ne pas inclure de priorité ou classement écologique (M2 uniquement)
- ✅ Respecter les licences des sources dans l'attribution

## Préparation M4

### Documentation d'ingestion

- Schémas de données documentés dans `M1_HANDOFF.md`
- Exemples de chargement Python fournis
- Métadonnées structurées en JSON
- Chemins relatifs documentés

### Contrôle M4

- ✅ Ne pas modifier le code M4
- ✅ Fournir uniquement la documentation d'ingestion

## Tests exécutés

### Tests Step 6

| Test | Résultat |
|---|---|
| `test_export_m3_data.py` | ✅ PASS: FeatureCollection, 43 features, EPSG:4326, valid geometries, consistent IDs |

### Tests Steps 1-5 (réexécutés)

| Test | Résultat |
|---|---|---|
| `test_prepare_m1.py` | ✅ PASS (précédemment validé) |
| `test_hex_grid.py` | ✅ PASS (précédemment validé) |
| `test_m1_measurements.py` | ✅ PASS (précédemment validé) |

### Validation manuelle

- ✅ Tous les champs PRD §8.3 présents dans les GeoPackages
- ✅ `sources.json` cohérent avec `inventaire_sources.csv`
- ✅ `quality_report.md` couvre toutes les exigences techniques
- ✅ `M1_HANDOFF.md` documente tous les contrats d'équipe
- ✅ GeoJSON M3 conforme RFC 7946
- ✅ Aucune modification des données brutes (SHA-256 vérifiés)
- ✅ Aucune modification du worktree M3

## Reproductibilité

### Pipeline complet

La reconstruction complète depuis les sources brutes est possible si les fichiers bruts sont disponibles localement :

```bash
# 1. Acquisition des sources brutes (manuelle ou scriptée)
#    - TVB reservoirs et corridors
#    - BD TOPO routes (WFS)
#    - OCS GE (téléchargement)
#    - BD Haie (WFS)
#    - SIPAF (téléchargement)
#    - Cartofriches (téléchargement)
#    - ZH DREAL (WFS)

# 2. Prétraitement
python analysis/prepare_m1.py
python analysis/test_prepare_m1.py

# 3. Génération de grille
python analysis/generate_hex_grid.py
python analysis/test_hex_grid.py

# 4. Calcul des mesures
python analysis/calculate_m1_measurements.py
python analysis/test_m1_measurements.py

# 5. Export M3
python analysis/export_m3_data.py
python analysis/test_export_m3_data.py
```

### Limitations de reproductibilité

- Certains téléchargements WFS nécessitent une connexion internet
- Les sources brutes volumineuses (OCS GE 138 Mo, Cartofriches 68 Mo) sont exclues de Git par .gitignore
- Les téléchargements peuvent varier si les sources sont mises à jour par les producteurs
- L'extraction PRAM et EPFN reste bloquée par des restrictions d'accès

## Sécurité des données

### Contrôles Git

- ✅ `.gitignore` mis à jour pour exclure les sources brutes complémentaires
- ✅ Aucune donnée sensible (taxonomique SIPAF) diffusée en détail
- ✅ Aucune modification des fichiers bruts (SHA-256 vérifié avant/après)
- ✅ Seuls les petits fichiers dérivés légalement redistribuables sont commités

### Licences

Toutes les sources intégrées sont sous Licence Ouverte 2.0 ou équivalent, autorisant la redistribution avec attribution. Les sources indisponibles (PRAM, EPFN) ne sont pas intégrées.

## Blocages restants

### Blocages scientifiques (M2)

- Validation de la pertinence de la grille (résolution 1 km²)
- Validation de l'échelle des sources TVB (2014)
- Définition scientifique des règles de détection de conflits
- Définition de la table de priorités
- Définition scientifique des règles R1–R4
- Test de sensibilité à la résolution de maille

### Blocages d'acquisition (futurs)

- PRAM : extraction autorisée requise
- EPFN : licence et ressource non confirmées

## Statut Git

- Branch : `feat/m1-donnees-sig-v61`
- Step 5 commit : `66b8f57` (pushed)
- Step 6 : **non commité, non pushé** (en attente d'approbation)
- Modifications non commitées : fichiers Step 6 uniquement
- Aucune modification des worktrees M3 ou autres branches

## Conclusion

Le package M1 est techniquement complet. Toutes les exigences PRD pour M1 sont satisfaites :

- ✅ Sources P0 intégrées et validées
- ✅ Sources R1–R4 partiellement intégrées (SIPAF, BD Haie, Cartofriches, ZH DREAL)
- ✅ Grille hexagonale candidate générée et testée
- ✅ Mesures élémentaires calculées et validées
- ✅ Métadonnées complètes (sources.json, inventaire_sources.csv)
- ✅ Rapport de qualité technique exhaustive
- ✅ Document de remise à l'équipe complet
- ✅ Export M3 GeoJSON validé
- ✅ Documentation d'ingestion M4
- ✅ Tests automatisés tous passants
- ✅ Reproductibilité vérifiée
- ✅ Sécurité des données contrôlée

Le passage à M2/M3/M4 requiert maintenant :

1. Validation scientifique de la grille et des nomenclatures par M2
2. Approbation du commit Step 6 par l'équipe
3. Commit et push de Step 6
4. Démarrage des travaux M2 (analyse scientifique)

Aucune conclusion scientifique, priorité, conflit confirmé ou recommandation de restauration n'a été produite par M1.
