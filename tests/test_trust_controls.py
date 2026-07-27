from __future__ import annotations

import ast
from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE = ROOT / "docs" / "ARCHITECTURE.md"
CONTROL_TEST_MAP: dict[str, tuple[str, str]] = {
    "synthetic-markers-validated": (
        "test_validation.py",
        "test_validation_flags_each_corrupted_contract",
    ),
    "socket-guard": ("test_socket_guard.py", "test_direct_socket_connect_is_blocked"),
    "do-not-contact-override": (
        "test_services.py",
        "test_do_not_contact_orgs_are_excluded_from_outreach_queue",
    ),
    "drafts-human-reviewed": (
        "test_services.py",
        "test_outreach_drafts_are_synthetic_and_carry_no_delivery_capability",
    ),
    "no-applicant-level-output": (
        "test_ui_contract.py",
        "test_pipeline_health_never_renders_applicant_identifiers_or_names",
    ),
    "generated-artifacts-untracked": (
        "test_trust_controls.py",
        "test_generated_artifacts_directory_is_gitignored",
    ),
}


def _extract_control_ids() -> tuple[bool, set[str]]:
    text = ARCHITECTURE.read_text(encoding="utf-8")
    match = re.search(r"^## Trust controls\s*$([\s\S]*?)(?=^##\s|\Z)", text, re.MULTILINE)
    if match is None:
        return False, set()
    return True, set(re.findall(r"<!-- control: ([a-z0-9-]+) -->", match.group(1)))


def test_trust_controls_sweep_covers_every_documented_control():
    heading_found, control_ids = _extract_control_ids()

    assert heading_found
    assert control_ids == set(CONTROL_TEST_MAP)
    assert len(control_ids) >= 6
    assert {"do-not-contact-override", "socket-guard"} <= control_ids


@pytest.mark.parametrize("control_id", sorted(CONTROL_TEST_MAP))
def test_control_maps_to_an_existing_test(control_id):
    filename, function_name = CONTROL_TEST_MAP[control_id]
    tree = ast.parse((ROOT / "tests" / filename).read_text(encoding="utf-8"))

    assert any(
        isinstance(node, ast.FunctionDef) and node.name == function_name
        for node in ast.walk(tree)
    )


def test_generated_artifacts_directory_is_gitignored():
    ignored_lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "data/generated/" in ignored_lines
