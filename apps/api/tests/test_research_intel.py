from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.research_intel import ResearchCouncilPayload, ResearchOpportunityActionPayload
from app.store.memory_store import CASE_STORE


def _auth_headers(user_id: str, role: str = "admin") -> dict[str, str]:
    return {"X-User-ID": user_id, "X-User-Role": role}


def _triage_case(client: TestClient, *, case_id: str, report_id: str) -> None:
    response = client.post(
        "/api/v1/triage/report",
        json={
            "report_id": report_id,
            "case_id": case_id,
            "report_datetime": "2026-03-19T10:00:00Z",
            "modality": "CT",
            "site": "Demo Hospital",
            "report_text": (
                "Findings: Abrupt cutoff of the pancreatic duct with focal atrophy. "
                "Impression: Suspicious for pancreatic neoplasm. Recommend EUS and biopsy."
            ),
        },
    )
    assert response.status_code == 200


def _artifact_text(relative_path: str) -> str:
    return (Path(__file__).resolve().parents[3] / relative_path).read_text(encoding="utf-8")


def test_research_intel_ingest_digest_and_promotion_routes() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    response = client.get("/api/v1/research-intel/sources")
    assert response.status_code == 200
    assert any(item["source_id"] == "pubmed" for item in response.json())
    assert any(item["source_id"] == "pubmed_early_detection" for item in response.json())

    response = client.post(
        "/api/v1/research-intel/runs/ingest",
        json={"mode": "fixture", "write_artifacts": True},
        headers=_auth_headers("research-admin"),
    )
    assert response.status_code == 200
    run_payload = response.json()["run"]
    assert run_payload["run_type"] == "ingest"
    assert run_payload["processed"] >= 6
    assert run_payload["created"] >= 6
    assert run_payload["metadata"]["requested_mode"] == "fixture"
    assert len(run_payload["items"]) >= run_payload["processed"]

    response = client.get(
        "/api/v1/research-intel/runs",
        headers=_auth_headers("research-admin"),
    )
    assert response.status_code == 200
    assert response.json()[0]["run_type"] == "ingest"

    response = client.get("/api/v1/research-intel/documents")
    assert response.status_code == 200
    documents = response.json()
    assert any(item["nct_id"] == "NCT06001234" for item in documents)
    assert any("early_detection" in item["topic_ids"] for item in documents)
    assert all(item["ingest_mode"] == "fixture" for item in documents)
    assert all(item["provenance"]["connector_id"] for item in documents)
    assert any(item["novelty_score"] for item in documents)
    assert any(any(entity["node_id"] == "liquid_biopsy" for entity in item["graph_entities"]) for item in documents)
    assert any(any(entity["node_id"] == "neoadjuvant_therapy" for entity in item["graph_entities"]) for item in documents)
    assert any(any(entity["node_id"] == "biomarker_stratification" for entity in item["graph_entities"]) for item in documents)
    assert any(any(entity["node_id"] == "segmentation_labels" for entity in item["graph_entities"]) for item in documents)
    assert any(any(entity["family_id"] == "molecular_detection" for entity in item["graph_entities"]) for item in documents)
    assert any(any(entity["match_strategy"] for entity in item["graph_entities"]) for item in documents)

    response = client.get("/api/v1/research-intel/sources")
    assert response.status_code == 200
    sources = response.json()
    pubmed = next(item for item in sources if item["source_id"] == "pubmed")
    assert pubmed["health_status"] == "healthy"
    assert pubmed["last_success_at"]
    assert pubmed["connector_id"] == "europe_pmc_search"
    assert pubmed["default_mode"] == "fixture"
    assert pubmed["schedule_state"] == "scheduled"
    assert pubmed["next_run_at"]
    assert pubmed["interval_hours"] == 12

    response = client.get("/api/v1/research-intel/schedule")
    assert response.status_code == 200
    schedule = response.json()
    assert schedule["due_count"] == 0
    assert schedule["scheduled_count"] >= 1
    assert schedule["live_ready_count"] >= 5

    response = client.get("/api/v1/research-intel/graph")
    assert response.status_code == 200
    graph = response.json()
    assert graph["nodes"]
    assert graph["edges"]
    assert "liquid_biopsy" in graph["active_node_ids"]
    liquid_biopsy = next(item for item in graph["nodes"] if item["node_id"] == "liquid_biopsy")
    assert liquid_biopsy["document_count"] >= 1
    assert liquid_biopsy["family_id"] == "molecular_detection"
    assert "high_risk_screening" in liquid_biopsy["related_node_ids"]
    assert any(item["node_id"] == "segmentation_labels" and item["document_count"] >= 1 for item in graph["nodes"])

    response = client.post(
        "/api/v1/research-intel/runs/digest",
        json={"publish": True, "write_artifacts": True},
        headers=_auth_headers("research-admin"),
    )
    assert response.status_code == 200
    digest_run = response.json()["run"]
    assert digest_run["run_type"] == "digest"
    assert digest_run["created"] >= 1
    assert any(path.startswith("artifacts/research-intel/opportunities/") for path in digest_run["artifact_paths"])

    response = client.get("/api/v1/research-intel/digests")
    assert response.status_code == 200
    digests = response.json()
    assert len(digests) == 1
    digest_id = digests[0]["digest_id"]

    response = client.get(f"/api/v1/research-intel/digests/{digest_id}")
    assert response.status_code == 200
    digest = response.json()
    assert digest["supporting_documents"]
    assert len(digest["council"]["stage_1"]) == 3
    assert all(item["confidence_label"] for item in digest["council"]["stage_1"])
    assert all(item["open_questions"] for item in digest["council"]["stage_1"])
    assert all(item["evidence_gaps"] for item in digest["council"]["stage_1"])
    assert all(item["peer_critiques"] for item in digest["council"]["stage_2"])
    assert all(item["preferred_actions"] for item in digest["council"]["stage_2"])
    assert digest["council"]["stage_3"]["overall_confidence"] in {"high", "medium", "low"}
    assert digest["council"]["stage_3"]["open_questions"]
    assert digest["council"]["stage_3"]["evidence_gaps"]
    assert digest["council"]["stage_3"]["next_experiments"]
    assert digest["council"]["stage_3"]["promotion_guardrails"]
    assert digest["council"]["stage_3"]["recommended_actions"]
    assert "Open questions:" in digest["summary_markdown"]
    assert "Promotion guardrails:" in digest["summary_markdown"]

    response = client.get("/api/v1/research-intel/opportunities")
    assert response.status_code == 200
    opportunities = response.json()
    assert opportunities
    first_opportunity = opportunities[0]
    opportunity_id = first_opportunity["opportunity_id"]
    assert first_opportunity["action_payload"]["objective"]
    assert first_opportunity["action_payload"]["why_now"]
    assert first_opportunity["action_payload"]["discovery_question"]
    assert first_opportunity["action_payload"]["artifact_spec"]["artifact_kind"]
    assert first_opportunity["action_payload"]["artifact_spec"]["suggested_path"]
    assert first_opportunity["action_payload"]["evidence_bundle"]
    assert first_opportunity["action_payload"]["proposed_steps"]
    assert first_opportunity["action_payload"]["measurable_outcomes"]
    assert first_opportunity["action_payload"]["promotion_guardrails"]
    assert first_opportunity["action_payload"]["contributor_packets"]

    opportunity_artifact_path = next(
        path
        for path in digest_run["artifact_paths"]
        if path.startswith(f"artifacts/research-intel/opportunities/{opportunity_id}")
        and path.endswith(".md")
    )
    opportunity_artifact_text = _artifact_text(opportunity_artifact_path)
    assert "## Objective" in opportunity_artifact_text
    assert "## Evidence bundle" in opportunity_artifact_text
    assert "## Suggested downstream artifact" in opportunity_artifact_text
    assert "## Contributor packets" in opportunity_artifact_text

    supported_opportunity = next(
        item for item in opportunities if item["opportunity_type"] in {"benchmark_gap", "rule_gap"}
    )
    experiment_kind = (
        "benchmark_stress_test"
        if supported_opportunity["opportunity_type"] == "benchmark_gap"
        else "rule_stress_test"
    )
    experiment_response = client.post(
        f"/api/v1/research-intel/opportunities/{supported_opportunity['opportunity_id']}/experiment",
        json={"write_artifacts": True, "experiment_kind": experiment_kind},
        headers=_auth_headers("research-admin"),
    )
    assert experiment_response.status_code == 200
    experiment_run = experiment_response.json()["run"]
    assert experiment_run["run_type"] == "experiment"
    assert experiment_run["metadata"]["ratchet_outcome"] in {"keep", "discard"}
    assert experiment_run["metadata"]["metric_name"]
    assert experiment_run["metadata"]["experiment_kind"] == experiment_kind
    assert any(path.startswith("artifacts/research-intel/experiments/") for path in experiment_run["artifact_paths"])

    experiment_artifact_path = next(
        path for path in experiment_run["artifact_paths"] if path.endswith(".md")
    )
    experiment_artifact_text = _artifact_text(experiment_artifact_path)
    assert "## Scores" in experiment_artifact_text
    assert "## Scored dimensions" in experiment_artifact_text
    assert "## Acceptance gates" in experiment_artifact_text

    opportunities_after_experiment = client.get("/api/v1/research-intel/opportunities").json()
    experimented = next(
        item for item in opportunities_after_experiment if item["opportunity_id"] == supported_opportunity["opportunity_id"]
    )
    assert experimented["action_payload"]["last_experiment"]["metric_name"]
    assert experimented["action_payload"]["last_experiment"]["ratchet_outcome"] in {"keep", "discard"}
    assert experimented["action_payload"]["last_experiment"]["artifact_paths"]
    assert experimented["action_payload"]["last_experiment"]["experiment_summary"]
    assert experimented["action_payload"]["last_experiment"]["scored_dimensions"]

    promote_response = client.post(
        f"/api/v1/research-intel/opportunities/{opportunity_id}/promote",
        json={"target": "docs_draft"},
        headers=_auth_headers("research-admin"),
    )
    assert promote_response.status_code == 200
    assert promote_response.json()["status"] == "promoted"
    assert promote_response.json()["artifact_path"]
    promotion_text = _artifact_text(promote_response.json()["artifact_path"])
    assert "## Discovery question" in promotion_text
    assert "## Evidence bundle" in promotion_text
    assert "## Measurable outcomes" in promotion_text
    assert "## Contributor packets" in promotion_text

    unsupported_opportunity = next(
        item
        for item in opportunities_after_experiment
        if item["opportunity_type"] not in {"benchmark_gap", "rule_gap"}
    )
    unsupported_response = client.post(
        f"/api/v1/research-intel/opportunities/{unsupported_opportunity['opportunity_id']}/experiment",
        json={"write_artifacts": False},
        headers=_auth_headers("research-admin"),
    )
    assert unsupported_response.status_code == 400


def test_research_intel_case_brief_maps_case_to_topics_and_documents() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    ingest_response = client.post(
        "/api/v1/research-intel/runs/ingest",
        json={"mode": "fixture", "write_artifacts": False},
        headers=_auth_headers("research-admin"),
    )
    assert ingest_response.status_code == 200

    digest_response = client.post(
        "/api/v1/research-intel/runs/digest",
        json={"publish": True, "write_artifacts": False},
        headers=_auth_headers("research-admin"),
    )
    assert digest_response.status_code == 200

    _triage_case(client, case_id="C-RI-1", report_id="R-RI-1")

    response = client.get(
        "/api/v1/research-intel/cases/C-RI-1/brief",
        headers=_auth_headers("reviewer-a", "reviewer"),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["matched_topics"]
    assert payload["supporting_documents"]
    assert "case score automatically" in payload["summary"]


def test_research_intel_digest_history_tracks_recurring_questions_across_runs() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    ingest_response = client.post(
        "/api/v1/research-intel/runs/ingest",
        json={"mode": "fixture", "write_artifacts": False},
        headers=_auth_headers("research-admin"),
    )
    assert ingest_response.status_code == 200

    first_digest = client.post(
        "/api/v1/research-intel/runs/digest",
        json={"publish": True, "write_artifacts": False},
        headers=_auth_headers("research-admin"),
    )
    assert first_digest.status_code == 200

    second_digest = client.post(
        "/api/v1/research-intel/runs/digest",
        json={"publish": True, "write_artifacts": False},
        headers=_auth_headers("research-admin"),
    )
    assert second_digest.status_code == 200

    digests = client.get("/api/v1/research-intel/digests").json()
    assert len(digests) >= 2
    latest = digests[0]
    previous = digests[1]
    assert latest["trend"]["previous_digest_id"] == previous["digest_id"]
    assert latest["trend"]["confidence_trend"] in {"holding", "raising", "lowering"}

    detail = client.get(f"/api/v1/research-intel/digests/{latest['digest_id']}").json()
    assert detail["history"]["recent_digests"]
    assert len(detail["history"]["recent_digests"]) >= 2
    assert detail["history"]["recurring_open_questions"]
    assert "## Across runs" in detail["summary_markdown"]


def test_research_intel_documents_support_filters_and_viewer_cannot_trigger_runs() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    response = client.post(
        "/api/v1/research-intel/runs/ingest",
        json={"mode": "fixture", "write_artifacts": False},
        headers=_auth_headers("viewer-a", "viewer"),
    )
    assert response.status_code == 403

    response = client.post(
        "/api/v1/research-intel/runs/ingest",
        json={"mode": "fixture", "write_artifacts": False},
        headers=_auth_headers("research-admin"),
    )
    assert response.status_code == 200

    response = client.get("/api/v1/research-intel/documents", params={"source_kind": "preprint"})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["source_kind"] == "preprint"

    response = client.get("/api/v1/research-intel/documents", params={"topic": "oss_opportunities"})
    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert all("oss_opportunities" in item["topic_ids"] for item in payload)


def test_research_intel_schedule_and_due_only_ingest_are_operator_friendly() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    response = client.get("/api/v1/research-intel/schedule")
    assert response.status_code == 200
    schedule = response.json()
    assert schedule["total_sources"] >= 9
    assert schedule["due_count"] >= 1
    assert schedule["live_ready_count"] >= 5
    assert any(item["schedule_state"] == "due" for item in schedule["sources"])

    response = client.post(
        "/api/v1/research-intel/runs/ingest",
        json={"mode": "fixture", "write_artifacts": False, "only_due": True},
        headers=_auth_headers("research-admin"),
    )
    assert response.status_code == 200
    payload = response.json()["run"]
    assert payload["metadata"]["only_due"] is True
    assert payload["processed"] >= 9
    assert payload["metadata"]["skipped_source_ids"] == []

    follow_up = client.post(
        "/api/v1/research-intel/runs/ingest",
        json={"mode": "fixture", "write_artifacts": False, "only_due": True},
        headers=_auth_headers("research-admin"),
    )
    assert follow_up.status_code == 200
    follow_up_payload = follow_up.json()["run"]
    assert follow_up_payload["processed"] == 0
    assert len(follow_up_payload["metadata"]["skipped_source_ids"]) >= schedule["total_sources"]

    refreshed_schedule = client.get("/api/v1/research-intel/schedule").json()
    assert refreshed_schedule["due_count"] == 0
    assert refreshed_schedule["scheduled_count"] >= 1


def test_research_intel_seeded_mode_is_still_available_for_bootstrap_runs() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    response = client.post(
        "/api/v1/research-intel/runs/ingest",
        json={"mode": "seeded", "write_artifacts": False, "max_documents_per_source": 1},
        headers=_auth_headers("research-admin"),
    )
    assert response.status_code == 200
    payload = response.json()["run"]
    assert payload["metadata"]["requested_mode"] == "seeded"
    assert payload["processed"] == 6


def test_research_intel_legacy_council_payloads_remain_readable() -> None:
    payload = ResearchCouncilPayload.model_validate(
        {
            "stage_1": [
                {
                    "persona": "literature_scout",
                    "focus": "Track literature",
                    "summary": "Legacy digest payload",
                    "citations": ["PMID:1234"],
                    "proposed_opportunity_types": ["benchmark_gap"],
                }
            ],
            "stage_2": [
                {
                    "persona": "literature_scout",
                    "ranked_topics": ["Early Detection"],
                    "ranked_opportunity_types": ["benchmark_gap"],
                    "critique": "Legacy critique",
                }
            ],
            "stage_3": {
                "chairman_summary": "Legacy chairman summary",
                "consensus_points": ["Keep the council payload backward compatible."],
                "disagreement_points": [],
                "recommended_actions": ["Regenerate the digest when richer council fields are available."],
            },
        }
    )

    assert payload.stage_1[0].confidence_label == "medium"
    assert payload.stage_2[0].confidence_adjustment == "hold"
    assert payload.stage_3.overall_confidence == "medium"


def test_research_intel_legacy_opportunity_payloads_remain_readable() -> None:
    payload = ResearchOpportunityActionPayload.model_validate(
        {
            "human_gate": True,
            "digest_id": "rdigest-legacy",
            "acceptance_gates": ["Keep the promotion human-gated."],
            "suggested_target": "docs_draft",
            "promoted_by": "legacy-user",
        }
    )

    assert payload.objective == ""
    assert payload.artifact_spec.artifact_kind == "community_project_spec"
    assert payload.acceptance_gates == ["Keep the promotion human-gated."]
