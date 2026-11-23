# -*- coding: utf-8 -*-
"""
Tests du générateur de notes Obsidian (obsidian_sync.py) : construction de la
note datée (frontmatter), nom de fichier, détection des doublons, garde-fou
« dry-run par défaut » et « écriture uniquement dans le dossier notes/ du projet ».

Lancement : python3 -m pytest tests/ -q
Aucun accès à un vrai vault Obsidian n'est nécessaire (répertoires temporaires).
"""

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import obsidian_sync  # noqa: E402


@pytest.fixture()
def cfg():
    return {
        "rapport": {"dossier": "rapports"},
        "notes": {
            "active": True,
            "dossier": "notes",
            "format_nom": "{date} - Veille modèles locaux.md",
            "tags": ["veille", "modèles-locaux"],
            "ecriture_autorisee": True,
        },
    }


def test_nom_fichier_note(cfg):
    assert obsidian_sync.nom_fichier_note("2026-11-24", cfg) == "2026-11-24 - Veille modèles locaux.md"


def test_construire_note_frontmatter_et_contenu(cfg):
    rapport = "# Veille modèles locaux — rapport du 2026-11-24\n\n## Verdict\n\n**À tester : `x`**\n"
    note = obsidian_sync.construire_note("2026-11-24", rapport, cfg)
    assert note.startswith("---\n")
    assert "date: 2026-11-24" in note
    assert "source: rapports/2026-11-24.md" in note
    assert "tags: [veille, modèles-locaux]" in note
    assert "type: veille-modeles-locaux" in note
    assert "# Veille modèles locaux — rapport du 2026-11-24" in note
    assert "**À tester : `x`**" in note


def test_dossier_notes_reste_dans_le_depot(cfg, tmp_path, monkeypatch):
    monkeypatch.setattr(obsidian_sync, "RACINE", tmp_path)
    assert obsidian_sync.dossier_notes(cfg) == tmp_path / "notes"
    cfg["notes"]["dossier"] = "../hors_du_depot"
    with pytest.raises(ValueError):
        obsidian_sync.dossier_notes(cfg)


def test_rapports_a_synchroniser_detecte_les_doublons(cfg, tmp_path):
    rapports = tmp_path / "rapports"
    rapports.mkdir()
    (rapports / "2026-11-17.md").write_text("rapport A", encoding="utf-8")
    (rapports / "2026-11-24.md").write_text("rapport B", encoding="utf-8")
    notes = tmp_path / "notes"
    notes.mkdir()
    note_existante = notes / "2026-11-17 - Veille modèles locaux.md"
    note_existante.write_text("déjà là", encoding="utf-8")

    restants = obsidian_sync.rapports_a_synchroniser(rapports, obsidian_sync.lister_notes(notes), cfg)
    assert [p.name for p in restants] == ["2026-11-24.md"]  # seul le 24 manque


def _prepare(tmp_path, cfg, ecriture: bool, apply_flag: bool):
    """Prépare un faux dépôt (rapports/ + config) et un faux RACINE, puis appelle main()."""
    rapports = tmp_path / "rapports"
    rapports.mkdir(exist_ok=True)
    (rapports / "2026-11-24.md").write_text("# rapport du 24\n", encoding="utf-8")
    cfg["notes"]["ecriture_autorisee"] = ecriture
    cfg_fichier = tmp_path / "config.yaml"
    cfg_fichier.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
    old = obsidian_sync.RACINE
    obsidian_sync.RACINE = tmp_path
    try:
        args = ["--config", str(cfg_fichier)] + (["--apply"] if apply_flag else [])
        code = obsidian_sync.main(args)
    finally:
        obsidian_sync.RACINE = old
    return code, tmp_path / "notes"


def test_dry_run_par_defaut_n_ecrit_rien(cfg, tmp_path):
    code, notes = _prepare(tmp_path, cfg, ecriture=True, apply_flag=False)
    assert code == 0
    assert not notes.exists() or list(notes.glob("*.md")) == []


def test_apply_refuse_sans_autorisation(cfg, tmp_path):
    code, notes = _prepare(tmp_path, cfg, ecriture=False, apply_flag=True)
    assert code == 0
    assert not notes.exists() or list(notes.glob("*.md")) == []


def test_apply_ecrit_la_note_dans_notes_du_projet(cfg, tmp_path):
    code, notes = _prepare(tmp_path, cfg, ecriture=True, apply_flag=True)
    assert code == 0
    note = notes / "2026-11-24 - Veille modèles locaux.md"
    assert note.exists()
    contenu = note.read_text(encoding="utf-8")
    assert "date: 2026-11-24" in contenu
    assert "# rapport du 24" in contenu
    # La note reste DANS le dossier notes/ du projet, jamais ailleurs
    assert note.parent == notes
