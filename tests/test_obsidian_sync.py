# -*- coding: utf-8 -*-
"""
Tests du pont Obsidian (obsidian_sync.py) : construction de la note datée,
nom de fichier, détection des doublons, et garde-fou « lecture seule ».

Lancement : python3 -m pytest tests/ -q
Aucun accès à un vrai vault n'est nécessaire (répertoires temporaires).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import obsidian_sync  # noqa: E402


@pytest.fixture()
def cfg():
    return {
        "rapport": {"dossier": "rapports"},
        "obsidian": {
            "active": True,
            "vault_path": "",
            "dossier_notes": "Veille modèles locaux",
            "format_nom": "{date} - Veille modèles locaux.md",
            "tags": ["veille", "modèles-locaux"],
            "ecriture_autorisee": False,
        },
    }


def test_nom_fichier_note(cfg):
    assert obsidian_sync.nom_fichier_note("2026-11-24", cfg) == "2026-11-24 - Veille modèles locaux.md"


def test_construire_note_frontmatter_et_contenu(cfg):
    rapport = "# Veille modèles locaux — rapport du 2026-11-24\n\n## Verdict\n\n**À tester : `x`**\n"
    note = obsidian_sync.construire_note("2026-11-24", rapport, cfg)
    # Frontmatter Obsidian (YAML entre ---) avec date, source et tags
    assert note.startswith("---\n")
    assert "date: 2026-11-24" in note
    assert "source: github.com/" in note and "rapports/2026-11-24.md" in note
    assert "tags: [veille, modèles-locaux]" in note
    assert "type: veille-modeles-locaux" in note
    # Le contenu du rapport est repris tel quel
    assert "# Veille modèles locaux — rapport du 2026-11-24" in note
    assert "**À tester : `x`**" in note
    # Le frontmatter est refermé avant le contenu
    assert note.count("---") >= 2


def test_rapports_a_synchroniser_detecte_les_doublons(cfg, tmp_path):
    # Deux rapports dans le dépôt
    rapports = tmp_path / "rapports"
    rapports.mkdir()
    (rapports / "2026-11-17.md").write_text("rapport A", encoding="utf-8")
    (rapports / "2026-11-24.md").write_text("rapport B", encoding="utf-8")
    # Le vault contient déjà la note du 17 novembre
    vault = tmp_path / "vault"
    dossier = vault / "Veille modèles locaux"
    dossier.mkdir(parents=True)
    note_existante = dossier / "2026-11-17 - Veille modèles locaux.md"
    note_existante.write_text("déjà là", encoding="utf-8")

    notes = obsidian_sync.lister_notes(vault, "Veille modèles locaux")
    assert notes == [note_existante]

    restants = obsidian_sync.rapports_a_synchroniser(rapports, notes, cfg)
    assert [p.name for p in restants] == ["2026-11-24.md"]  # seul le 24 manque


def test_lister_notes_vault_illisible(cfg, tmp_path):
    with pytest.raises(FileNotFoundError):
        obsidian_sync.lister_notes(tmp_path / "inexistant", "Veille modèles locaux")


def test_mode_lecture_seule_par_defaut(cfg, tmp_path):
    """Sans --apply et avec ecriture_autorisee: false, aucun fichier n'est créé dans le vault."""
    import yaml
    import obsidian_sync as osync

    rapports = tmp_path / "rapports"
    rapports.mkdir()
    (rapports / "2026-11-24.md").write_text("# rapport\n", encoding="utf-8")
    vault = tmp_path / "vault"
    (vault / "Veille modèles locaux").mkdir(parents=True)

    cfg["obsidian"]["vault_path"] = str(vault)
    cfg_fichier = tmp_path / "config.yaml"
    cfg_fichier.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")

    old = osync.RACINE
    osync.RACINE = tmp_path
    try:
        code = osync.main(["--config", str(cfg_fichier)])  # sans --apply
    finally:
        osync.RACINE = old
    assert code == 0
    # Aucune note écrite dans le vault (lecture seule)
    assert list((vault / "Veille modèles locaux").glob("*.md")) == []


def test_mode_ecriture_refuse_sans_autorisation(cfg, tmp_path):
    """Même avec --apply, l'écriture est refusée si ecriture_autorisee: false."""
    import yaml
    import obsidian_sync as osync

    rapports = tmp_path / "rapports"
    rapports.mkdir()
    (rapports / "2026-11-24.md").write_text("# rapport\n", encoding="utf-8")
    vault = tmp_path / "vault"
    (vault / "Veille modèles locaux").mkdir(parents=True)

    cfg["obsidian"]["vault_path"] = str(vault)
    cfg["obsidian"]["ecriture_autorisee"] = False  # pas d'autorisation
    cfg_fichier = tmp_path / "config.yaml"
    cfg_fichier.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")

    old = osync.RACINE
    osync.RACINE = tmp_path
    try:
        code = osync.main(["--config", str(cfg_fichier), "--apply"])
    finally:
        osync.RACINE = old
    assert code == 0
    assert list((vault / "Veille modèles locaux").glob("*.md")) == []


def test_mode_ecriture_avec_autorisation(cfg, tmp_path):
    """Avec --apply ET ecriture_autorisee: true, la note datée est écrite dans le vault."""
    import yaml
    import obsidian_sync as osync

    rapports = tmp_path / "rapports"
    rapports.mkdir()
    (rapports / "2026-11-24.md").write_text("# Veille modèles locaux — rapport du 2026-11-24\n\nVerdict…\n", encoding="utf-8")
    vault = tmp_path / "vault"
    (vault / "Veille modèles locaux").mkdir(parents=True)

    cfg["obsidian"]["vault_path"] = str(vault)
    cfg["obsidian"]["ecriture_autorisee"] = True
    cfg_fichier = tmp_path / "config.yaml"
    cfg_fichier.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")

    old = osync.RACINE
    osync.RACINE = tmp_path
    try:
        code = osync.main(["--config", str(cfg_fichier), "--apply"])
    finally:
        osync.RACINE = old
    assert code == 0
    note = vault / "Veille modèles locaux" / "2026-11-24 - Veille modèles locaux.md"
    assert note.exists()
    contenu = note.read_text(encoding="utf-8")
    assert "date: 2026-11-24" in contenu
    assert "Verdict…" in contenu
