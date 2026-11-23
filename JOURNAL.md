# JOURNAL — veille-modeles-locaux

Chaque étape faite sur le dépôt est consignée ici (date, fichier, raison).

| Date (UTC) | Fichier / zone | Étape | Raison |
|---|---|---|---|
| 2026-11-23 | `veille-modeles-locaux/` | Création du dossier racine du dépôt local. | Démarrage du projet demandé par l'utilisateur. |
| 2026-11-23 | (chat) | Arborescence et plan présentés à l'utilisateur, en attente d'accord avant toute écriture de code. | Contrainte explicite de l'utilisateur : ne rien écrire avant son accord, ne rien pousser sur GitHub sans accord explicite. |
| 2026-11-23 | (chat) | Accord reçu. Choix retenus : licences listées une par une dans `config.yaml` avec filtre `acceptee` (inconnue = refusée par défaut) ; comparaison chiffrée via Open LLM Leaderboard + LMArena, « non mesuré » sinon. | Décisions de l'utilisateur lors de la revue du plan. |
| 2026-11-23 | `config.yaml` | Règles écrites : budget 9 Go strict, 3–14 Md (petits 3–6 Md en surbrillance), licences avec filtre, modèles actuels, tâches, sources (Ollama /library, HF api gguf+mlx, classements via datasets-server), délai 2 s, User-Agent clair. | Fichier central de configuration demandé. |
| 2026-11-23 | `historique.json` | Semence avec les 5 LLM actuels + embeddings (statut « actuel »). | Pour que la veille ne re-signale pas les modèles déjà utilisés et puisse détecter leur disparition. |
| 2026-11-23 | `veille.py` | Script principal écrit : collecte polie (robots.txt, délai, UA), filtrage déterministe en fonctions pures, rapport FR (constat/cause/geste), historique, journal. | Cœur du dépôt demandé. |
| 2026-11-23 | `tests/test_filtrage.py` | 24 tests pytest écrits et passés (modèles fictifs : trop gros, licence NC, hors tranche, non installable, pas de français, catégorie « petit », « non mesuré », source indisponible). | Livrable « tests simples » demandé. |
| 2026-11-23 | `.github/workflows/veille-hebdo.yml` | Action écrite : cron `0 6 * * 1` + `workflow_dispatch`, Python 3.12, pip install requests pyyaml, run veille.py + pytest, commit auto du rapport. | Livrable « rapport hebdomadaire commité par l'Action » demandé. |
| 2026-11-23 | `README.md`, `.gitignore` | Mode d'emploi en français simple + ignore Python. | Livrables demandés. |
| 2026-11-23 | `rapports/2026-11-23.md` | Premier rapport généré en local avec `python3 veille.py` : 8 candidats retenus (dont 6 petits modèles 3–6 Md), 79 écartés avec raisons, 0 alerte, LMArena OK / Open LLM Leaderboard indisponible (indiqué dans le rapport). | Valider le format du rapport avant mise en production. |
| 2026-11-23 | `veille.py` | Corrections post-run : vérification directe des pages Ollama des modèles actuels (faux positifs d'alertes supprimés), scores arrondis, plafonds de requêtes HF (max 30 fiches, 60 tentatives), progression affichée, avertissements plafonnés à 20 dans le rapport. | Un premier run a montré des alertes « modèle actuel absent » fausses (top 25 seulement) et des boucles trop longues. |
| 2026-11-23 | `config.yaml` | Plafonds ajustés : `max_modeles_ollama: 25`, `max_modeles_hf: 100`, `max_fiches_hf: 30`, `max_termes_classements: 6`, `timeout_secondes: 15`. | Borner la durée d'un run (~10 min) pour rester confortable en GitHub Action. |
| 2026-11-23 | dépôt git local | `git init -b main` + commit initial (4146c7c) de tous les fichiers. **Aucun push** vers GitHub. | Le push reste soumis à l'accord explicite de l'utilisateur. |
| 2026-11-23 | `tests/` | `python3 -m pytest tests/ -q` -> 24 tests passés après chaque modification. | Qualité du filtrage déterministe. |
| 2026-11-23 | identité git | Identité du dépôt passée à `Zeelichisgood <Zeelichisgood@users.noreply.github.com>` + réécriture de l'auteur des 2 commits (rebase --root --reset-author). | Éviter de publier l'email local `…@macbookair.home` dans un dépôt public. |
| 2026-11-23 | GitHub | Dépôt public créé et poussé avec `gh repo create veille-modeles-locaux --public --source . --push` → https://github.com/Zeelichisgood/veille-modeles-locaux (branche `main`). | Mise en ligne autorisée explicitement par l'utilisateur. |
| 2026-11-23 | `.github/workflows/veille-hebdo.yml` | Fix : le message de commit multi-lignes du step "Committer" cassait le YAML (lignes en colonne 0) → remplacé par des `-m` séparés ; YAML revalidé, workflow bien enregistré (schedule + workflow_dispatch). | Le premier run push avait échoué ("workflow file issue") à cause de cette indentation. |
| 2026-11-23 | GitHub Actions | Run manuel déclenché (`gh workflow run veille-hebdo.yml`, run 45205235153) pour valider l'Action de bout en bout. | Validation avant le premier cron lundi 06h00 UTC. |
| 2026-11-23 | `rapports/2026-11-23.md` | Rapport de veille généré : 15 candidat(s) retenu(s), 102 écarté(s), 6 alerte(s). | Exécution hebdomadaire (cron lundi 06h00 UTC ou manuel). |
| 2026-11-23 | `rapports/2026-11-23.md` | Rapport de veille généré : 8 candidat(s) retenu(s), 79 écarté(s), 0 alerte(s). | Exécution hebdomadaire (cron lundi 06h00 UTC ou manuel). |
