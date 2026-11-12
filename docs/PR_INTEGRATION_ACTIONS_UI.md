# Améliorer les diagnostics territoriaux et préparer les décisions d’étude M2

L’application affichait un classement documentaire et les pistes d’investigation
sans sélection opérationnelle explicite. Cette PR adapte le frontend/backend
existant pour lire les décisions canoniques du lot ACTIONS_ETUDE via les routes
M4 déjà présentes. Les 101 fiches sont raccordées dans le fonctionnement local
avec le lot final ; les clés territoire/grille/maille sont conservées.

La vue d’étude conserve 27 rouges, 33 orange, 9 jaunes et 32 grises. Le nouveau lot
porte 60 sélections principales d’étude A04 par maille, neuf orientations de
préservation et 32 décisions non évaluables. Les 165 pistes historiques restent
traçables. La fiche présente le diagnostic, les observations, l’action à étudier
et les conditions avant travaux ; les codes et la provenance sont accessibles
au clic. Le catalogue distingue pistes historiques et sélections courantes.
L’en-tête, le responsive, le cadrage Caen et le rendu des couleurs sont corrigés.

D/S et les statuts scientifiques restent inchangés et indéterminés/non évaluables.
Aucune intervention écologique n’est présentée comme un chantier validé. Aucun
calcul scientifique, contrat public ou verrou de diffusion n’est modifié.

Validation : 27 tests backend, tests frontend de priorités et d’actions, build
statique et parcours Chrome des quatre couleurs, de cinq largeurs et d’un clic
réel mobile. Les couleurs rendues sont vérifiées sans avertissement MapLibre.
Le build statique fonctionne avec les données publiques existantes, sans appel
à une API interne et sans décision d’action inventée.

**Périmètre de publication : code uniquement.** Les données publiques actuellement
déployées restent les anciens exports : 101 fiches et 165 pistes, sans les nouvelles
décisions. Le frontend/backend est préparé pour ces nouvelles actions, mais elles
ne seront pas visibles sur Vercel avant leur autorisation et leur publication
distincte. Une candidature minimisée est prête hors du répertoire public ; aucun
ZIP/GeoPackage interne ni nouvel export non autorisé n’est ajouté dans cette PR.
La procédure est décrite dans `docs/INTEGRATION_ACTIONS_UI_20261112.md`.

Cette PR vise la revue du code vers `main`. Aucune fusion ni modification de la
configuration Vercel n’est demandée ou effectuée par cette opération.
