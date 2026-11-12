# Préparation opérationnelle — fichiers nouveaux uniquement

Voir le [compte rendu en huit points](../deblocage_operationnel_m1_m2_v61.md).

- `diagnostic_paires.json` conserve les 97 paires non vides sur les 903 testées pour chacune des deux représentations de grille, ainsi que les résultats des 16 contrôles ciblés. Les autres paires sont disjointes. Aucun CSV ni scénario de taille de maille n'est réaudité.
- `diagnostiquer_paires.py` permet de reproduire le diagnostic et les contre-exemples du prototype, sans modifier les entrées ni appeler les pipelines réels. La sortie doit être nouvelle.
- `grid_overlap.proposition.patch` décrit le changement recommandé dans `analysis/validate_inputs.py`. **Il n'a pas été appliqué au dépôt.** Le budget numérique est une convention d'ingénierie proposée, pas une borne d'erreur garantie par GEOS ; la constante M2 n'est pas augmentée.
- `verification_correctif.json` enregistre le contrôle supplémentaire effectué sur une copie temporaire du validateur exact proposé : comparaison aux cas ciblés, avertissement numérique et garde de lacune. Les empreintes identifient le code original et proposé ; ce contrôle n'est pas la suite SIG d'une future intégration.
- Les deux configurations `.proposition.json` sont acceptées par les parseurs existants. Leurs champs correspondent aux schémas documentés M1 ; leur inspection sur les GeoPackages réels reste nécessaire. Les couvertures sont inconnues et aucune distance de précision n'est renseignée.

Depuis la racine, avec l'environnement M2 et un extrait du commit M1 `fc76d6230994af9aef27f42bb42e0374cd0c8251` :

```sh
PYTHONDONTWRITEBYTECODE=1 python docs/deblocage_m1_m2_v61/diagnostiquer_paires.py /chemin/du/snapshot /tmp/nouveau_diagnostic_paires.json
git apply --check docs/deblocage_m1_m2_v61/grid_overlap.proposition.patch
```

La seconde commande contrôle seulement l'applicabilité du diff. N'utiliser aucune commande d'application avant la décision demandée par le périmètre de cette étape. La sauvegarde intégrale, le clone/worktree, la fusion et les exports SIG décrits dans le compte rendu sont **des procédures futures, non exécutées**. Aucun message n'a été envoyé à M1.
