import json
from pathlib import Path
from fastapi import FastAPI, HTTPException

app = FastAPI()

# Chemin vers notre fichier de données
DATA_FILE = Path(__file__).parent / "data" / "zones.json"


@app.get("/")
def accueil():
    return {"message": "Bienvenue sur l'API Datathon Normandie"}


@app.get("/zones")
def obtenir_zones():

    with open(DATA_FILE, "r", encoding="utf-8") as fichier:
        zones = json.load(fichier)

    return zones

@app.get("/zones/{zone_id}")
def obtenir_zone(zone_id: int):

    with open(DATA_FILE, "r", encoding="utf-8") as fichier:
        zones = json.load(fichier)

    for zone in zones:
        if zone["id"] == zone_id:
            return zone

    raise HTTPException(
        status_code=404,
        detail="Zone introuvable"
    )