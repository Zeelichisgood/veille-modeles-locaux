# veille-modeles-locaux

Veille hebdomadaire et automatique des **nouveaux modèles de langage utilisables en local** sur un
**Mac M1, 16 Go de RAM** (Ollama). Chaque semaine, un rapport indique quels modèles valent la peine
d'être testés, comparés à mes modèles actuels, et lesquels sont écartés (et pourquoi).

**Ce dépôt est public et ne contient aucune donnée personnelle, aucun nom de client, aucune clé API.**
Toutes les sources interrogées sont des API publiques en lecture seule.

---

## Comment ça marche, en simple

1. Chaque **mardi entre 3h et 6h du matin, heure française** (cron GitHub : mardi 03h00 UTC = 4h en hiver, 5h en été ; et sur demande manuelle), une **GitHub Action** exécute `veille.py`.
2. `veille.py` interroge les sources publiques :
   - la **bibliothèque Ollama** (`ollama.com/library`, pages publiques uniquement — `robots.txt` est respecté, avec un délai entre les requêtes et un User-Agent clair) ;
   - l'**API Hugging Face** (`huggingface.co/api/models`) : modèles récents et téléchargés, filtrés sur les dépôts **GGUF** ou **MLX** ;
   - les **classements ouverts** (LMArena / Chatbot Arena via son dataset public, Open LLM Leaderboard) en lecture seule, pour les scores.
3. Un **filtrage déterministe en Python** (aucun LLM dans l'Action) retient un modèle s'il :
   - fait **moins de 9 Go** en fichier quantifié (Q4_K_M ou équiv.) — au-delà, le Mac sature le swap ;
   - fait entre **3 et 14 milliards de paramètres** (les **3–6 Md** sont mis en surbrillance comme « petits modèles spécialisés », avec de la marge mémoire) ;
   - est **installable en local** : Ollama, ou GGUF, ou MLX ;
   - a une **licence qui autorise l'usage professionnel** (voir `config.yaml`) ;
   - annonce du **français** quand les langues sont connues.
4. Le rapport est écrit dans `rapports/AAAA-MM-JJ.md`, **commité automatiquement** par l'Action, et
   `historique.json` est mis à jour pour ne signaler que les **nouveautés**.
5. Si une source est indisponible, le rapport le dit (« source indisponible ») **au lieu d'échouer**.

## Arborescence

```text
veille-modeles-locaux/
├── README.md                      # ce fichier
├── JOURNAL.md                     # journal des étapes (date, fichier, raison)
├── config.yaml                    # TOUTES les règles modifiables (sans toucher au code)
├── historique.json                # modèles déjà vus (anti-doublon entre semaines)
├── veille.py                      # script principal (stdlib + requests + pyyaml)
├── obsidian_sync.py               # pont vers Obsidian (LECTURE SEULE par défaut)
├── tests/test_filtrage.py         # tests pytest du filtrage (modèles fictifs)
├── tests/test_obsidian_sync.py    # tests pytest du pont Obsidian
├── rapports/                      # un rapport par semaine : AAAA-MM-JJ.md
└── .github/workflows/veille-hebdo.yml   # l'Action (cron mardi 03h00 UTC = 3h–6h heure française + manuel)
```

## Le rapport hebdomadaire (`rapports/AAAA-MM-JJ.md`)

1. **Verdict en une ligne** — « Rien à tester cette semaine » ou « À tester : X » — avec constat / cause / geste.
2. **Tableau des modèles retenus** : nom, taille, paramètres, licence, date, langues, commande `ollama pull`, lien source.
3. **Comparaison tâche par tâche** avec mes modèles actuels (mistral-nemo 12B, qwen3.5 9B, qwen3 8B, phi4 14B, granite3.3 8B) : scores issus des classements publics **cités avec leur source** ; si aucune donnée fiable n'existe, le rapport écrit **« non mesuré »** — aucun chiffre n'est inventé.
4. **Modèles écartés**, une ligne chacun avec la raison (trop gros, licence non commerciale, pas de français…).
5. **Alertes** : suppression ou changement de licence d'un de mes modèles actuels.

## Changer les règles

Tout se passe dans **`config.yaml`**, sans modifier le code :

| Tu veux changer… | Où dans `config.yaml` |
|---|---|
| Le budget mémoire (taille max du fichier) | `budget_memoire.taille_fichier_max_go` |
| La tranche de paramètres (et la catégorie « petits modèles ») | `parametres.min_milliards` / `max_milliards` / `petit_modele_max_milliards` |
| Les licences acceptées (usage pro) | `licences.connues` — chaque licence a `acceptee: true/false` + une note ; `regle_licence_inconnue` règle le cas d'une licence inconnue (`refuser` par défaut, ou `signaler`) |
| Mes modèles actuels de référence | `modeles_actuels.llm` (+ `embeddings`) |
| Mes tâches | `taches` |
| Les sources, le délai entre requêtes, le User-Agent | `sources` |

## Lancer l'Action à la main

Sur GitHub : onglet **Actions** → « Veille hebdomadaire des modèles locaux » → **Run workflow**.
Le rapport de la journée est alors généré et commité automatiquement.

En local (pour tester) :

```bash
pip install requests pyyaml pytest
python3 veille.py                 # génère rapports/AAAA-MM-JJ.md (date du jour, UTC)
python3 veille.py --date 2026-11-30   # forcer une date
python3 -m pytest tests/ -q       # tests du filtrage
```

## Note Obsidian à chaque run

Chaque rapport `rapports/AAAA-MM-JJ.md` peut devenir une **note datée dans ton vault Obsidian**
(frontmatter `date`/`tags`/`source` + rapport complet) via `obsidian_sync.py`.

**Par défaut, le script est en lecture seule** sur le vault : il liste les notes existantes et
affiche ce qu'il écrirait, sans rien modifier. L'écriture n'est possible qu'avec
`obsidian.ecriture_autorisee: true` dans `config.yaml` **et** la commande `--apply`.

```bash
# Voir ce qui serait écrit (aucune écriture) :
python3 obsidian_sync.py

# Écrire les notes manquantes (seulement si ecriture_autorisee: true) :
python3 obsidian_sync.py --apply
```

Le vault n'étant pas lisible depuis la GitHub Action (elle tourne sur les serveurs de GitHub),
la synchro se fait **côté Mac** : une fois le rapport poussé, exécute sur ta machine :

```bash
git -C "chemin/vers/veille-modeles-locaux" pull && python3 "chemin/vers/veille-modeles-locaux/obsidian_sync.py" --apply
```

À planifier par exemple le mardi matin après 6h (cron local / launchd), ou à la main.
Avant cela, renseigne `obsidian.vault_path` dans `config.yaml` (chemin absolu de ton vault).

## Coût et confidentialité

- **0 €** : dépôt public GitHub = minutes GitHub Actions gratuites ; API publiques sans clé.
- **Aucune donnée personnelle** n'est collectée, transmise ou committée. Les éventuels jetons futurs
  passeraient exclusivement par les **secrets GitHub** (jamais écrits dans le dépôt).
- Les requêtes sont polies : `robots.txt` respecté, délai entre requêtes, User-Agent explicite
  (`veille-modeles-locaux/1.0 …`).

## Reprendre le projet

Voir **`JOURNAL.md`** : chaque étape y est consignée (date, fichier, raison).
