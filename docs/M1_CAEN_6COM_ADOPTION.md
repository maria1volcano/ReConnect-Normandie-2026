# Adoption M1 — grille Caen et cinq communes

M1 adopte pour l’intégration locale la grille géographique issue du lot M2 immuable
`RECONNECT_CAEN_ET_NORD_M2_DEMO_INTERNE_20261111_V1.zip`, empreinte SHA-256
`F1878207F370DC2A424898CF2DE89DB540D6EABAB43BD7E5F6C93BBF3C2FD3B4`.

- `grid_version` : `M1-CAEN-6COM-1KM2-FLAT-L93-O0-V1`
- territoire : Caen 14118, Ouistreham 14488, Bénouville 14060,
  Blainville-sur-Orne 14076, Colombelles 14167 et Hérouville-Saint-Clair 14327 ;
- 101 cellules, dont 34 intérieures et 67 fragments de bord ;
- EPSG:2154, flat-top, origine `(0,0)`, aire nominale 1 km² ;
- limites communales IGN ADMIN EXPRESS COG LATEST, Licence Ouverte 2.0 ;
- 66 identifiants hérités et 66 hexagones complets strictement identiques à la
  livraison cinq communes précédente.

Le script `analysis/validate_caen_6com_adoption.py` refait les contrôles depuis le
ZIP sans le modifier : empreinte, CRS, versions, validité, couverture, communes,
topologie, surfaces et compatibilité avec la grille 66.

Cette adoption vaut uniquement comme référence géographique interne pour la
démonstration locale. Elle ne constitue pas une autorisation de publication des
données M2, diagnostics, événements ou propositions.
