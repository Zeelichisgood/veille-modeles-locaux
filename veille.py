#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
veille.py — Veille hebdomadaire des nouveaux modèles de langage utilisables
en local sur un Mac M1 16 Go (Ollama).

Pipeline (aucun LLM n'est appelé ici, tout est déterministe) :
  1. charger la configuration (config.yaml) et l'historique (historique.json) ;
  2. interroger les sources publiques en lecture seule (bibliothèque Ollama,
     API Hugging Face, classements ouverts) avec un User-Agent clair, un délai
     entre les requêtes et le respect de robots.txt ;
  3. filtrer les modèles avec des règles déterministes (taille du fichier
     quantifié, nombre de paramètres, licence, mode d'installation, langues) ;
  4. générer le rapport rapports/AAAA-MM-JJ.md, mettre à jour historique.json
     et consigner l'étape dans JOURNAL.md.

Si une source est indisponible, le rapport l'indique au lieu d'échouer.
Aucune donnée personnelle n'est collectée ou transmise. Aucune clé API requise.

Dépendances : requests, pyyaml.  Usage :  python3 veille.py [--date AAAA-MM-JJ]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import quote, urlsplit

import requests
import yaml

RACINE = Path(__file__).resolve().parent

# =====================================================================
# Configuration et historique
# =====================================================================


def charger_config(chemin: Path) -> dict:
    """Charge config.yaml. Lève une erreur claire si le fichier est illisible."""
    with open(chemin, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not isinstance(cfg, dict):
        raise ValueError(f"{chemin} ne contient pas un dictionnaire YAML valide.")
    return cfg


def charger_historique(chemin: Path) -> dict:
    """Charge historique.json ; renvoie un historique vierge s'il n'existe pas."""
    if not chemin.exists():
        return {"version": 1, "derniere_mise_a_jour": None, "modeles": {}}
    with open(chemin, "r", encoding="utf-8") as f:
        return json.load(f)


def sauvegarder_historique(chemin: Path, hist: dict) -> None:
    """Écrit historique.json proprement (UTF-8, indenté, trié pour des diffs lisibles)."""
    hist["modeles"] = dict(sorted(hist["modeles"].items()))
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(hist, f, ensure_ascii=False, indent=2)
        f.write("\n")


# =====================================================================
# Modèle de données
# =====================================================================


@dataclass
class Modele:
    """Un modèle candidat, normalisé, quelle que soit la source."""

    source: str                                   # "ollama" | "huggingface"
    nom: str                                      # nom de base (ex. "qwen3")
    tag: Optional[str] = None                     # tag Ollama ou id HF
    source_url: str = ""
    taille_go: Optional[float] = None             # taille du fichier quantifié visé, en Go
    parametres_milliards: Optional[float] = None  # ex. 8.0 pour 8B
    licence: Optional[str] = None                 # ex. "apache-2.0"
    langues: list = field(default_factory=list)   # langues annoncées (vide = non précisé)
    formats: list = field(default_factory=list)   # ["ollama"], ["gguf"], ["mlx"]...
    quantification: Optional[str] = None          # ex. "Q4_K_M"
    date_modification: Optional[str] = None
    commande_pull: Optional[str] = None           # ex. "ollama pull qwen3:8b"
    description: str = ""

    @property
    def cle(self) -> str:
        """Clé unique utilisée dans historique.json (anti-doublon)."""
        return f"{self.source}:{self.nom}:{self.tag or ''}"

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "nom": self.nom,
            "tag": self.tag,
            "taille_go": self.taille_go,
            "parametres_milliards": self.parametres_milliards,
            "licence": self.licence,
            "langues": self.langues,
            "formats": self.formats,
            "quantification": self.quantification,
            "commande_pull": self.commande_pull,
            "source_url": self.source_url,
            "description": self.description,
        }


def extraire_parametres_milliards(texte: Optional[str]) -> Optional[float]:
    """Extrait un nombre de paramètres en milliards depuis un texte.

    Exemples : 'qwen3:8b' -> 8.0, 'Phi-4-14B' -> 14.0, '30b-a3b' -> 30.0.
    Retourne None si rien n'est trouvé (on ne devine jamais).
    """
    if not texte:
        return None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*[bB](?![a-zA-Z])", texte)
    if m:
        return float(m.group(1).replace(",", "."))
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:milliards|billions)\b", texte, re.IGNORECASE)
    if m:
        return float(m.group(1).replace(",", "."))
    return None


def extraire_quantification(tag: Optional[str]) -> Optional[str]:
    """Extrait la quantification d'un tag (ex. 'q4_K_M' -> 'Q4_K_M')."""
    if not tag:
        return None
    m = re.search(r"(q\d[_a-z0-9]*|iq\d[_a-z0-9]*)", tag, re.IGNORECASE)
    return m.group(1).upper() if m else None


def normaliser_licence(lic: Optional[str]) -> Optional[str]:
    """Normalise une licence : minuscules, sans préfixe 'license:'."""
    if not lic:
        return None
    return lic.strip().lower().removeprefix("license:")


def terme_recherche(nom: str) -> str:
    """Fragment de nom utilisé pour chercher dans les classements (ex. 'qwen3' -> 'qwen')."""
    base = nom.split("/")[-1].split(":")[0].split("-")[0].split("_")[0]
    base = re.sub(r"\d+$", "", base)
    return base.lower() or nom.lower()


# =====================================================================
# Client HTTP poli (User-Agent clair, délai, robots.txt)
# =====================================================================


class ClientHTTP:
    """Client HTTP réutilisable : délai entre requêtes, timeout, robots.txt."""

    def __init__(self, cfg_req: dict):
        self.delai = float(cfg_req.get("delai_entre_requetes_secondes", 2.0))
        self.timeout = float(cfg_req.get("timeout_secondes", 25))
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": cfg_req.get("user_agent", "veille-modeles-locaux/1.0")})
        self._robots: dict[str, list[str]] = {}  # hôte -> préfixes interdits

    def _prefixes_interdits(self, hote: str, scheme: str) -> list[str]:
        """Lit robots.txt une fois par hôte et renvoie les préfixes Disallow applicables."""
        if hote in self._robots:
            return self._robots[hote]
        interdits: list[str] = []
        try:
            time.sleep(self.delai)
            r = self.session.get(f"{scheme}://{hote}/robots.txt", timeout=self.timeout)
            if r.status_code == 200:
                groupe_courant = ""
                for ligne in r.text.splitlines():
                    ligne = ligne.strip()
                    if ligne.lower().startswith("user-agent:"):
                        groupe_courant = ligne.split(":", 1)[1].strip().lower()
                    elif ligne.lower().startswith("disallow:") and groupe_courant in ("*", "veille-modeles-locaux"):
                        val = ligne.split(":", 1)[1].strip()
                        if val:
                            interdits.append(val)
        except Exception:
            pass  # pas de robots.txt ou illisible -> on considère tout autorisé
        self._robots[hote] = interdits
        return interdits

    def get(self, url: str, params: Optional[dict] = None) -> requests.Response:
        """GET avec délai poli et vérification de robots.txt. Lève une exception en cas d'erreur."""
        time.sleep(self.delai)  # délai entre les requêtes, même en local
        p = urlsplit(url)
        if any(p.path.startswith(d) for d in self._prefixes_interdits(p.netloc, p.scheme)):
            raise PermissionError(f"robots.txt de {p.netloc} interdit l'accès à {p.path}")
        r = self.session.get(url, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r


# =====================================================================
# Sources : collecte
# =====================================================================


def collecter_ollama(client: ClientHTTP, cfg: dict, avertissements: list) -> tuple[list[Modele], bool]:
    """Interroge les pages publiques de la bibliothèque Ollama (robots.txt autorise /library).

    Retourne (modèles, ok) où ok=False si la source est totalement indisponible.
    """
    src = cfg["sources"]["ollama"]
    max_n = int(cfg["sources"]["requetes"].get("max_modeles_ollama", 25))
    licences_connues = [e["id"] for e in cfg["licences"]["connues"]]
    modeles: list[Modele] = []
    pages_ok = 0
    re_lien = re.compile(r'href="/library/([a-z0-9][\w.-]*)"')
    # 1) On récupère d'abord les noms uniques de toutes les pages, puis on plafond.
    noms: list[str] = []
    for page in src["pages"]:
        url = src["url_base"] + page
        try:
            html = client.get(url).text
        except Exception as e:
            avertissements.append(f"Ollama : page '{page}' indisponible ({type(e).__name__}: {e})")
            continue
        pages_ok += 1
        for m in re_lien.finditer(html):
            n = m.group(1)
            if n != "library" and n not in noms:
                noms.append(n)
    # 2) Fiches détaillées des max_n premiers modèles.
    for i, nom in enumerate(noms[:max_n], start=1):
        try:
            modeles.extend(_fiche_ollama(client, src, nom, licences_connues))
        except Exception as e:
            avertissements.append(f"Ollama : fiche '{nom}' illisible ({type(e).__name__}: {e})")
        if i % 10 == 0:
            print(f"[veille] Ollama : {i}/{min(max_n, len(noms))} fiches lues", flush=True)
    return modeles, pages_ok > 0


def _fiche_ollama(client: ClientHTTP, src: dict, nom: str, licences_connues: list[str]) -> list[Modele]:
    """Parse la page /library/<nom> d'Ollama : paires (tag, taille) + licence si mentionnée."""
    url = f"{src['url_base']}/library/{nom}"
    html = client.get(url).text
    licence = None
    html_min = html.lower()
    for lic in licences_connues:
        if lic in html_min:
            licence = lic
            break
    modeles: list[Modele] = []
    vus: set[str] = set()
    # Chaque tag apparaît sous la forme ">nom:tag</p>" suivi peu après de sa taille.
    for m in re.finditer(r">" + re.escape(nom) + r":([\w.-]+)</p>", html):
        tag = m.group(1)
        if tag in vus:
            continue
        suite = html[m.end(): m.end() + 250]
        tm = re.search(r"([\d]+(?:\.[\d]+)?)\s*(GB|MB)", suite, re.IGNORECASE)
        if not tm:
            continue
        vus.add(tag)
        taille = float(tm.group(1)) / 1024.0 if tm.group(2).upper() == "MB" else float(tm.group(1))
        modeles.append(Modele(
            source="ollama",
            nom=nom,
            tag=tag,
            source_url=url,
            taille_go=round(taille, 2),
            parametres_milliards=extraire_parametres_milliards(tag) or extraire_parametres_milliards(nom),
            licence=licence,
            langues=[],  # non précisé sur la page Ollama
            formats=["ollama"],
            quantification=extraire_quantification(tag),
            commande_pull=f"ollama pull {nom}:{tag}",
        ))
    if not modeles:
        # Page sans tableau de tags (modèle retiré ou spécial) : entrée minimale.
        modeles.append(Modele(source="ollama", nom=nom, tag=None, source_url=url,
                              formats=["ollama"], commande_pull=f"ollama pull {nom}"))
    return modeles


def collecter_huggingface(client: ClientHTTP, cfg: dict, avertissements: list) -> tuple[list[Modele], bool]:
    """Interroge l'API publique de Hugging Face (modèles récents et téléchargés, tags gguf/mlx)."""
    src = cfg["sources"]["huggingface"]
    max_n = int(cfg["sources"]["requetes"].get("max_modeles_hf", 200))
    vus: dict[str, dict] = {}
    requetes_ok = 0
    for tri in src["tris"]:
        for tag in src["filtres_tags"]:
            params = {"sort": tri, "direction": "-1", "limit": max_n, "filter": tag}
            try:
                data = client.get(src["api_base"], params=params).json()
            except Exception as e:
                avertissements.append(f"Hugging Face : tri='{tri}' filtre='{tag}' indisponible ({type(e).__name__}: {e})")
                continue
            requetes_ok += 1
            for item in data:
                if isinstance(item, dict) and "id" in item:
                    vus.setdefault(item["id"], item)
    modeles: list[Modele] = []
    max_fiches = int(cfg["sources"]["requetes"].get("max_fiches_hf", 30))
    max_tentatives = max_fiches * 2  # on ne boucle pas indéfiniment si l'API renvoie des erreurs
    nb_fiches = 0
    nb_tentatives = 0
    for rid, item in list(vus.items())[:max_n]:
        if nb_fiches >= max_fiches or nb_tentatives >= max_tentatives:
            break
        # Pré-filtre bon marché sur le nom pour ne détailler que les candidats plausibles.
        params_nom = extraire_parametres_milliards(rid)
        if params_nom is not None and not (1.0 <= params_nom <= 30.0):
            continue
        nb_tentatives += 1
        try:
            modeles.append(_fiche_huggingface(client, src, item))
            nb_fiches += 1
        except Exception as e:
            # 429/500/timeout : on note seulement en avertissement si peu de fiches aboutissent.
            avertissements.append(f"Hugging Face : fiche '{rid}' non lue ({type(e).__name__})")
        if nb_tentatives % 10 == 0:
            print(f"[veille] Hugging Face : {nb_tentatives} fiches tentées, {nb_fiches} lues", flush=True)
    return modeles, requetes_ok > 0


def _fiche_huggingface(client: ClientHTTP, src: dict, item: dict) -> Modele:
    """Construit un Modele depuis un modèle HF (détails avec tailles de fichiers)."""
    rid = item["id"]
    detail = client.get(f"{src['api_base']}/{rid}", params={"blobs": "true"}).json()
    tags = [t.lower() for t in detail.get("tags", [])]
    licence = next((t.removeprefix("license:") for t in tags if t.startswith("license:")), None)
    card = detail.get("cardData") or {}
    langues = card.get("language") or []
    if isinstance(langues, str):
        langues = [langues]
    formats: list[str] = []
    if "gguf" in tags:
        formats.append("gguf")
    if "mlx" in tags or any("mlx" in (s["rfilename"].lower()) for s in detail.get("siblings", [])):
        formats.append("mlx")
    # Taille du fichier quantifié visé : Q4_K_M en priorité, sinon le plus gros .gguf,
    # sinon la somme des fichiers MLX (safetensors).
    taille_go: Optional[float] = None
    quant: Optional[str] = None
    siblings = detail.get("siblings", [])
    gguf = [s for s in siblings if s["rfilename"].lower().endswith(".gguf")]
    if gguf:
        q4 = [s for s in gguf if "q4_k_m" in s["rfilename"].lower()]
        choisi = q4[0] if q4 else max(gguf, key=lambda s: (s.get("lfs") or {}).get("size") or 0)
        taille_go = round(((choisi.get("lfs") or {}).get("size") or 0) / 1e9, 2)
        quant = extraire_quantification(choisi["rfilename"])
    elif formats == ["mlx"]:
        total = sum((s.get("lfs") or {}).get("size") or 0 for s in siblings)
        taille_go = round(total / 1e9, 2) if total else None
    return Modele(
        source="huggingface",
        nom=rid,
        tag=None,
        source_url=f"https://huggingface.co/{rid}",
        taille_go=taille_go,
        parametres_milliards=extraire_parametres_milliards(rid),
        licence=normaliser_licence(licence),
        langues=[str(l) for l in langues],
        formats=formats or ["gguf" if "gguf" in tags else "mlx"],
        quantification=quant,
        date_modification=detail.get("lastModified", "")[:10] or None,
        commande_pull=None,  # pas de pull Ollama : lien direct vers le dépôt
    )


def collecter_classements(client: ClientHTTP, cfg: dict, termes: list[str],
                          avertissements: list) -> dict:
    """Interroge les classements ouverts (lecture seule) pour une liste de noms.

    Retourne {terme: {nom_du_classement: {"score": ..., "rang": ..., "date": ...}}}.
    Toute erreur -> avertissement, et le rapport affichera « non mesuré ».
    """
    base = "https://datasets-server.huggingface.co/filter"
    resultats: dict[str, dict] = {t: {} for t in termes}
    for cls in cfg["sources"].get("classements", []):
        if not cls.get("actif", True):
            continue
        if cls.get("type") != "hf_datasets_server":
            avertissements.append(f"Classement '{cls['nom']}' : type '{cls.get('type')}' non supporté, ignoré.")
            continue
        champ = cls.get("champ_modele", "model_name")
        indisponible = False
        for terme in termes:
            if indisponible:
                break  # classement en panne : on n'insiste pas, le rapport dira « non mesuré »
            terme_sur = terme.replace("'", "")
            where = f'"{champ}" ILIKE \'%{terme_sur}%\''
            try:
                r = client.get(base, params={
                    "dataset": cls["dataset"], "config": cls["config"], "split": cls["split"],
                    "where": where, "offset": 0, "length": 20,
                })
                rows = r.json().get("rows", [])
            except Exception as e:
                avertissements.append(f"Classement '{cls['nom']}' : indisponible ({type(e).__name__}: {e})")
                indisponible = True
                continue
            meilleur = None
            for row in rows:
                r0 = row.get("row", {})
                score = r0.get(cls.get("champ_score") or "")
                rang = r0.get(cls.get("champ_rang")) if cls.get("champ_rang") else None
                if score is None:
                    continue
                if meilleur is None or (rang is not None and (meilleur["rang"] is None or rang < meilleur["rang"])):
                    meilleur = {"score": score, "rang": rang,
                                "date": r0.get("leaderboard_publish_date") or r0.get("date") or "",
                                "modele_trouve": r0.get(champ, "")}
            if meilleur:
                resultats[terme][cls["nom"]] = meilleur
    return resultats


# =====================================================================
# Filtrage déterministe (fonctions pures, testées par pytest)
# =====================================================================


def regle_taille(m: Modele, cfg: dict) -> tuple[bool, str]:
    """Règle 1 : le fichier quantifié doit faire strictement moins de taille_fichier_max_go."""
    max_go = float(cfg["budget_memoire"]["taille_fichier_max_go"])
    if m.taille_go is None:
        return False, "taille du fichier quantifié non déterminée"
    if m.taille_go >= max_go:
        return False, f"trop gros : {m.taille_go} Go >= {max_go} Go (budget mémoire)"
    return True, ""


def regle_parametres(m: Modele, cfg: dict) -> tuple[bool, str]:
    """Règle 2 : entre min_milliards et max_milliards de paramètres."""
    pmin = float(cfg["parametres"]["min_milliards"])
    pmax = float(cfg["parametres"]["max_milliards"])
    if m.parametres_milliards is None:
        return False, "nombre de paramètres non déterminé"
    p = m.parametres_milliards
    if not (pmin <= p <= pmax):
        return False, f"hors tranche : {p} Md (attendu {pmin}–{pmax} Md)"
    return True, ""


def regle_installable(m: Modele, cfg: dict) -> tuple[bool, str]:
    """Règle 3 : installable via Ollama ou disponible en GGUF/MLX."""
    acceptes = set(cfg["installable"].get("formats_locaux", ["gguf", "mlx"]))
    if cfg["installable"].get("via_ollama", True):
        acceptes.add("ollama")
    if set(m.formats) & acceptes:
        return True, ""
    return False, f"non installable en local (formats: {', '.join(m.formats) or 'aucun'})"


def regle_licence(m: Modele, cfg: dict) -> tuple[bool, str]:
    """Règle 4 : la licence doit autoriser un usage professionnel (voir config.yaml)."""
    return _regle_licence_impl(normaliser_licence(m.licence), cfg)


def _regle_licence_impl(lic: Optional[str], cfg: dict) -> tuple[bool, str]:
    connues = cfg["licences"]["connues"]
    mode_inconnue = cfg["licences"].get("regle_licence_inconnue", "refuser")
    if lic is None:
        if mode_inconnue == "accepter":
            return True, ""
        if mode_inconnue == "signaler":
            return True, "licence inconnue (signalée, à vérifier manuellement)"
        return False, "licence inconnue (règle par défaut : refuser)"
    for entry in connues:
        if lic == entry["id"] or lic.startswith(entry["id"]):
            if entry["acceptee"]:
                return True, ""
            return False, f"licence '{lic}' non acceptée pour un usage pro ({entry['note']})"
    if mode_inconnue == "signaler":
        return True, f"licence '{lic}' non listée (signalée, à vérifier manuellement)"
    return False, f"licence '{lic}' non listée dans config.yaml (règle par défaut : refuser)"


def regle_langues(m: Modele, cfg: dict) -> tuple[bool, str]:
    """Règle 5 : si les langues sont annoncées et qu'aucune n'est le français -> écarté.

    Si rien n'est annoncé, on ne peut pas conclure : le modèle n'est pas écarté.
    """
    if not cfg["langues"].get("exiger_francais_si_connues", True):
        return True, ""
    if not m.langues:
        return True, ""
    codes_fr = [c.lower() for c in cfg["langues"]["codes_francais"]]
    for langue in m.langues:
        l = str(langue).lower()
        if any(code in l for code in codes_fr):
            return True, ""
    return False, f"pas de français annoncé (langues: {', '.join(map(str, m.langues))})"


REGLES = [regle_taille, regle_parametres, regle_installable, regle_licence, regle_langues]


def filtrer(modeles: list[Modele], cfg: dict) -> tuple[list[Modele], list[tuple[Modele, str]]]:
    """Applique toutes les règles. Retourne (retenus, écartés avec raison)."""
    retenus: list[Modele] = []
    ecartes: list[tuple[Modele, str]] = []
    for m in modeles:
        raisons = [raison for regle in REGLES for ok, raison in [regle(m, cfg)] if not ok]
        if raisons:
            ecartes.append((m, " ; ".join(raisons)))
        else:
            retenus.append(m)
    return retenus, ecartes


def categorie(m: Modele, cfg: dict) -> str:
    """'petit' pour les 3–6 Md (catégorie mise en surbrillance), sinon 'standard'."""
    pmax_petit = float(cfg["parametres"].get("petit_modele_max_milliards", 6.0))
    if m.parametres_milliards is not None and m.parametres_milliards <= pmax_petit:
        return "petit"
    return "standard"


def est_nouveau(m: Modele, hist: dict) -> bool:
    """True si ce modèle (cette clé) n'a jamais été vu dans l'historique."""
    return m.cle not in hist.get("modeles", {})


# =====================================================================
# Alertes sur les modèles actuels
# =====================================================================


def verifier_presence_actuels(client: ClientHTTP, cfg: dict) -> set[str]:
    """Vérifie directement la page /library/<nom> de chaque modèle actuel (et embeddings).

    Le classement « newest » ne contient pas forcément mes modèles actuels : on va
    chercher leur page explicitement (6 requêtes, polies) avant de crier à la suppression.
    """
    src = cfg["sources"]["ollama"]
    presents: set[str] = set()
    actuels = cfg.get("modeles_actuels", {})
    noms = [ma["nom"] for ma in actuels.get("llm", [])]
    emb = actuels.get("embeddings") or {}
    if emb.get("nom"):
        noms.append(emb["nom"])
    for nom in noms:
        try:
            client.get(f"{src['url_base']}/library/{nom}")
            presents.add(nom)
        except Exception:
            pass  # page absente ou en erreur -> signalé comme alerte par detecter_alertes
    return presents


def detecter_alertes(cfg: dict, hist: dict, noms_ollama_vus: set[str],
                     ollama_ok: bool, avertissements: list) -> list[str]:
    """Vérifie que chaque modèle actuel est toujours présent et signale toute disparition."""
    alertes: list[str] = []
    if not ollama_ok:
        return alertes  # source indisponible : on ne crie pas à la suppression
    actuels = cfg.get("modeles_actuels", {})
    for ma in actuels.get("llm", []):
        nom = ma["nom"]
        if nom not in noms_ollama_vus:
            alertes.append(f"⚠️ '{nom}' ({ma.get('role', 'modèle actuel')}) n'apparaît plus dans la "
                           f"bibliothèque Ollama : vérifier une éventuelle suppression ou un renommage.")
    emb = actuels.get("embeddings") or {}
    if emb.get("nom") and emb["nom"] not in noms_ollama_vus:
        alertes.append(f"⚠️ Embeddings actuel '{emb['nom']}' absent de la bibliothèque Ollama : à vérifier.")
    return alertes


# =====================================================================
# Rapport
# =====================================================================


def _fmt_taille(m: Modele) -> str:
    return f"{m.taille_go} Go" if m.taille_go is not None else "non déterminée"


def _fmt_params(m: Modele) -> str:
    return f"{m.parametres_milliards:g} Md" if m.parametres_milliards is not None else "non déterminé"


def _lien_source(m: Modele) -> str:
    return f"[source]({m.source_url})" if m.source_url else "—"


def _ligne_tableau(m: Modele) -> str:
    langues = ", ".join(map(str, m.langues)) if m.langues else "non précisé"
    if m.commande_pull:
        install = m.commande_pull
    else:
        install = f"{', '.join(m.formats).upper()} — voir le lien source"
    return (f"| `{m.nom}{':' + m.tag if m.tag else ''}` | {_fmt_taille(m)} | {_fmt_params(m)} "
            f"| {m.licence or 'inconnue'} | {m.date_modification or '—'} | {langues} "
            f"| `{install}` | {_lien_source(m)} |")


def section_comparaison(m: Modele, cfg: dict, scores: dict) -> str:
    """Comparaison tâche par tâche avec les modèles actuels.

    Règle d'honnêteté : si aucun score fiable n'est publié, on écrit « non mesuré ».
    """
    terme = terme_recherche(m.nom)
    lignes = [f"#### `{m.nom}{':' + m.tag if m.tag else ''}` — comparaison avec mes modèles actuels", ""]
    # Scores globaux publiés pour ce candidat.
    for cls in cfg["sources"].get("classements", []):
        if not cls.get("actif", True):
            continue
        s = scores.get(terme, {}).get(cls["nom"])
        if s:
            try:
                score_txt = f"{float(s['score']):.1f}"
            except (TypeError, ValueError):
                score_txt = str(s["score"])
            rang = f", rang {s['rang']:g}" if s.get("rang") is not None else ""
            date = f" (publié le {s['date']})" if s.get("date") else ""
            lignes.append(f"- **{cls['nom']}** : score {score_txt}{rang}{date} — "
                          f"source : `{cls['dataset']}` (lecture seule).")
        else:
            lignes.append(f"- **{cls['nom']}** : non mesuré (aucun score publié trouvé pour ce modèle).")
    # Mes modèles actuels sur le même classement (meilleur score retenu).
    lignes.append("")
    lignes.append("| Tâche | Ce candidat | Mes modèles actuels (référence) | Source |")
    lignes.append("|---|---|---|---|")
    refs = []
    for ma in cfg.get("modeles_actuels", {}).get("llm", []):
        t = terme_recherche(ma["nom"])
        for cls in cfg["sources"].get("classements", []):
            if cls.get("actif", True) and t in scores and cls["nom"] in scores[t]:
                sc = scores[t][cls["nom"]]["score"]
                try:
                    sc = f"{float(sc):.1f}"
                except (TypeError, ValueError):
                    pass
                refs.append(f"{ma['nom']} : {sc} ({cls['nom']})")
                break
    ref_txt = " ; ".join(refs) if refs else "non mesuré"
    for tache in cfg.get("taches", []):
        lignes.append(f"| {tache} | non mesuré | {ref_txt} | classements publics |")
    lignes.append("")
    lignes.append("> Aucun chiffre n'est inventé : « non mesuré » signifie qu'aucun benchmark "
                  "public fiable n'a été trouvé pour cette tâche. À confirmer par un test local "
                  "avant adoption.")
    lignes.append("")
    return "\n".join(lignes)


def generer_rapport(date_rapport: str, retenus: list[Modele], ecartes: list[tuple[Modele, str]],
                    alertes: list[str], scores: dict, avertissements: list,
                    sources_statut: dict, cfg: dict) -> str:
    """Construit le rapport hebdomadaire en markdown, en français (constat / cause / geste)."""
    petits = [m for m in retenus if categorie(m, cfg) == "petit"]
    standards = [m for m in retenus if categorie(m, cfg) == "standard"]
    L: list[str] = []
    L.append(f"# Veille modèles locaux — rapport du {date_rapport}")
    L.append("")
    L.append("> Généré automatiquement par `veille.py` (GitHub Action, chaque lundi à 06h00 UTC, "
             "plus déclenchement manuel). Aucune donnée personnelle, aucune clé. Sources publiques "
             "en lecture seule. Machine cible : Mac M1 16 Go, budget 8 Go / modèle chargé, "
             "fichier quantifié < 9 Go, 3–14 Md de paramètres.")
    L.append("")

    # ------------------------------------------------------------------
    L.append("## Verdict")
    L.append("")
    if retenus:
        noms = ", ".join(f"`{m.nom}{':' + m.tag if m.tag else ''}`" for m in retenus)
        L.append(f"**À tester : {noms}**")
        L.append("")
        L.append(f"- **Constat** : {len(retenus)} modèle(s) nouveau(x) passe(nt) tous les filtres "
                 f"(taille < {cfg['budget_memoire']['taille_fichier_max_go']} Go, "
                 f"{cfg['parametres']['min_milliards']:g}–{cfg['parametres']['max_milliards']:g} Md, "
                 f"licence acceptée, installable en local).")
        L.append(f"- **Cause** : ces modèles sont absents de `historique.json` et ils correspondent "
                 f"à la tranche visée pour la machine (8 Go utiles, contexte 8 192 jetons).")
        L.append("- **Geste** : les tirer (`ollama pull ...` ou dépôt GGUF/MLX), puis les tester "
                 "sur les 7 tâches de `config.yaml` avec une note de 9 000 caractères ; garder ceux "
                 "qui battent mistral-nemo 12B / qwen3.5 9B sans inventer ni ralentir.")
    else:
        L.append("**Rien à tester cette semaine.**")
        L.append("")
        L.append("- **Constat** : aucun nouveau modèle ne passe à la fois le filtre mémoire "
                 f"(< {cfg['budget_memoire']['taille_fichier_max_go']} Go), la tranche de paramètres "
                 "et le filtre de licence.")
        L.append("- **Cause** : soit aucune nouveauté cette semaine, soit les nouveautés sont "
                 "écartées (voir section 3 pour les raisons).")
        L.append("- **Geste** : aucune action requise ; relancer la veille lundi prochain.")
    L.append("")

    # ------------------------------------------------------------------
    L.append("## 1. Modèles retenus (nouveautés de la semaine)")
    L.append("")
    if retenus:
        L.append("| Modèle | Taille fichier | Paramètres | Licence | Date | Langues annoncées | Installation | Source |")
        L.append("|---|---|---|---|---|---|---|---|")
        for m in standards:
            L.append(_ligne_tableau(m))
        L.append("")
        if petits:
            L.append(f"### ⭐ Petits modèles spécialisés ({cfg['parametres']['min_milliards']:g}–"
                     f"{cfg['parametres']['petit_modele_max_milliards']:g} Md) — marge mémoire confortable")
            L.append("")
            L.append("| Modèle | Taille fichier | Paramètres | Licence | Date | Langues annoncées | Installation | Source |")
            L.append("|---|---|---|---|---|---|---|---|")
            for m in petits:
                L.append(_ligne_tableau(m))
            L.append("")
    else:
        L.append("_Aucun modèle retenu cette semaine._")
        L.append("")

    # ------------------------------------------------------------------
    L.append("## 2. Comparaison avec mes modèles actuels (tâche par tâche)")
    L.append("")
    if retenus:
        for m in retenus:
            L.append(section_comparaison(m, cfg, scores))
    else:
        L.append("_Pas de candidat à comparer cette semaine._")
        L.append("")

    # ------------------------------------------------------------------
    L.append("## 3. Modèles écartés (une ligne par raison)")
    L.append("")
    if ecartes:
        for m, raison in ecartes[:40]:
            L.append(f"- `{m.nom}{':' + m.tag if m.tag else ''}` ({m.source}) — {raison}.")
        if len(ecartes) > 40:
            L.append(f"- … et {len(ecartes) - 40} autre(s) écarté(s) (liste complète dans `historique.json`).")
    else:
        L.append("_Aucun modèle écarté cette semaine._")
    L.append("")

    # ------------------------------------------------------------------
    L.append("## 4. Alertes sur mes modèles actuels")
    L.append("")
    if alertes:
        for a in alertes:
            L.append(f"- {a}")
    else:
        L.append("- Aucune alerte : tous les modèles actuels sont toujours présents.")
    L.append("")

    # ------------------------------------------------------------------
    L.append("## 5. Sources interrogées cette semaine")
    L.append("")
    L.append("| Source | Statut | Détail |")
    L.append("|---|---|---|")
    for nom, (ok, detail) in sources_statut.items():
        L.append(f"| {nom} | {'✅ OK' if ok else '⚠️ indisponible'} | {detail} |")
    if avertissements:
        L.append("")
        L.append("Avertissements :")
        for a in avertissements[:20]:
            L.append(f"- {a}")
        if len(avertissements) > 20:
            L.append(f"- … et {len(avertissements) - 20} autre(s) avertissement(s).")
    L.append("")
    L.append("---")
    L.append(f"*Rapport généré le {date_rapport} (UTC) par `veille.py`. Les scores cités proviennent "
             "de classements publics en lecture seule ; « non mesuré » = aucune donnée fiable trouvée. "
             "Aucun chiffre n'est estimé ou inventé.*")
    L.append("")
    return "\n".join(L)


# =====================================================================
# Historique et journal
# =====================================================================


def mettre_a_jour_historique(hist: dict, retenus: list[Modele],
                             ecartes: list[tuple[Modele, str]], date_rapport: str) -> None:
    """Ajoute les modèles vus cette semaine à historique.json (sans jamais écraser les 'actuel')."""
    modeles = hist.setdefault("modeles", {})
    for m in retenus:
        if m.cle not in modeles:
            modeles[m.cle] = {"statut": "vu", "premiere_observation": date_rapport,
                              "vu_le": date_rapport, **m.to_dict()}
        else:
            modeles[m.cle]["vu_le"] = date_rapport
    for m, raison in ecartes:
        if m.cle not in modeles:
            modeles[m.cle] = {"statut": "ecarte", "raison": raison,
                              "premiere_observation": date_rapport, "vu_le": date_rapport,
                              **m.to_dict()}
        else:
            modeles[m.cle]["vu_le"] = date_rapport
    hist["derniere_mise_a_jour"] = date_rapport


def journaliser(chemin_journal: Path, date_rapport: str, fichier: str, etape: str, raison: str) -> None:
    """Consigne une étape dans JOURNAL.md (tableau date / fichier / étape / raison)."""
    try:
        with open(chemin_journal, "a", encoding="utf-8") as f:
            f.write(f"| {date_rapport} | `{fichier}` | {etape} | {raison} |\n")
    except Exception:
        pass  # le journal ne doit jamais faire échouer la veille


# =====================================================================
# Programme principal
# =====================================================================


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Veille hebdomadaire des modèles LLM locaux.")
    parser.add_argument("--config", default=str(RACINE / "config.yaml"))
    parser.add_argument("--historique", default=str(RACINE / "historique.json"))
    parser.add_argument("--journal", default=str(RACINE / "JOURNAL.md"))
    parser.add_argument("--date", default=None,
                        help="Date du rapport AAAA-MM-JJ (défaut : aujourd'hui, UTC).")
    args = parser.parse_args(argv)

    date_rapport = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cfg = charger_config(Path(args.config))
    hist = charger_historique(Path(args.historique))
    dossier_rapports = RACINE / cfg["rapport"]["dossier"]
    dossier_rapports.mkdir(parents=True, exist_ok=True)

    client = ClientHTTP(cfg["sources"]["requetes"])
    avertissements: list[str] = []
    sources_statut: dict[str, tuple[bool, str]] = {}

    def log(msg: str) -> None:
        print(f"[veille {date_rapport}] {msg}", flush=True)

    # --- 1. Collecte (chaque source est isolée : une panne n'arrête pas les autres)
    modeles: list[Modele] = []
    noms_ollama_vus: set[str] = set()
    if cfg["sources"]["ollama"].get("active", True):
        log("Collecte Ollama...")
        m_ollama, ok = collecter_ollama(client, cfg, avertissements)
        log(f"Ollama : {len(m_ollama)} version(s) de modèles")
        modeles += m_ollama
        noms_ollama_vus = {m.nom for m in m_ollama}
        sources_statut["Ollama (ollama.com/library)"] = (ok, f"{len(m_ollama)} version(s) de modèles examinée(s)")
    else:
        sources_statut["Ollama (ollama.com/library)"] = (False, "source désactivée dans config.yaml")
    if cfg["sources"]["huggingface"].get("active", True):
        log("Collecte Hugging Face...")
        m_hf, ok = collecter_huggingface(client, cfg, avertissements)
        log(f"Hugging Face : {len(m_hf)} dépôt(s)")
        modeles += m_hf
        sources_statut["Hugging Face (api/models, gguf + mlx)"] = (ok, f"{len(m_hf)} dépôt(s) examiné(s)")
    else:
        sources_statut["Hugging Face (api/models, gguf + mlx)"] = (False, "source désactivée dans config.yaml")

    # --- 2. Filtrage déterministe
    log("Filtrage déterministe...")
    retenus, ecartes = filtrer(modeles, cfg)
    retenus_nouveaux = [m for m in retenus if est_nouveau(m, hist)]
    ecartes_nouveaux = [(m, r) for m, r in ecartes if est_nouveau(m, hist)]
    log(f"{len(retenus_nouveaux)} candidat(s) retenu(s) et nouveau(x), {len(ecartes_nouveaux)} écarté(s) nouveau(x)")

    # --- 3. Classements (optionnel ; sinon « non mesuré » dans le rapport)
    max_termes = int(cfg["sources"]["requetes"].get("max_termes_classements", 8))
    termes = sorted({terme_recherche(m.nom) for m in retenus_nouveaux} |
                    {terme_recherche(ma["nom"]) for ma in cfg.get("modeles_actuels", {}).get("llm", [])})
    termes = termes[:max_termes]
    scores: dict = {}
    if any(c.get("actif", True) for c in cfg["sources"].get("classements", [])) and termes:
        log(f"Classements ({len(termes)} terme(s) max)...")
        scores = collecter_classements(client, cfg, termes, avertissements)
        sources_statut["Classements ouverts (LMArena, Open LLM Leaderboard)"] = (
            bool(scores), f"{sum(len(v) for v in scores.values())} score(s) trouvé(s) pour {len(termes)} terme(s)")

    # --- 4. Alertes sur les modèles actuels (vérification directe de leurs pages Ollama)
    if sources_statut.get("Ollama (ollama.com/library)", (False, ""))[0]:
        noms_ollama_vus = noms_ollama_vus | verifier_presence_actuels(client, cfg)
    alertes = detecter_alertes(cfg, hist, noms_ollama_vus,
                                sources_statut.get("Ollama (ollama.com/library)", (False, ""))[0],
                                avertissements)

    # --- 5. Rapport + historique + journal
    log("Génération du rapport...")
    rapport = generer_rapport(date_rapport, retenus_nouveaux, ecartes_nouveaux, alertes,
                              scores, avertissements, sources_statut, cfg)
    chemin_rapport = dossier_rapports / f"{date_rapport}.md"
    with open(chemin_rapport, "w", encoding="utf-8") as f:
        f.write(rapport)
    mettre_a_jour_historique(hist, retenus, ecartes, date_rapport)
    sauvegarder_historique(Path(args.historique), hist)
    journaliser(Path(args.journal), date_rapport, f"rapports/{date_rapport}.md",
                f"Rapport de veille généré : {len(retenus_nouveaux)} candidat(s) retenu(s), "
                f"{len(ecartes_nouveaux)} écarté(s), {len(alertes)} alerte(s).",
                "Exécution hebdomadaire (cron lundi 06h00 UTC ou manuel).")

    # --- 6. Résumé console
    print(f"Rapport écrit : {chemin_rapport}")
    print(f"Retenus (nouveaux) : {len(retenus_nouveaux)} -> "
          + (", ".join(m.cle for m in retenus_nouveaux) if retenus_nouveaux else "aucun"))
    print(f"Écartés (nouveaux) : {len(ecartes_nouveaux)} | Alertes : {len(alertes)} | "
          f"Avertissements : {len(avertissements)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
