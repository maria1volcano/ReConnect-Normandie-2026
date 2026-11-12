# Datathon-normandie-2026


# Backend — ReConnect Normandie

API FastAPI du projet ReConnect Normandie.

## Installation

Depuis le dossier backend :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Démarrage

```bash
uvicorn main:app --reload
```

## Accès

- Documentation : http://127.0.0.1:8000/docs
- Santé du serveur : http://127.0.0.1:8000/health
- Zones TEST : http://127.0.0.1:8000/zone

## Données

Les données actuelles sont fictives (TEST).
Elles seront remplacées par des exports JSON/GeoJSON validés.

## Technologies

Python, FastAPI, Uvicorn.
