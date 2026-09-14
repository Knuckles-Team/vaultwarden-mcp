import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONCEPTS_DOC = ROOT / "docs" / "concepts.md"
PACKAGE_DIR = ROOT / "vaultwarden_mcp"

_MARKER_RE = re.compile(r"CONCEPT:(VW-[A-Za-z0-9][A-Za-z0-9.\-]*)")


def _markers_in_code() -> set[str]:
    """Every ``CONCEPT:VW-…`` marker found anywhere under ``vaultwarden_mcp/**/*.py``."""
    markers: set[str] = set()
    for path in PACKAGE_DIR.rglob("*.py"):
        markers.update(_MARKER_RE.findall(path.read_text(encoding="utf-8")))
    return markers


@pytest.mark.concept("VW-OS.governance.concept-registry")
def test_concepts_doc_exists():
    """Concept registry doc exists. CONCEPT:VW-OS.governance.concept-registry"""
    assert CONCEPTS_DOC.is_file()


@pytest.mark.concept("VW-OS.governance.concept-registry")
def test_prefix_registered():
    """Project concept prefix is registered. CONCEPT:VW-OS.governance.concept-registry"""
    assert "VW-" in CONCEPTS_DOC.read_text(encoding="utf-8")


@pytest.mark.concept("VW-OS.governance.concept-registry")
def test_every_code_marker_is_registered():
    """Every CONCEPT:VW-* marker in code appears in the concepts registry.

    CONCEPT:VW-OS.governance.concept-registry
    """
    registry_text = CONCEPTS_DOC.read_text(encoding="utf-8")
    code_markers = _markers_in_code()
    missing = sorted(marker for marker in code_markers if marker not in registry_text)
    assert not missing, f"CONCEPT:VW-* markers missing from docs/concepts.md: {missing}"
