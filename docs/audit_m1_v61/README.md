# Annexes de la revue M1 → M2 du 8 novembre 2026

Le [rapport](../revue_scientifique_m1_m2_v61.md) distingue vérifications exécutées, déclarations M1 et décisions scientifiques restantes.

- `controles.json` : inventaire complet du snapshot M1 avec tailles/empreintes, environnement logiciel, intégrité et statistiques des CSV, contrôles des géométries, empreintes de génération, rejets du validateur M2, scénarios de grille et conservation des fichiers préexistants.
- `verifier_livraison.py` : script d'inspection des entrées en lecture seule ; il écrit uniquement le JSON demandé en deuxième argument. Il n'appelle aucun `main()` M1/M2, n'effectue aucune commande de mutation Git et ne produit aucun GeoJSON ou GeoPackage.

Le script utilise le code M2 du répertoire courant, y compris les modifications locales. `m2_audited_code_sha256` et `m2_initial_status` identifient l'état effectivement audité ; le SHA de HEAD seul ne suffit pas à reproduire cet état. Les empreintes des fichiers M1 figurent dans `inventory`. Les contrôles de préservation de cette exécution sont comparés à un manifeste temporaire des fichiers préexistants, pris avant l'ajout du rapport ; ils ne constituent pas une signature externe.

## Reproduire les contrôles sans modifier les données M1

Depuis la racine du dépôt, avec un environnement satisfaisant `analysis/requirements.txt` et la référence Git disponible :

```sh
audit_snapshot_dir=$(mktemp -d)
git archive fc76d6230994af9aef27f42bb42e0374cd0c8251 | tar -xf - -C "$audit_snapshot_dir"
PYTHONDONTWRITEBYTECODE=1 python docs/audit_m1_v61/verifier_livraison.py "$audit_snapshot_dir" /tmp/reconnect_m1_reverification.json
```

Ne pas installer simultanément les exigences M1 et M2 : leurs contraintes pandas sont incompatibles. L'exécution initiale a utilisé un environnement temporaire M2 ; les versions exactes sont enregistrées dans le JSON.

Un troisième argument facultatif accepte un manifeste de préservation externe de forme `{files: {chemin: sha256}, status, head, branch}`. Sans cet argument, le script prend son propre état initial en mémoire. Le chemin de sortie doit être un nouveau fichier d'audit, hors de l'archive M1 et distinct des entrées du projet.

Les scénarios 0,5/1/2 km², le demi-pas d'ancrage et les 1 000 subdivisions par côté de bbox sont des expériences numériques, sans adoption d'un nouveau support ni de paramètres écologiques. Les exports CSV sont contrôlés comme tables livrées : les mesures ne sont pas recalculées depuis les sources manquantes. Les tests synthétiques historiques R1–R4 et D/S ne sont pas relancés.
