from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
VALIDATE_REPO_SCRIPT = ROOT / "scripts" / "validate_repo.py"


def _load_validate_repo_module():
    spec = importlib.util.spec_from_file_location("validate_repo", VALIDATE_REPO_SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_load_published_external_benchmark_registry_accepts_current_registry() -> None:
    validate_repo = _load_validate_repo_module()

    descriptors = validate_repo.load_published_external_benchmark_registry(
        ROOT / "docs" / "examples" / "published-external-benchmarks.json",
        root=ROOT,
    )

    assert [descriptor["id"] for descriptor in descriptors] == [
        "retrospective-sample",
        "wording-variance-sample",
    ]


def test_load_published_external_benchmark_registry_rejects_duplicate_ids(tmp_path: Path) -> None:
    validate_repo = _load_validate_repo_module()
    (tmp_path / "sample-a.json").write_text("{}\n")
    (tmp_path / "sample-b.json").write_text("{}\n")

    registry_path = tmp_path / "published-external-benchmarks.json"
    registry_path.write_text(
        json.dumps(
            [
                {
                    "id": "duplicate-pack",
                    "label": "Pack A",
                    "title": "Pack A",
                    "description": "First duplicate entry.",
                    "snapshot_path": "sample-a.json",
                },
                {
                    "id": "duplicate-pack",
                    "label": "Pack B",
                    "title": "Pack B",
                    "description": "Second duplicate entry.",
                    "snapshot_path": "sample-b.json",
                },
            ]
        )
    )

    with pytest.raises(ValueError, match="duplicate id"):
        validate_repo.load_published_external_benchmark_registry(registry_path, root=tmp_path)


def test_load_published_external_benchmark_registry_rejects_missing_snapshot_file(tmp_path: Path) -> None:
    validate_repo = _load_validate_repo_module()
    registry_path = tmp_path / "published-external-benchmarks.json"
    registry_path.write_text(
        json.dumps(
            [
                {
                    "id": "missing-pack",
                    "label": "Missing Pack",
                    "title": "Missing Pack",
                    "description": "Entry with a missing snapshot.",
                    "snapshot_path": "missing.json",
                }
            ]
        )
    )

    with pytest.raises(ValueError, match="references missing file"):
        validate_repo.load_published_external_benchmark_registry(registry_path, root=tmp_path)
