#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
obsidian_sync.py — pont entre ce dépôt et ton vault Obsidian.

Objectif : chaque rapport de veille (rapports/AAAA-MM-JJ.md) devient une note
datée et précise dans Obsidian (frontmatter YAML + contenu du rapport).

SÉCURITÉ / ACCÈS :
  - Par défaut, ce script est en LECTURE SEULE sur le vault : il liste les
    notes existantes et affiche ce qu'il écrirait, sans rien modifier.
  - L'écriture n'a lieu qu'avec `--apply` ET `obsidian.ecriture_autorisee: true`
    dans config.yaml. Tant que l'utilisateur n'a pas donné l'accès en écriture,
    rien n'est écrit dans Obsidian.
  - Si le vault est illisible (chemin non autorisé), le script le dit clairement
    au lieu d'échouer.

Flux prévu : la GitHub Action produit le rapport dans le dépôt GitHub ;
côté Mac, une petite tâche planifiée (ex. cron/launchd mardi matin) exécute :
    git -C <ce dépôt> pull && python3 obsidian_sync.py --apply

Dépendances : requests, pyyaml (comme veille.py).
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent


# =====================================================================
# Fonctions pures (testées par pytest)
# =====================================================================


def charger_config(chemin: Path) -> dict:
    with open(chemin, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def nom_fichier_note(date_rapport: str, cfg: dict) -> str:
    """Nom de la note Obsidian pour un rapport donné (ex. '2026-11-24 - Veille modèles locaux.md')."""
    fmt = cfg.get("obsidian", {}).get("format_nom", "{date} - Veille modèles locaux.md")
    return fmt.format(date=date_rapport)


def construire_note(date_rapport: str, contenu_rapport: str, cfg: dict) -> str:
    """Construit le contenu markdown de la note Obsidian (frontmatter + rapport)."""
    obs = cfg.get("obsidian", {})
    tags = obs.get("tags", ["veille", "modèles-locaux"])
    lignes = [
        "---",
        f"date: {date_rapport}",
        f"source: github.com/Zeelichisgood/veille-modeles-locaux (rapports/{date_rapport}.md)",
        "tags: [" + ", ".join(tags) + "]",
        "type: veille-modeles-locaux",
        "---",
        "",
        f"# Veille modèles locaux — {date_rapport}",
        "",
    ]
    # Le rapport contient déjà son propre titre H1 : on le garde tel quel.
    lignes.append(contenu_rapport.rstrip())
    lignes.append("")
    return "\n".join(lignes)


def lister_notes(vault: Path, dossier: str) -> list[Path]:
    """LECTURE SEULE : liste les notes existantes dans <vault>/<dossier> (ou le vault entier)."""
    base = vault / dossier if dossier else vault
    if not base.is_dir():
        raise FileNotFoundError(f"dossier introuvable ou non lisible : {base}")
    return sorted(p for p in base.glob("*.md") if p.is_file())


def rapports_a_synchroniser(dossier_rapports: Path, notes_existantes: list[Path],
                            cfg: dict) -> list[Path]:
    """Rapports du dépôt qui n'ont pas encore de note Obsidian correspondante."""
    noms_notes = {p.name for p in notes_existantes}
    restants = []
    for rapport in sorted(dossier_rapports.glob("*.md")):
        date_rapport = rapport.stem  # AAAA-MM-JJ
        if nom_fichier_note(date_rapport, cfg) in noms_notes:
            continue
        restants.append(rapport)
    return restants


# =====================================================================
# Programme principal
# =====================================================================


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Synchronise les rapports vers Obsidian (lecture seule par défaut).")
    parser.add_argument("--config", default=str(RACINE / "config.yaml"))
    parser.add_argument("--apply", action="store_true",
                        help="Écrire les notes manquantes (nécessite aussi ecriture_autorisee: true dans config.yaml).")
    args = parser.parse_args(argv)

    cfg = charger_config(Path(args.config))
    obs = cfg.get("obsidian", {})
    if not obs.get("active", False):
        print("Section 'obsidian' inactive dans config.yaml : rien à faire.")
        return 0

    vault_path = obs.get("vault_path", "")
    dossier = obs.get("dossier_notes", "Veille modèles locaux")
    if not vault_path:
        print("⚠️  obsidian.vault_path est vide dans config.yaml : indique le chemin de ton vault Obsidian.")
        print("    Exemple : vault_path: \"/Users/<toi>/Documents/Vault Obsidian\"")
        return 0
    vault = Path(vault_path).expanduser()
    if not vault.is_dir():
        print(f"⚠️  Vault illisible (accès non autorisé ou chemin faux) : {vault}")
        print("    Donne l'accès en lecture au dossier du vault dans la configuration de Vibe,")
        print("    puis renseigne ce chemin dans config.yaml.")
        return 0

    dossier_rapports = RACINE / cfg.get("rapport", {}).get("dossier", "rapports")
    try:
        notes = lister_notes(vault, dossier)
    except FileNotFoundError as e:
        print(f"⚠️  {e} — lecture seule impossible, aucune écriture tentée.")
        return 0
    print(f"📖 Vault lu (lecture seule) : {len(notes)} note(s) dans '{dossier or '.'}'.")

    a_sync = rapports_a_synchroniser(dossier_rapports, notes, cfg)
    if not a_sync:
        print("✅ Toutes les notes de veille sont déjà à jour dans Obsidian.")
        return 0

    ecriture_ok = bool(obs.get("ecriture_autorisee", False)) and args.apply
    for rapport in a_sync:
        note = construire_note(rapport.stem, rapport.read_text(encoding="utf-8"), cfg)
        cible = vault / dossier / nom_fichier_note(rapport.stem, cfg) if dossier else vault / nom_fichier_note(rapport.stem, cfg)
        if ecriture_ok:
            cible.parent.mkdir(parents=True, exist_ok=True)
            cible.write_text(note, encoding="utf-8")
            print(f"✍️  Note écrite : {cible}")
        else:
            print(f"🔎 [dry-run] Écrirait : {cible} ({len(note)} caractères)")
    if not ecriture_ok:
        print("\nAucun fichier n'a été modifié dans Obsidian (mode lecture seule).")
        print("Pour activer l'écriture : obsidian.ecriture_autorisee: true dans config.yaml, puis relancer avec --apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
