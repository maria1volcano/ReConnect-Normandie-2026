# Intégration M3 — Caen et cinq communes

## Jeux affichés

- REAL : 101 cellules servies uniquement par le backend local M4, version
  `M1-CAEN-6COM-1KM2-FLAT-L93-O0-V1`, territoire
  `caen_et_nord_6communes`.
- TEST : `grille_pilote_wgs84.geojson`, 43 cellules historiques, version
  `M1-CAND-1KM2-FLAT-L93-O0-V1`.

Les observations utilisent toujours l’identité composite
`territory_id + grid_version + maille_id`. Aucun fallback vers TEST ou vers la
grille 66 n’est effectué si le backend REAL est indisponible.

## Trois concepts séparés

1. La vue « Ordre de vérification documentaire — exploratoire » affiche V1–V4.
2. La vue « Priorité écologique — non validée » garde les 101 cellules grises.
3. Le mode TEST affiche uniquement les priorités synthétiques des 43 cellules.

Les 165 pistes sont des investigations documentaires. Les 404 résultats R1–R4
restent `non_evaluable` et aucune recommandation validée n’est affichée.

## Accès aux données

Le service `backend/server.py` lit directement le ZIP M2 audité, vérifie son
SHA-256 et écoute exclusivement sur `127.0.0.1`. Il ne fournit aucune route vers
les GeoPackages, fichiers complets ou géométries d’événements. Les réponses ont
des en-têtes `no-store`, refusent les proxys déclarés et valident la portée sur
chaque fiche.

La grille publique 66 issue de l’étape précédente n’est plus utilisée par REAL.
Les données M2 101 ne sont ni copiées dans `frontend/public`, ni incorporées au
bundle de production.

La publication reste interdite tant que le projet n’a pas délivré d’autorisation
explicite et de contrat M4 de production.
