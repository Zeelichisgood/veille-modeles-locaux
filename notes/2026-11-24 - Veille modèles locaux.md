---
date: 2026-11-24
source: rapports/2026-11-24.md (github.com/Zeelichisgood/veille-modeles-locaux)
tags: [veille, modèles-locaux]
type: veille-modeles-locaux
---

# Veille modèles locaux — rapport du 2026-11-24

> Généré automatiquement par `veille.py` (GitHub Action, chaque mardi entre 3h et 6h heure française, plus déclenchement manuel). Aucune donnée personnelle, aucune clé. Sources publiques en lecture seule. Machine cible : Mac M1 16 Go, budget 8 Go / modèle chargé, fichier quantifié < 9 Go, 3–14 Md de paramètres.

## Verdict

**À tester : `William-WSDS/Qwen3.5-9B-GGUF`, `William-WSDS/Qwen3.5-4B-GGUF`, `mradermacher/JiRackUltra_7b-GGUF`**

- **Constat** : 3 modèle(s) nouveau(x) passe(nt) tous les filtres (taille < 9.0 Go, 3–14 Md, licence acceptée, installable en local).
- **Cause** : ces modèles sont absents de `historique.json` et ils correspondent à la tranche visée pour la machine (8 Go utiles, contexte 8 192 jetons).
- **Geste** : les tirer (`ollama pull ...` ou dépôt GGUF/MLX), puis les tester sur les 7 tâches de `config.yaml` avec une note de 9 000 caractères ; garder ceux qui battent mistral-nemo 12B / qwen3.5 9B sans inventer ni ralentir.

## 1. Modèles retenus (nouveautés de la semaine)

| Modèle | Taille fichier | Paramètres | Licence | Date | Langues annoncées | Installation | Source |
|---|---|---|---|---|---|---|---|
| `William-WSDS/Qwen3.5-9B-GGUF` | 5.83 Go | 9 Md | apache-2.0 | 2026-11-24 | non précisé | `GGUF — voir le lien source` | [source](https://huggingface.co/William-WSDS/Qwen3.5-9B-GGUF) |
| `mradermacher/JiRackUltra_7b-GGUF` | 4.68 Go | 7 Md | mit | 2026-11-24 | en, zh, ja, ko, fr, es, pt, de, it, ru, ar, vi, th | `GGUF — voir le lien source` | [source](https://huggingface.co/mradermacher/JiRackUltra_7b-GGUF) |

### ⭐ Petits modèles spécialisés (3–6 Md) — marge mémoire confortable

| Modèle | Taille fichier | Paramètres | Licence | Date | Langues annoncées | Installation | Source |
|---|---|---|---|---|---|---|---|
| `William-WSDS/Qwen3.5-4B-GGUF` | 2.82 Go | 4 Md | apache-2.0 | 2026-11-24 | non précisé | `GGUF — voir le lien source` | [source](https://huggingface.co/William-WSDS/Qwen3.5-4B-GGUF) |

## 2. Comparaison avec mes modèles actuels (tâche par tâche)

#### `William-WSDS/Qwen3.5-9B-GGUF` — comparaison avec mes modèles actuels

- **LMArena — Chatbot Arena (texte)** : score 1543.9, rang 14 (publié le 2026-11-22) — source : `lmarena-ai/leaderboard-dataset` (lecture seule).
- **Open LLM Leaderboard** : non mesuré (aucun score publié trouvé pour ce modèle).

| Tâche | Ce candidat | Mes modèles actuels (référence) | Source |
|---|---|---|---|
| Titrer et synthétiser une note en français, format imposé, sans rien inventer | non mesuré | mistral-nemo : 1428.7 (LMArena — Chatbot Arena (texte)) ; qwen3.5 : 1543.9 (LMArena — Chatbot Arena (texte)) ; qwen3 : 1484.9 (LMArena — Chatbot Arena (texte)) ; phi4 : 1211.4 (LMArena — Chatbot Arena (texte)) | classements publics |
| Extraire décisions, actions, chiffres et dates d'une note, avec citation exacte | non mesuré | mistral-nemo : 1428.7 (LMArena — Chatbot Arena (texte)) ; qwen3.5 : 1543.9 (LMArena — Chatbot Arena (texte)) ; qwen3 : 1484.9 (LMArena — Chatbot Arena (texte)) ; phi4 : 1211.4 (LMArena — Chatbot Arena (texte)) | classements publics |
| Classer et trier des notes (catégories, niveau de confidentialité) | non mesuré | mistral-nemo : 1428.7 (LMArena — Chatbot Arena (texte)) ; qwen3.5 : 1543.9 (LMArena — Chatbot Arena (texte)) ; qwen3 : 1484.9 (LMArena — Chatbot Arena (texte)) ; phi4 : 1211.4 (LMArena — Chatbot Arena (texte)) | classements publics |
| Fusionner plusieurs notes proches en une fiche cohérente | non mesuré | mistral-nemo : 1428.7 (LMArena — Chatbot Arena (texte)) ; qwen3.5 : 1543.9 (LMArena — Chatbot Arena (texte)) ; qwen3 : 1484.9 (LMArena — Chatbot Arena (texte)) ; phi4 : 1211.4 (LMArena — Chatbot Arena (texte)) | classements publics |
| Répondre à une question transversale à partir de 2 ou 3 notes | non mesuré | mistral-nemo : 1428.7 (LMArena — Chatbot Arena (texte)) ; qwen3.5 : 1543.9 (LMArena — Chatbot Arena (texte)) ; qwen3 : 1484.9 (LMArena — Chatbot Arena (texte)) ; phi4 : 1211.4 (LMArena — Chatbot Arena (texte)) | classements publics |
| Français courant, contenu anglais fréquent, vocabulaire stratégie/vente/finance | non mesuré | mistral-nemo : 1428.7 (LMArena — Chatbot Arena (texte)) ; qwen3.5 : 1543.9 (LMArena — Chatbot Arena (texte)) ; qwen3 : 1484.9 (LMArena — Chatbot Arena (texte)) ; phi4 : 1211.4 (LMArena — Chatbot Arena (texte)) | classements publics |
| Critères éliminatoires : lenteur (> 3 min pour 9 000 caractères), inventions, mélange de langues, format non respecté | non mesuré | mistral-nemo : 1428.7 (LMArena — Chatbot Arena (texte)) ; qwen3.5 : 1543.9 (LMArena — Chatbot Arena (texte)) ; qwen3 : 1484.9 (LMArena — Chatbot Arena (texte)) ; phi4 : 1211.4 (LMArena — Chatbot Arena (texte)) | classements publics |

> Aucun chiffre n'est inventé : « non mesuré » signifie qu'aucun benchmark public fiable n'a été trouvé pour cette tâche. À confirmer par un test local avant adoption.

#### `William-WSDS/Qwen3.5-4B-GGUF` — comparaison avec mes modèles actuels

- **LMArena — Chatbot Arena (texte)** : score 1543.9, rang 14 (publié le 2026-11-22) — source : `lmarena-ai/leaderboard-dataset` (lecture seule).
- **Open LLM Leaderboard** : non mesuré (aucun score publié trouvé pour ce modèle).

| Tâche | Ce candidat | Mes modèles actuels (référence) | Source |
|---|---|---|---|
| Titrer et synthétiser une note en français, format imposé, sans rien inventer | non mesuré | mistral-nemo : 1428.7 (LMArena — Chatbot Arena (texte)) ; qwen3.5 : 1543.9 (LMArena — Chatbot Arena (texte)) ; qwen3 : 1484.9 (LMArena — Chatbot Arena (texte)) ; phi4 : 1211.4 (LMArena — Chatbot Arena (texte)) | classements publics |
| Extraire décisions, actions, chiffres et dates d'une note, avec citation exacte | non mesuré | mistral-nemo : 1428.7 (LMArena — Chatbot Arena (texte)) ; qwen3.5 : 1543.9 (LMArena — Chatbot Arena (texte)) ; qwen3 : 1484.9 (LMArena — Chatbot Arena (texte)) ; phi4 : 1211.4 (LMArena — Chatbot Arena (texte)) | classements publics |
| Classer et trier des notes (catégories, niveau de confidentialité) | non mesuré | mistral-nemo : 1428.7 (LMArena — Chatbot Arena (texte)) ; qwen3.5 : 1543.9 (LMArena — Chatbot Arena (texte)) ; qwen3 : 1484.9 (LMArena — Chatbot Arena (texte)) ; phi4 : 1211.4 (LMArena — Chatbot Arena (texte)) | classements publics |
| Fusionner plusieurs notes proches en une fiche cohérente | non mesuré | mistral-nemo : 1428.7 (LMArena — Chatbot Arena (texte)) ; qwen3.5 : 1543.9 (LMArena — Chatbot Arena (texte)) ; qwen3 : 1484.9 (LMArena — Chatbot Arena (texte)) ; phi4 : 1211.4 (LMArena — Chatbot Arena (texte)) | classements publics |
| Répondre à une question transversale à partir de 2 ou 3 notes | non mesuré | mistral-nemo : 1428.7 (LMArena — Chatbot Arena (texte)) ; qwen3.5 : 1543.9 (LMArena — Chatbot Arena (texte)) ; qwen3 : 1484.9 (LMArena — Chatbot Arena (texte)) ; phi4 : 1211.4 (LMArena — Chatbot Arena (texte)) | classements publics |
| Français courant, contenu anglais fréquent, vocabulaire stratégie/vente/finance | non mesuré | mistral-nemo : 1428.7 (LMArena — Chatbot Arena (texte)) ; qwen3.5 : 1543.9 (LMArena — Chatbot Arena (texte)) ; qwen3 : 1484.9 (LMArena — Chatbot Arena (texte)) ; phi4 : 1211.4 (LMArena — Chatbot Arena (texte)) | classements publics |
| Critères éliminatoires : lenteur (> 3 min pour 9 000 caractères), inventions, mélange de langues, format non respecté | non mesuré | mistral-nemo : 1428.7 (LMArena — Chatbot Arena (texte)) ; qwen3.5 : 1543.9 (LMArena — Chatbot Arena (texte)) ; qwen3 : 1484.9 (LMArena — Chatbot Arena (texte)) ; phi4 : 1211.4 (LMArena — Chatbot Arena (texte)) | classements publics |

> Aucun chiffre n'est inventé : « non mesuré » signifie qu'aucun benchmark public fiable n'a été trouvé pour cette tâche. À confirmer par un test local avant adoption.

#### `mradermacher/JiRackUltra_7b-GGUF` — comparaison avec mes modèles actuels

- **LMArena — Chatbot Arena (texte)** : non mesuré (aucun score publié trouvé pour ce modèle).
- **Open LLM Leaderboard** : non mesuré (aucun score publié trouvé pour ce modèle).

| Tâche | Ce candidat | Mes modèles actuels (référence) | Source |
|---|---|---|---|
| Titrer et synthétiser une note en français, format imposé, sans rien inventer | non mesuré | mistral-nemo : 1428.7 (LMArena — Chatbot Arena (texte)) ; qwen3.5 : 1543.9 (LMArena — Chatbot Arena (texte)) ; qwen3 : 1484.9 (LMArena — Chatbot Arena (texte)) ; phi4 : 1211.4 (LMArena — Chatbot Arena (texte)) | classements publics |
| Extraire décisions, actions, chiffres et dates d'une note, avec citation exacte | non mesuré | mistral-nemo : 1428.7 (LMArena — Chatbot Arena (texte)) ; qwen3.5 : 1543.9 (LMArena — Chatbot Arena (texte)) ; qwen3 : 1484.9 (LMArena — Chatbot Arena (texte)) ; phi4 : 1211.4 (LMArena — Chatbot Arena (texte)) | classements publics |
| Classer et trier des notes (catégories, niveau de confidentialité) | non mesuré | mistral-nemo : 1428.7 (LMArena — Chatbot Arena (texte)) ; qwen3.5 : 1543.9 (LMArena — Chatbot Arena (texte)) ; qwen3 : 1484.9 (LMArena — Chatbot Arena (texte)) ; phi4 : 1211.4 (LMArena — Chatbot Arena (texte)) | classements publics |
| Fusionner plusieurs notes proches en une fiche cohérente | non mesuré | mistral-nemo : 1428.7 (LMArena — Chatbot Arena (texte)) ; qwen3.5 : 1543.9 (LMArena — Chatbot Arena (texte)) ; qwen3 : 1484.9 (LMArena — Chatbot Arena (texte)) ; phi4 : 1211.4 (LMArena — Chatbot Arena (texte)) | classements publics |
| Répondre à une question transversale à partir de 2 ou 3 notes | non mesuré | mistral-nemo : 1428.7 (LMArena — Chatbot Arena (texte)) ; qwen3.5 : 1543.9 (LMArena — Chatbot Arena (texte)) ; qwen3 : 1484.9 (LMArena — Chatbot Arena (texte)) ; phi4 : 1211.4 (LMArena — Chatbot Arena (texte)) | classements publics |
| Français courant, contenu anglais fréquent, vocabulaire stratégie/vente/finance | non mesuré | mistral-nemo : 1428.7 (LMArena — Chatbot Arena (texte)) ; qwen3.5 : 1543.9 (LMArena — Chatbot Arena (texte)) ; qwen3 : 1484.9 (LMArena — Chatbot Arena (texte)) ; phi4 : 1211.4 (LMArena — Chatbot Arena (texte)) | classements publics |
| Critères éliminatoires : lenteur (> 3 min pour 9 000 caractères), inventions, mélange de langues, format non respecté | non mesuré | mistral-nemo : 1428.7 (LMArena — Chatbot Arena (texte)) ; qwen3.5 : 1543.9 (LMArena — Chatbot Arena (texte)) ; qwen3 : 1484.9 (LMArena — Chatbot Arena (texte)) ; phi4 : 1211.4 (LMArena — Chatbot Arena (texte)) | classements publics |

> Aucun chiffre n'est inventé : « non mesuré » signifie qu'aucun benchmark public fiable n'a été trouvé pour cette tâche. À confirmer par un test local avant adoption.

## 3. Modèles écartés (une ligne par raison)

- `inkling-2-mini:26b-a5b-iq4_NL` (ollama) — trop gros : 18.0 Go >= 9.0 Go (budget mémoire) ; hors tranche : 26.0 Md (attendu 3.0–14.0 Md).
- `mradermacher/BLIP-Live-Gemma-i1-GGUF` (huggingface) — trop gros : 16.8 Go >= 9.0 Go (budget mémoire) ; nombre de paramètres non déterminé ; licence 'cc-by-nc-4.0' non acceptée pour un usage pro (Non commerciale : interdite pour un usage professionnel.) ; pas de français annoncé (langues: en).
- `mradermacher/WeMM-Ecom-9B-i1-GGUF` (huggingface) — licence inconnue (règle par défaut : refuser).
- `mradermacher/WeMM-Ecom-9B-GGUF` (huggingface) — pas de français annoncé (langues: zh, en).
- `bloomer010/Ling-3.2-air-REAP-408-GGUF` (huggingface) — trop gros : 60.43 Go >= 9.0 Go (budget mémoire) ; nombre de paramètres non déterminé.
- `mradermacher/MiMo-V2.6-Flash-RL-heretic-GGUF` (huggingface) — nombre de paramètres non déterminé ; pas de français annoncé (langues: en).
- `mradermacher/WeMM-Ecom-4B-GGUF` (huggingface) — licence inconnue (règle par défaut : refuser).
- `axom-ai/axomai-brain-progya-8b` (huggingface) — licence 'other' non acceptée pour un usage pro (Licence non reconnue : refusée par prudence.) ; pas de français annoncé (langues: as, en).
- `MouseWurX/Riker-89Bob-A6B-Flash-Next-REAP70-GGUF` (huggingface) — trop gros : 45.01 Go >= 9.0 Go (budget mémoire) ; licence 'other' non acceptée pour un usage pro (Licence non reconnue : refusée par prudence.).
- `respinosamena/Thirty-30M-Instruct-GGUF` (huggingface) — nombre de paramètres non déterminé ; pas de français annoncé (langues: en).
- `mradermacher/AH-Mechanic-1-4B-i1-GGUF` (huggingface) — pas de français annoncé (langues: en).
- `patrickbdevaney/GLM-5.3-Flash-prune-vs-quant-matched-bytes` (huggingface) — trop gros : 106.62 Go >= 9.0 Go (budget mémoire) ; nombre de paramètres non déterminé.
- `nandangowda/supermart-slm` (huggingface) — nombre de paramètres non déterminé ; licence 'other' non acceptée pour un usage pro (Licence non reconnue : refusée par prudence.) ; pas de français annoncé (langues: en).
- `prithivMLmods/Qwen3.8-Flash-Next-abliterated-MXFP4-MoE-GGUF` (huggingface) — trop gros : 124.05 Go >= 9.0 Go (budget mémoire) ; nombre de paramètres non déterminé ; licence 'other' non acceptée pour un usage pro (Licence non reconnue : refusée par prudence.) ; pas de français annoncé (langues: en).
- `prithivMLmods/CCORE-Web-Coder-4B-MTP-GGUF` (huggingface) — pas de français annoncé (langues: en).
- `kingjones777/Zenotron-Mini-0.5-Multilingual-SuperRoc-GGUF` (huggingface) — trop gros : 19.7 Go >= 9.0 Go (budget mémoire) ; nombre de paramètres non déterminé.
- `Kujira/Inkling-2-Mini-CHiPS-Abliterated-GGUF` (huggingface) — trop gros : 22.87 Go >= 9.0 Go (budget mémoire) ; nombre de paramètres non déterminé.
- `William-WSDS/Qwen3.8-27B-GGUF` (huggingface) — trop gros : 17.01 Go >= 9.0 Go (budget mémoire) ; hors tranche : 27.0 Md (attendu 3.0–14.0 Md).
- `mradermacher/BLIP-Live-GGUF` (huggingface) — trop gros : 21.71 Go >= 9.0 Go (budget mémoire) ; nombre de paramètres non déterminé ; licence 'cc-by-nc-4.0' non acceptée pour un usage pro (Non commerciale : interdite pour un usage professionnel.) ; pas de français annoncé (langues: en).
- `mradermacher/MFANN-SFT-GGUF` (huggingface) — nombre de paramètres non déterminé ; licence inconnue (règle par défaut : refuser) ; pas de français annoncé (langues: en).
- `mradermacher/Juliet-Chat-mini-GGUF` (huggingface) — nombre de paramètres non déterminé ; pas de français annoncé (langues: en).
- `mradermacher/MT3-Gen5-GP-gemma-2-RAv0.1E-9B_v1-GGUF` (huggingface) — licence inconnue (règle par défaut : refuser) ; pas de français annoncé (langues: en).
- `mradermacher/dqnGPT-v1-GGUF` (huggingface) — nombre de paramètres non déterminé ; pas de français annoncé (langues: en).
- `fijam/ik_llama-IQ4_NT` (huggingface) — trop gros : 14.48 Go >= 9.0 Go (budget mémoire) ; nombre de paramètres non déterminé ; licence 'llama3.1' non listée dans config.yaml (règle par défaut : refuser).
- `Harfusha/local-ai-hub-preprocess-qwen25-coder-3b` (huggingface) — licence 'other' non acceptée pour un usage pro (Licence non reconnue : refusée par prudence.).

## 4. Alertes sur mes modèles actuels

- Aucune alerte : tous les modèles actuels sont toujours présents.

## 5. Sources interrogées cette semaine

| Source | Statut | Détail |
|---|---|---|
| Ollama (ollama.com/library) | ✅ OK | 58 version(s) de modèles examinée(s) |
| Hugging Face (api/models, gguf + mlx) | ✅ OK | 30 dépôt(s) examiné(s) |
| Classements ouverts (LMArena, Open LLM Leaderboard) | ✅ OK | 4 score(s) trouvé(s) pour 6 terme(s) |

Avertissements :
- Classement 'Open LLM Leaderboard' : indisponible (HTTPError: 500 Server Error: Internal Server Error for url: https://datasets-server.huggingface.co/filter?dataset=open-llm-leaderboard%2Fresults&config=default&split=train&where=%22model_name%22+ILIKE+%27%25granite3.%25%27&offset=0&length=20)

---
*Rapport généré le 2026-11-24 (UTC) par `veille.py`. Les scores cités proviennent de classements publics en lecture seule ; « non mesuré » = aucune donnée fiable trouvée. Aucun chiffre n'est estimé ou inventé.*
