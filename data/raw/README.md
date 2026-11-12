# Données brutes locales — M1 Step 2

Ces fichiers sont des acquisitions officielles conservées sans modification. Les archives et extractions volumineuses sont ignorées par Git ; ce README assure la traçabilité. Date d'acquisition : 2026-11-03.

| Dossier/fichier | Source exacte | Taille | SHA-256 | Licence / état |
|---|---|---:|---|---|
| `tvb_srce_normandie/reservoirs_srce_normandie_source.zip` | `https://www.data.gouv.fr/api/1/datasets/r/c6e90e56-421d-45b3-9457-1c9a19962633` | 27 080 588 | `12BBABAB26A594363B8F8DCB111AC43745E5829D4DCAEC33F5B475F5127A6E7C` | DREAL Normandie, Licence Ouverte 2.0, téléchargé et inspecté |
| `tvb_srce_normandie/corridors_basse_normandie/corridors_srce_basse_normandie_source.zip` | `https://www.data.gouv.fr/api/1/datasets/r/e9c69c04-02bd-459b-9821-3ffe70360aae` | 19 757 409 | `9F8AB6B025C09163F77EE567E83DF946B68153C463AD26A0D39DDAD84D994AFB` | DREAL Normandie, Licence Ouverte 2.0, téléchargé et inspecté |
| `bdtopo_routes/routes_orne_estuaire_bbox.geojson` | `https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=BDTOPO_V3%3Atroncon_de_route&OUTPUTFORMAT=application%2Fjson&SRSNAME=EPSG%3A4326&BBOX=-0.28%2C49.20%2C-0.22%2C49.26%2CEPSG%3A4326&COUNT=5000` | 5 739 817 | `133992B47A34FF4C840FB114B6A21F0EED2D331C55F089B6A45532B8E4A3ADA2` | IGN, Licence Ouverte 2.0, téléchargé et inspecté |
| `ocsge_d014_2023/OCS-GE_2-0__GPKG_LAMB93_D014_2023-01-01.7z` | `https://data.geopf.fr/telechargement/download/OCSGE/OCS-GE_2-0__GPKG_LAMB93_D014_2023-01-01/OCS-GE_2-0__GPKG_LAMB93_D014_2023-01-01.7z` | 138 290 682 | `F1DA3C0C5978988C536C5ACB5C9173E519D1271BD88EE45CBCEA1F54991D7CAC` | IGN/DGALN, Licence Ouverte 2.0, téléchargé et inspecté |

Les sous-dossiers `extracted/` sont des décompressions byte-for-byte des archives, pas des sorties harmonisées. Ne pas les modifier. Toute transformation future doit écrire sous `data/processed/`.

## Acquisitions complémentaires — Step 5

Date d'acquisition : 3 novembre 2026. Ces fichiers restent ignorés par Git et ne sont jamais modifiés par les scripts.

| Dossier/fichier | Source exacte | Taille | SHA-256 | Licence / état |
|---|---|---:|---|---|
| `bdhaie_pilot/haies_pilot.geojson` | WFS IGN `BDTOPO_V3:haie`, bbox pilote WGS84 | 755 367 | `B6838E1A8D1F118AA75227A28167071BB863177D9A3634949FE97A94F433FE27` | Licence Ouverte 2.0 ; extrait borné, 1 181 lignes |
| `sipaf/Tous_les_PAF.gpkg` | `https://passagesfaune.fr/geonature/api/media/exports/schedules/Tous_les_PAF.gpkg` | 1 015 808 | `53A2E899985854888AEFF0E818CACE78FB4A1F471466B28C93E5B34A7A1345F3` | Licence Ouverte 2.0 ; export national courant, 2 457 objets, aucun dans le pilote ; inventaire non exhaustif |
| `cartofriches/friches-surfaces.gpkg` | `https://static.data.gouv.fr/resources/sites-references-dans-cartofriches/20261007-122403/friches-surfaces.gpkg` | 70 332 416 | `5325E49E0096613903697FD4077D646B311AD51F5CAFBC75D3EB2A17453DA386` | Cerema, Licence Ouverte 2.0 ; 36 238 objets nationaux, 3 dans le pilote ; inventaire non exhaustif |
| `zones_humides/zones_humides_pilot.gml` | WFS DREAL `ms:drealnorm_zh_s_r28`, bbox pilote EPSG:2154 | 623 194 | `1B88C80EBD45098BE435E3CD53E31EB30985566E29B51585D3C699AE730C3CA2` | Licence Ouverte 2.0 ; extrait borné, 165 polygones ; inventaires hétérogènes |

Le service DREAL n'accepte que les formats GML annoncés par ses capacités : une première demande GeoJSON a échoué, puis l'extrait borné GML a été acquis en EPSG:2154. PRAM reste soumis à extraction autorisée et EPFN à clarification de licence/ressource.
