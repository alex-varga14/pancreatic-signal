from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import autoresearch as autoresearch_service
from app.services import ontology as ontology_module


def _auth_headers(user_id: str, role: str) -> dict[str, str]:
    return {"X-User-ID": user_id, "X-User-Role": role}


@pytest.fixture()
def autoresearch_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Stand up a fake project layout in tmp and point the service at it."""

    project_root = tmp_path / "project"
    runs_dir = project_root / "autoresearch" / "runs"
    baseline_dir = project_root / "autoresearch" / "baseline"
    ontology_dir = project_root / "data" / "ontologies"
    runs_dir.mkdir(parents=True)
    baseline_dir.mkdir(parents=True)
    ontology_dir.mkdir(parents=True)

    bundled_ontology = copy.deepcopy(ontology_module.load_ontology())
    baseline_path = baseline_dir / "pancreatic_signal_rules.json"
    ontology_path = ontology_dir / "pancreatic_signal_rules.json"
    baseline_path.write_text(json.dumps(bundled_ontology, indent=2) + "\n")
    ontology_path.write_text(json.dumps(bundled_ontology, indent=2) + "\n")

    monkeypatch.setattr(autoresearch_service, "_project_root", lambda: project_root)
    monkeypatch.setattr(
        autoresearch_service,
        "_baseline_path",
        lambda: baseline_path,
    )
    monkeypatch.setattr(
        autoresearch_service,
        "_audit_log_path",
        lambda: project_root / "autoresearch" / "promotion_audit.jsonl",
    )
    monkeypatch.setattr(ontology_module, "ONTOLOGY_PATH", ontology_path)
    ontology_module.load_ontology.cache_clear()

    yield project_root

    ontology_module.load_ontology.cache_clear()


def _seed_run(
    project_root: Path,
    *,
    run_id: str,
    status: str,
    primary_value: float | None = 0.92,
    baseline_value: float | None = 0.85,
    delta: float | None = 0.07,
    candidate: dict | None = None,
    notes: str | None = None,
) -> Path:
    run_dir = project_root / "autoresearch" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    decision = {
        "status": status,
        "primary_metric": "f1_at_top_k_demo_rules",
        "primary_value": primary_value,
        "baseline_value": baseline_value,
        "delta": delta,
        "reasons": [],
    }
    (run_dir / "decision.json").write_text(json.dumps(decision, indent=2))
    if candidate is not None:
        (run_dir / "proposal.json").write_text(json.dumps(candidate, indent=2))
    if notes is not None:
        (run_dir / "notes.md").write_text(notes)
    (run_dir / "eval.json").write_text(json.dumps({"primary_metric": "f1_at_top_k_demo_rules"}))
    (run_dir / "diff.json").write_text(json.dumps({"family_changes": []}))
    return run_dir


def test_list_runs_returns_recent_runs(autoresearch_workspace: Path) -> None:
    _seed_run(autoresearch_workspace, run_id="2026-04-25T10-00-00Z", status="kept")
    _seed_run(autoresearch_workspace, run_id="2026-04-26T10-00-00Z", status="discarded_no_improvement", primary_value=0.81, delta=-0.04)

    client = TestClient(app)
    response = client.get(
        "/api/v1/autoresearch/runs",
        headers=_auth_headers("nav-1", "navigator"),
    )
    assert response.status_code == 200
    payload = response.json()
    assert {item["run_id"] for item in payload} == {
        "2026-04-25T10-00-00Z",
        "2026-04-26T10-00-00Z",
    }


def test_list_runs_rejects_viewer_role(autoresearch_workspace: Path) -> None:
    _seed_run(autoresearch_workspace, run_id="2026-04-25T10-00-00Z", status="kept")
    client = TestClient(app)
    response = client.get(
        "/api/v1/autoresearch/runs",
        headers=_auth_headers("v-1", "viewer"),
    )
    assert response.status_code == 403


def test_run_detail_returns_404_for_unknown_run(autoresearch_workspace: Path) -> None:
    client = TestClient(app)
    response = client.get(
        "/api/v1/autoresearch/runs/never-existed",
        headers=_auth_headers("nav-1", "navigator"),
    )
    assert response.status_code == 404


def test_leaderboard_returns_only_kept_runs_sorted_by_primary_value(
    autoresearch_workspace: Path,
) -> None:
    _seed_run(autoresearch_workspace, run_id="run-a", status="kept", primary_value=0.90, delta=0.05)
    _seed_run(autoresearch_workspace, run_id="run-b", status="kept", primary_value=0.95, delta=0.10)
    _seed_run(autoresearch_workspace, run_id="run-c", status="discarded_no_improvement", primary_value=0.82, delta=-0.03)

    client = TestClient(app)
    response = client.get(
        "/api/v1/autoresearch/leaderboard",
        headers=_auth_headers("nav-1", "navigator"),
    )
    assert response.status_code == 200
    payload = response.json()
    assert [run["run_id"] for run in payload["runs"]] == ["run-b", "run-a"]


def test_promote_requires_admin(autoresearch_workspace: Path) -> None:
    bundled = copy.deepcopy(ontology_module.load_ontology())
    _seed_run(
        autoresearch_workspace,
        run_id="run-promote",
        status="kept",
        candidate=bundled,
    )
    client = TestClient(app)
    response = client.post(
        "/api/v1/autoresearch/promote/run-promote",
        headers=_auth_headers("nav-1", "navigator"),
    )
    assert response.status_code == 403


def test_promote_kept_run_writes_promotion_record(autoresearch_workspace: Path) -> None:
    bundled = copy.deepcopy(ontology_module.load_ontology())
    bundled["families"][0]["weight"] = 0.6
    run_dir = _seed_run(
        autoresearch_workspace,
        run_id="run-promote-ok",
        status="kept",
        candidate=bundled,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/autoresearch/promote/run-promote-ok",
        headers=_auth_headers("admin-1", "admin"),
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["run_id"] == "run-promote-ok"
    assert payload["ontology_target"].endswith("pancreatic_signal_rules.json")

    promotion_file = run_dir / "promotion.json"
    assert promotion_file.exists()
    written = json.loads(promotion_file.read_text())
    assert written["actor_user_id"] == "admin-1"

    promoted_ontology = json.loads(ontology_module.ONTOLOGY_PATH.read_text())
    assert promoted_ontology["families"][0]["weight"] == 0.6


def test_promote_rejects_non_kept_run(autoresearch_workspace: Path) -> None:
    bundled = copy.deepcopy(ontology_module.load_ontology())
    _seed_run(
        autoresearch_workspace,
        run_id="run-not-kept",
        status="discarded_no_improvement",
        candidate=bundled,
    )
    client = TestClient(app)
    response = client.post(
        "/api/v1/autoresearch/promote/run-not-kept",
        headers=_auth_headers("admin-1", "admin"),
    )
    assert response.status_code == 400
    assert "kept" in response.json()["detail"]
