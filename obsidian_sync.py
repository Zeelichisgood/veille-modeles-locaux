#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
obsidian_sync.py — génère une note Obsidian datée par run de la veille.

Principe en DEUX TEMPS (décidé avec l'utilisateur) :
  1. Chaque rapport rapports/AAAA-MM-JJ.md devient une note markdown prête pour
     Obsidian (frontmatter YAML + contenu du rapport) dans le dossier `notes/`
     DU PROJET (configurable via notes.dossier dans config.yaml).
  2. Plus tard, Obsidian sera branché sur ce dossier `notes/` (vault déplacé,
     synchro iCloud, plugin…) — géré hors de ce script.

SÉCURITÉ :
  - Le script n'écrit QUE dans le dossier `notes/` du projet, jamais ailleurs.
  - Sans `--apply`, il fait un dry-run (liste ce qu'il écrirait, n'écrit rien).
  - L'écriture exige `notes.ecriture_autorisee: true` dans config.yaml ET `--apply`.

Usage :
    python3 obsidian_sync.py            # dry-run (lecture seule)
    python3 obsidian_sync.py --apply    # écrit les notes manquantes dans notes/

Dépendances : pyyaml.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent


# =====================================================================
# Fonctions pures (testées par pytest)
# =====================================================================


def charger_config(chemin: Path) -> dict:
    with open(chemin, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def dossier_notes(cfg: dict) -> Path:
    """Dossier cible des notes, toujours DANS le dépôt (jamais ailleurs)."""
    rel = cfg.get("notes", {}).get("dossier", "notes")
    cible = (RACINE / rel).resolve()
    # Garde-fou absolu : la cible doit rester dans le dépôt.
    if RACINE.resolve() not in cible.parents and cible != RACINE.resolve():
        raise ValueError(f"notes.dossier doit rester dans le dépôt : {rel}")
    return cible


def nom_fichier_note(date_rapport: str, cfg: dict) -> str:
    """Nom de la note pour un rapport (ex. '2026-11-24 - Veille modèles locaux.md')."""
    fmt = cfg.get("notes", {}).get("format_nom", "{date} - Veille modèles locaux.md")
    return fmt.format(date=date_rapport)


def construire_note(date_rapport: str, contenu_rapport: str, cfg: dict) -> str:
    """Contenu markdown de la note : frontmatter Obsidian + rapport complet."""
    notes = cfg.get("notes", {})
    tags = notes.get("tags", ["veille", "modèles-locaux"])
    return "\n".join([
        "---",
        f"date: {date_rapport}",
        f"source: rapports/{date_rapport}.md (github.com/Zeelichisgood/veille-modeles-locaux)",
        "tags: [" + ", ".join(tags) + "]",
        "type: veille-modeles-locaux",
        "---",
        "",
        contenu_rapport.rstrip(),
        "",
    ])


def lister_notes(dossier: Path) -> list[Path]:
    """LECTURE : notes déjà présentes dans le dossier cible (vide s'il n'existe pas)."""
    if not dossier.is_dir():
        return []
    return sorted(p for p in dossier.glob("*.md") if p.is_file())


def rapports_a_synchroniser(dossier_rapports: Path, notes_existantes: list[Path], cfg: dict) -> list[Path]:
    """Rapports du dépôt qui n'ont pas encore de note correspondante."""
    noms_notes = {p.name for p in notes_existantes}
    return [r for r in sorted(dossier_rapports.glob("*.md"))
            if nom_fichier_note(r.stem, cfg) not in noms_notes]


# =====================================================================
# Programme principal
# =====================================================================


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Génère les notes Obsidian des rapports (dry-run par défaut).")
    parser.add_argument("--config", default=str(RACINE / "config.yaml"))
    parser.add_argument("--apply", action="store_true",
                        help="Écrire les notes manquantes (nécessite aussi notes.ecriture_autorisee: true).")
    args = parser.parse_args(argv)

    cfg = charger_config(Path(args.config))
    notes_cfg = cfg.get("notes", {})
    if not notes_cfg.get("active", False):
        print("Section 'notes' inactive dans config.yaml : rien à faire.")
        return 0

    cible = dossier_notes(cfg)
    dossier_rapports = RACINE / cfg.get("rapport", {}).get("dossier", "rapports")
    if not dossier_rapports.is_dir():
        print(f"⚠️  Aucun dossier de rapports lisible : {dossier_rapports}")
        return 0

    notes = lister_notes(cible)
    print(f"📖 {len(notes)} note(s) déjà présente(s) dans {cible.relative_to(RACINE)}/.")

    a_sync = rapports_a_synchroniser(dossier_rapports, notes, cfg)
    if not a_sync:
        print("✅ Toutes les notes sont déjà à jour.")
        return 0

    ecriture_ok = bool(notes_cfg.get("ecriture_autorisee", False)) and args.apply
    for rapport in a_sync:
        note = construire_note(rapport.stem, rapport.read_text(encoding="utf-8"), cfg)
        cible_fichier = cible / nom_fichier_note(rapport.stem, cfg)
        if ecriture_ok:
            cible.mkdir(parents=True, exist_ok=True)
            cible_fichier.write_text(note, encoding="utf-8")
            print(f"✍️  Note écrite : {cible_fichier.relative_to(RACINE)}")
        else:
            print(f"🔎 [dry-run] Écrirait : {cible_fichier.relative_to(RACINE)} ({len(note)} caractères)")
    if not ecriture_ok:
        print("\nAucune note écrite (mode lecture seule).")
        print("Pour activer l'écriture dans le dossier notes/ du projet :")
        print("  notes.ecriture_autorisee: true dans config.yaml, puis relancer avec --apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
