# -*- coding: utf-8 -*-
"""
Tests du filtrage déterministe de veille.py, avec des modèles fictifs.

Lancement :  python3 -m pytest tests/ -q
Aucune connexion réseau n'est nécessaire : on teste les fonctions pures.
"""

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # racine du dépôt

import veille  # noqa: E402


# ---------------------------------------------------------------------
# Configuration de test (synthétique, indépendante de config.yaml)
# ---------------------------------------------------------------------

@pytest.fixture()
def cfg():
    return {
        "budget_memoire": {"taille_fichier_max_go": 9.0},
        "parametres": {"min_milliards": 3.0, "max_milliards": 14.0,
                       "petit_modele_max_milliards": 6.0},
        "installable": {"via_ollama": True, "formats_locaux": ["gguf", "mlx"]},
        "licences": {
            "regle_licence_inconnue": "refuser",
            "connues": [
                {"id": "apache-2.0", "acceptee": True, "note": "OK"},
                {"id": "mit", "acceptee": True, "note": "OK"},
                {"id": "cc-by-nc-4.0", "acceptee": False, "note": "non commercial"},
            ],
        },
        "langues": {"exiger_francais_si_connues": True,
                    "codes_francais": ["fr", "french", "français", "multilingual"]},
        "taches": ["Titrer une note en français"],
        "modeles_actuels": {"llm": [{"nom": "qwen3", "tag_ollama": "8b"}], "embeddings": {"nom": "nomic-embed-text"}},
        "sources": {"classements": []},
    }


def modele_fictif(**kwargs):
    """Modèle fictif valide par défaut ; on surcharge champ par champ."""
    base = dict(source="ollama", nom="fictif", tag="8b", source_url="https://exemple.test/fictif",
                taille_go=5.0, parametres_milliards=8.0, licence="apache-2.0",
                langues=["fr", "en"], formats=["ollama"], quantification="Q4_K_M",
                commande_pull="ollama pull fictif:8b")
    base.update(kwargs)
    if "commande_pull" not in kwargs:
        base["commande_pull"] = f"ollama pull {base['nom']}:{base['tag']}"
    return veille.Modele(**base)


# ---------------------------------------------------------------------
# Le vrai config.yaml doit être valide et cohérent
# ---------------------------------------------------------------------

def test_config_yaml_reel_charge():
    cfg = veille.charger_config(Path(__file__).resolve().parent.parent / "config.yaml")
    assert cfg["budget_memoire"]["taille_fichier_max_go"] == 9.0
    assert cfg["parametres"]["min_milliards"] <= cfg["parametres"]["max_milliards"]
    assert any(e["id"] == "apache-2.0" and e["acceptee"] for e in cfg["licences"]["connues"])
    assert len(cfg["modeles_actuels"]["llm"]) == 5
    assert cfg["modeles_actuels"]["embeddings"]["nom"] == "nomic-embed-text"


# ---------------------------------------------------------------------
# Règles individuelles
# ---------------------------------------------------------------------

def test_taille_limite_stricte(cfg):
    assert veille.regle_taille(modele_fictif(taille_go=8.99), cfg)[0] is True
    # 9 Go pile est refusé : la règle est « strictement moins de 9 Go »
    ok, raison = veille.regle_taille(modele_fictif(taille_go=9.0), cfg)
    assert ok is False and "trop gros" in raison
    ok, raison = veille.regle_taille(modele_fictif(taille_go=15.0), cfg)
    assert ok is False and "trop gros" in raison


def test_taille_inconnue_refusee(cfg):
    ok, raison = veille.regle_taille(modele_fictif(taille_go=None), cfg)
    assert ok is False and "non déterminée" in raison


def test_parametres_hors_tranche(cfg):
    assert veille.regle_parametres(modele_fictif(parametres_milliards=2.9), cfg)[0] is False
    assert veille.regle_parametres(modele_fictif(parametres_milliards=3.0), cfg)[0] is True
    assert veille.regle_parametres(modele_fictif(parametres_milliards=14.0), cfg)[0] is True
    assert veille.regle_parametres(modele_fictif(parametres_milliards=14.1), cfg)[0] is False
    ok, _ = veille.regle_parametres(modele_fictif(parametres_milliards=None), cfg)
    assert ok is False


def test_installable(cfg):
    assert veille.regle_installable(modele_fictif(formats=["ollama"]), cfg)[0] is True
    assert veille.regle_installable(modele_fictif(source="huggingface", formats=["gguf"]), cfg)[0] is True
    assert veille.regle_installable(modele_fictif(formats=["mlx"]), cfg)[0] is True
    ok, raison = veille.regle_installable(modele_fictif(formats=["safetensors"]), cfg)
    assert ok is False and "non installable" in raison


def test_licence(cfg):
    assert veille.regle_licence(modele_fictif(licence="Apache-2.0"), cfg)[0] is True
    assert veille.regle_licence(modele_fictif(licence="license:mit"), cfg)[0] is True
    ok, raison = veille.regle_licence(modele_fictif(licence="cc-by-nc-4.0"), cfg)
    assert ok is False and "non acceptée" in raison
    ok, raison = veille.regle_licence(modele_fictif(licence=None), cfg)
    assert ok is False and "inconnue" in raison
    ok, raison = veille.regle_licence(modele_fictif(licence="une-licence-exotique"), cfg)
    assert ok is False and "non listée" in raison


def test_licence_inconnue_mode_signaler(cfg):
    cfg["licences"]["regle_licence_inconnue"] = "signaler"
    ok, raison = veille.regle_licence(modele_fictif(licence=None), cfg)
    assert ok is True and "signalée" in raison


def test_langues(cfg):
    assert veille.regle_langues(modele_fictif(langues=["fr", "en"]), cfg)[0] is True
    assert veille.regle_langues(modele_fictif(langues=["Multilingual"]), cfg)[0] is True
    assert veille.regle_langues(modele_fictif(langues=[]), cfg)[0] is True  # non précisé : pas de conclusion
    ok, raison = veille.regle_langues(modele_fictif(langues=["en", "de"]), cfg)
    assert ok is False and "pas de français" in raison


# ---------------------------------------------------------------------
# Filtrage global + catégories + nouveauté
# ---------------------------------------------------------------------

def test_filtrer_global(cfg):
    modeles = [
        modele_fictif(nom="bon", tag="8b"),                                   # retenu
        modele_fictif(nom="gros", tag="14b", taille_go=12.4),                 # trop gros
        modele_fictif(nom="nc", tag="8b", licence="cc-by-nc-4.0"),             # licence NC
        modele_fictif(nom="petit", tag="4b", parametres_milliards=4.0),        # retenu, catégorie petit
        modele_fictif(nom="inconnu", tag="8b", licence=None),                  # licence inconnue
        modele_fictif(nom="anglais", tag="8b", langues=["en"]),               # pas de français
        modele_fictif(nom="hf", source="huggingface", tag=None, formats=["gguf"]),  # retenu (GGUF)
    ]
    retenus, ecartes = veille.filtrer(modeles, cfg)
    noms_retenus = {m.nom for m in retenus}
    assert noms_retenus == {"bon", "petit", "hf"}
    raisons = {m.nom: r for m, r in ecartes}
    assert "trop gros" in raisons["gros"]
    assert "non acceptée" in raisons["nc"]
    assert "inconnue" in raisons["inconnu"]
    assert "pas de français" in raisons["anglais"]


def test_categorie_petit(cfg):
    assert veille.categorie(modele_fictif(parametres_milliards=4.0), cfg) == "petit"
    assert veille.categorie(modele_fictif(parametres_milliards=6.0), cfg) == "petit"
    assert veille.categorie(modele_fictif(parametres_milliards=8.0), cfg) == "standard"


def test_est_nouveau():
    hist = {"modeles": {"ollama:qwen3:8b": {"statut": "vu"}}}
    assert veille.est_nouveau(modele_fictif(nom="qwen3", tag="8b"), hist) is False
    assert veille.est_nouveau(modele_fictif(nom="qwen3", tag="14b"), hist) is True


# ---------------------------------------------------------------------
# Helpers d'extraction
# ---------------------------------------------------------------------

@pytest.mark.parametrize("texte,attendu", [
    ("qwen3:8b", 8.0),
    ("phi4:14b", 14.0),
    ("Qwen3-8B-GGUF", 8.0),
    ("llama-30b-a3b", 30.0),
    ("12 milliards de paramètres", 12.0),
    ("gemma3", None),
    (None, None),
])
def test_extraire_parametres(texte, attendu):
    assert veille.extraire_parametres_milliards(texte) == attendu


def test_extraire_quantification():
    assert veille.extraire_quantification("q4_K_M") == "Q4_K_M"
    assert veille.extraire_quantification("8b") is None


def test_terme_recherche():
    assert veille.terme_recherche("qwen3") == "qwen"
    assert veille.terme_recherche("Qwen/Qwen3-8B-GGUF") == "qwen"
    assert veille.terme_recherche("mistral-nemo") == "mistral"


# ---------------------------------------------------------------------
# Rapport : format et règle « non mesuré »
# ---------------------------------------------------------------------

def test_rapport_verdict_rien_a_tester(cfg):
    rapport = veille.generer_rapport("2026-11-23", [], [], [], {}, [],
                                     {"Ollama": (True, "ok")}, cfg)
    assert "Rien à tester cette semaine" in rapport
    assert "non mesuré" in rapport or "Aucun modèle" in rapport


def test_rapport_verdict_a_tester_et_non_mesure(cfg):
    m = modele_fictif(nom="nouveau-modele", tag="8b")
    rapport = veille.generer_rapport("2026-11-23", [m], [], [], {}, [],
                                     {"Ollama": (True, "ok")}, cfg)
    assert "À tester : `nouveau-modele:8b`" in rapport
    assert "ollama pull nouveau-modele:8b" in rapport
    # Sans aucun score de classement, la comparaison doit dire « non mesuré ».
    assert "non mesuré" in rapport
    assert "LMArena" not in rapport or "non mesuré" in rapport


def test_rapport_source_indisponible(cfg):
    rapport = veille.generer_rapport("2026-11-23", [], [], [], {},
                                     ["Ollama : page indisponible (TimeoutError)"],
                                     {"Ollama": (False, "indisponible")}, cfg)
    assert "indisponible" in rapport
    assert "Ollama : page indisponible" in rapport


def test_historique_mise_a_jour():
    hist = {"version": 1, "derniere_mise_a_jour": None, "modeles": {}}
    m = modele_fictif(nom="abc", tag="8b")
    veille.mettre_a_jour_historique(hist, [m], [], "2026-11-23")
    assert "ollama:abc:8b" in hist["modeles"]
    assert hist["modeles"]["ollama:abc:8b"]["statut"] == "vu"
    assert hist["derniere_mise_a_jour"] == "2026-11-23"
    # Un modèle actuel ne doit jamais être écrasé par la mise à jour.
    hist["modeles"]["ollama:abc:8b"]["statut"] = "actuel"
    veille.mettre_a_jour_historique(hist, [m], [], "2026-11-30")
    assert hist["modeles"]["ollama:abc:8b"]["statut"] == "actuel"
