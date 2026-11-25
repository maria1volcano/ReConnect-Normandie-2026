"""Routeur M4 facultatif : données internes, lecture seule et boucle locale."""
import json
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

VERSION='caen6-priorites-etude-actions-20261112-1'
router=APIRouter(prefix='/__internal/m2/caen',tags=['M2 études indicatives'])
ALLOWED={'mailles.geojson','conflits.geojson','fiches_zones.json','actions_resultats.json','priorites_etude_interventions.json','pistes_investigation_trace.json'}
CACHE={}


def load(request,name):
    if request.client is None or request.client.host not in {'127.0.0.1','::1','::ffff:127.0.0.1'}:
        raise HTTPException(403,'Revue locale uniquement')
    if request.headers.get('forwarded')or request.headers.get('x-forwarded-for')or request.headers.get('sec-fetch-site')=='cross-site':
        raise HTTPException(403,'Diffusion par proxy non autorisée')
    root=os.environ.get('M2_CAEN_LOT_ROOT')
    if not root:raise HTTPException(503,'Lot non configuré')
    path=Path(root).resolve()/'demo_interne'/name
    try:
        key=(str(path),path.stat().st_mtime_ns)
        if key not in CACHE:
            data=json.loads(path.read_text(encoding='utf-8'))
            if len(CACHE)>20:CACHE.clear()
            CACHE[key]=(data,{f['maille_id']:f for f in data.get('fiches',[])})
        return CACHE[key]
    except(OSError,ValueError):raise HTTPException(503,'Lot interne invalide')


def fiches(request):
    doc,index=load(request,'fiches_zones.json')
    if doc.get('version_priorisation_etudes')!=VERSION or doc.get('classification_defaut')!='priorites_etude_interventions':
        raise HTTPException(409,'Version opérationnelle incompatible')
    return doc,index


def response(data):return JSONResponse(data,headers={'Cache-Control':'no-store, private','X-Content-Type-Options':'nosniff'})


@router.get('/fiches/{maille_id}')
def fiche(request:Request,maille_id:str,grid_version:str,territory_id:str):
    doc,index=fiches(request)
    if grid_version!=doc['scope']['grid_version']or territory_id!=doc['scope']['territory_id']:raise HTTPException(409,'Portée incompatible')
    if maille_id not in index:raise HTTPException(404,'Maille absente')
    return response(index[maille_id])


@router.get('/{name}')
def resource(request:Request,name:str):
    if name not in ALLOWED:raise HTTPException(404,'Ressource absente')
    fiches(request)
    return response(load(request,name)[0])
