# Démonstration locale ReConnect — Caen et cinq communes (6 communes, 101 mailles)

## Prérequis

- conserver le ZIP M2 à son emplacement d’origine ;
- utiliser uniquement `127.0.0.1` ;
- ne pas ouvrir les ports au LAN et ne pas utiliser de tunnel public.

## 1. Démarrer le backend local M4

```powershell
cd C:\Users\omama\OneDrive\Bureau\datathon\migration-reconnect\backend
$env:RECONNECT_M2_ZIP='C:\Users\omama\Downloads\RECONNECT_CAEN_ET_NORD_M2_DEMO_INTERNE_20261111_V1.zip'
$env:RECONNECT_FRONTEND_ORIGIN='http://127.0.0.1:5173'
& 'C:\Users\omama\OneDrive\Bureau\datathon\migration-reconnect-m1\.venv-m1\Scripts\python.exe' server.py
```

Le service doit annoncer `http://127.0.0.1:8765`. Vérification :

```powershell
Invoke-WebRequest http://127.0.0.1:8765/health -UseBasicParsing
```

## 2. Démarrer le frontend

```powershell
cd C:\Users\omama\OneDrive\Bureau\datathon\migration-reconnect\frontend
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

Ouvrir `http://127.0.0.1:5173`.

## 3. Parcours de démonstration

1. À l’ouverture, la carte se cadre automatiquement sur le territoire REAL (101 cellules) dès que le backend répond. « Voir la zone d’étude » permet de revenir à ce cadrage ; « Réessayer » relance le chargement si le backend était absent.
2. Garder « Ordre de vérification documentaire — exploratoire ».
3. Expliquer les catégories V1–V4 et leur caractère documentaire.
4. Cliquer une cellule rouge puis lire ses observations et pistes.
5. Préciser que les résultats R1–R4 sont non évaluables.
6. Passer à « Priorité écologique — non validée » : les 101 cellules deviennent grises.

## Mode TEST historique (interface masquée)

Le mode TEST (43 mailles pilotes Orne, couleurs synthétiques) n'est plus exposé dans
l'interface : la carte REAL 101 mailles est l'expérience principale. Toute
l'implémentation est conservée — remettre `TEST_MODE_UI_ENABLED` à `true` dans
`frontend/src/components/layout/ApplicationLayout.tsx` réactive les boutons
« Activer/Quitter le mode TEST », les badges et la navigation pilote.

Le contour historique du pilote (`frontend/public/data/pilot-boundary.geojson`)
porte `statut = en_attente` : sa géométrie n'est pas encore validée, il n'est
donc pas affiché en superposition sur le territoire REAL. Les données du pilote
restent disponibles en interne pour une future version validée.

## Limites à annoncer

- revue/démonstration locale uniquement ;
- aucune priorité écologique validée ;
- aucune recommandation de travaux ;
- zéro observation ne démontre pas une absence ;
- SRCE millésime 2014 et inventaires non exhaustifs ;
- catalogue M5 complet non disponible.

## Tests

```powershell
cd ..\backend
$env:RECONNECT_M2_ZIP='C:\Users\omama\Downloads\RECONNECT_CAEN_ET_NORD_M2_DEMO_INTERNE_20261111_V1.zip'
& 'C:\Users\omama\OneDrive\Bureau\datathon\migration-reconnect-m1\.venv-m1\Scripts\python.exe' -m unittest -v test_server.py

cd ..\frontend
npm.cmd run test:priorities
npm.cmd run typecheck
npm.cmd run build
```
