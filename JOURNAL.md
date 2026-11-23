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
| 2026-11-23 | `rapports/2026-11-23.md` | Premier rapport généré en local avec `python3 veille.py` (run en cours). | Valider le format du rapport avant mise en production. |
| 2026-11-23 | `rapports/2026-11-23.md` | Rapport de veille généré : 15 candidat(s) retenu(s), 102 écarté(s), 6 alerte(s). | Exécution hebdomadaire (cron lundi 06h00 UTC ou manuel). |
| 2026-11-23 | `rapports/2026-11-23.md` | Rapport de veille généré : 8 candidat(s) retenu(s), 79 écarté(s), 0 alerte(s). | Exécution hebdomadaire (cron lundi 06h00 UTC ou manuel). |
