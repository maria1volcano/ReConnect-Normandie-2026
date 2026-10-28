from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def accueil():
    return {"message": "Bienvenue sur l'API Dataaaaathon Normandie"}

@app.get("/zones")
def obtenir_zones():
    zones = [
        {
            "id": 1,
            "nom": "Zone test A",
            "pollution_lumineuse": 75,
            "biodiversite": 40
        },
        {
            "id": 2,
            "nom": "Zone test B",
            "pollution_lumineuse": 30,
            "biodiversite": 80
        }
    ]

    return zones