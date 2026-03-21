import base64
import json
from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.store.memory_store import CASE_STORE


def _auth_headers(user_id: str, role: str, *, sites: str | None = None) -> dict[str, str]:
    headers = {"X-User-ID": user_id, "X-User-Role": role}
    if sites:
        headers["X-User-Sites"] = sites
    return headers


def _trusted_identity_header(payload: dict[str, object], *, encode_base64: bool = False) -> dict[str, str]:
    raw = json.dumps(payload)
    if encode_base64:
        raw = base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8").rstrip("=")
    return {settings.auth_proxy_identity_header_name: raw}


@contextmanager
def _override_settings(**overrides: object):
    original_values = {key: getattr(settings, key) for key in overrides}
    try:
        for key, value in overrides.items():
            setattr(settings, key, value)
        yield
    finally:
        for key, value in original_values.items():
            setattr(settings, key, value)


def _triage_case(client: TestClient, *, case_id: str, report_id: str) -> None:
    response = client.post(
        "/api/v1/triage/report",
        json={
            "report_id": report_id,
            "case_id": case_id,
            "report_datetime": "2026-03-19T10:00:00Z",
            "modality": "CT",
            "site": "Demo Hospital",
            "report_text": "Impression: Suspicious for pancreatic neoplasm. Recommend biopsy.",
        },
    )
    assert response.status_code == 200


def test_auth_me_returns_mock_actor_by_default() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == "demo-reviewer"
    assert payload["display_name"] == "Demo Reviewer"
    assert payload["role"] == "admin"
    assert payload["auth_mode"] == "mock"
    assert payload["provider"] == "mock"
    assert payload["capabilities"]["can_review_cases"] is True
    assert payload["capabilities"]["can_export_data"] is True


def test_auth_me_supports_header_override() -> None:
    client = TestClient(app)
    response = client.get(
        "/api/v1/auth/me",
        headers={
            **_auth_headers("navigator-a", "navigator", sites="North Clinic, Demo Hospital"),
            "X-User-Name": "Navigator A",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == "navigator-a"
    assert payload["display_name"] == "Navigator A"
    assert payload["role"] == "navigator"
    assert payload["auth_mode"] == "header"
    assert payload["provider"] == "header"
    assert payload["site_scope"] == ["North Clinic", "Demo Hospital"]
    assert payload["capabilities"]["can_import_reports"] is True


def test_auth_me_supports_trusted_identity_header() -> None:
    client = TestClient(app)
    response = client.get(
        "/api/v1/auth/me",
        headers=_trusted_identity_header(
            {
                "sub": "proxy-user-1",
                "name": "Proxy User",
                "role": "reviewer",
                "sites": ["Demo Hospital", "North Clinic"],
            }
        ),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == "proxy-user-1"
    assert payload["display_name"] == "Proxy User"
    assert payload["role"] == "reviewer"
    assert payload["auth_mode"] == "proxy"
    assert payload["provider"] == "generic-proxy"
    assert payload["site_scope"] == ["Demo Hospital", "North Clinic"]
    assert payload["capabilities"]["can_submit_feedback"] is True


def test_auth_me_supports_base64_trusted_identity_header() -> None:
    client = TestClient(app)
    response = client.get(
        "/api/v1/auth/me",
        headers=_trusted_identity_header(
            {
                "sub": "proxy-user-2",
                "name": "Proxy Encoded",
                "role": "navigator",
                "sites": "North Clinic, Demo Hospital",
            },
            encode_base64=True,
        ),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == "proxy-user-2"
    assert payload["role"] == "navigator"
    assert payload["auth_mode"] == "proxy"
    assert payload["provider"] == "generic-proxy"
    assert payload["site_scope"] == ["North Clinic", "Demo Hospital"]


def test_trusted_identity_can_map_groups_to_role() -> None:
    client = TestClient(app)
    with _override_settings(auth_proxy_group_role_map="pdac-reviewers:reviewer,pdac-navigators:navigator"):
        response = client.get(
            "/api/v1/auth/me",
            headers=_trusted_identity_header(
                {
                    "sub": "group-user",
                    "name": "Group User",
                    "groups": ["pdac-reviewers", "pdac-navigators"],
                }
            ),
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["role"] == "navigator"
    assert payload["auth_mode"] == "proxy"
    assert payload["capabilities"]["can_export_data"] is True


def test_trusted_identity_provider_preset_supports_keycloak_style_claims() -> None:
    client = TestClient(app)
    with _override_settings(
        auth_proxy_provider_preset="keycloak",
        auth_role_alias_map="pdac-reviewer:reviewer",
    ):
        response = client.get(
            "/api/v1/auth/me",
            headers=_trusted_identity_header(
                {
                    "preferred_username": "kc-user",
                    "name": "Keycloak User",
                    "realm_access": {"roles": ["offline_access", "pdac-reviewer"]},
                    "sites": ["North Clinic"],
                }
            ),
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == "kc-user"
    assert payload["role"] == "reviewer"
    assert payload["provider"] == "keycloak"
    assert payload["site_scope"] == ["North Clinic"]


def test_trusted_identity_precedence_over_field_headers() -> None:
    client = TestClient(app)
    response = client.get(
        "/api/v1/auth/me",
        headers={
            **_trusted_identity_header(
                {"sub": "proxy-precedence", "name": "Proxy Preferred", "role": "reviewer"}
            ),
            **_auth_headers("header-user", "admin"),
            "X-User-Name": "Header User",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == "proxy-precedence"
    assert payload["display_name"] == "Proxy Preferred"
    assert payload["role"] == "reviewer"
    assert payload["auth_mode"] == "proxy"
    assert payload["provider"] == "generic-proxy"


def test_trusted_identity_invalid_payload_returns_400() -> None:
    client = TestClient(app)
    response = client.get(
        "/api/v1/auth/me",
        headers={settings.auth_proxy_identity_header_name: "not-json-or-base64"},
    )
    assert response.status_code == 400


def test_viewer_receives_read_only_capabilities() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/auth/me", headers=_auth_headers("viewer-1", "viewer"))
    assert response.status_code == 200
    payload = response.json()
    assert payload["capabilities"]["can_review_cases"] is False
    assert payload["capabilities"]["can_submit_feedback"] is False
    assert payload["capabilities"]["can_import_reports"] is False
    assert payload["capabilities"]["can_export_data"] is False


def test_review_route_uses_authenticated_actor() -> None:
    CASE_STORE.reset()
    client = TestClient(app)
    _triage_case(client, case_id="C-AUTH-1", report_id="R-AUTH-1")

    response = client.post(
        "/api/v1/cases/C-AUTH-1/review",
        json={"action": "assign", "reviewer": "someone-else", "assigned_to": "navigator-b"},
        headers=_auth_headers("alex", "reviewer"),
    )
    assert response.status_code == 200

    case_detail = client.get("/api/v1/cases/C-AUTH-1").json()
    assert case_detail["review_actions"][0]["reviewer"] == "alex"


def test_viewer_role_cannot_review_or_export_or_import() -> None:
    CASE_STORE.reset()
    client = TestClient(app)
    _triage_case(client, case_id="C-AUTH-2", report_id="R-AUTH-2")
    viewer_headers = {"X-User-ID": "viewer-1", "X-User-Role": "viewer"}

    review_response = client.post(
        "/api/v1/cases/C-AUTH-2/review",
        json={"action": "in_review"},
        headers=viewer_headers,
    )
    assert review_response.status_code == 403

    export_response = client.get("/api/v1/exports/cases.csv", headers=viewer_headers)
    assert export_response.status_code == 403

    import_response = client.post(
        "/api/v1/imports/reports",
        files={
            "file": (
                "reports.jsonl",
                '{"report_id":"R-IMPORT-AUTH","case_id":"C-IMPORT-AUTH","report_datetime":"2026-03-19T10:00:00Z","modality":"CT","site":"Demo Hospital","report_text":"Impression: No acute abnormality."}',
                "application/x-ndjson",
            )
        },
        headers=viewer_headers,
    )
    assert import_response.status_code == 403


def test_site_scoped_actor_only_sees_accessible_cases() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    response = client.post(
        "/api/v1/triage/report",
        json={
            "report_id": "R-SCOPE-1",
            "case_id": "C-SCOPE-1",
            "report_datetime": "2026-03-19T10:00:00Z",
            "modality": "CT",
            "site": "Demo Hospital",
            "report_text": "Impression: Suspicious for pancreatic neoplasm. Recommend biopsy.",
        },
    )
    assert response.status_code == 200
    response = client.post(
        "/api/v1/triage/report",
        json={
            "report_id": "R-SCOPE-2",
            "case_id": "C-SCOPE-2",
            "report_datetime": "2026-03-19T10:00:00Z",
            "modality": "CT",
            "site": "North Clinic",
            "report_text": "Impression: Recommend EUS for focal pancreatic duct change.",
        },
    )
    assert response.status_code == 200

    north_headers = _auth_headers("north-reviewer", "reviewer", sites="North Clinic")

    case_list_response = client.get("/api/v1/cases", headers=north_headers)
    assert case_list_response.status_code == 200
    assert [item["case_id"] for item in case_list_response.json()] == ["C-SCOPE-2"]

    blocked_detail = client.get("/api/v1/cases/C-SCOPE-1", headers=north_headers)
    assert blocked_detail.status_code == 404

    blocked_review = client.post(
        "/api/v1/cases/C-SCOPE-1/review",
        json={"action": "in_review"},
        headers=north_headers,
    )
    assert blocked_review.status_code == 404

    visible_detail = client.get("/api/v1/cases/C-SCOPE-2", headers=north_headers)
    assert visible_detail.status_code == 200
    assert visible_detail.json()["site"] == "North Clinic"


def test_site_scoped_actor_cannot_request_out_of_scope_site_filter() -> None:
    client = TestClient(app)
    response = client.get(
        "/api/v1/cases",
        params={"site": "Demo Hospital"},
        headers=_auth_headers("north-reviewer", "reviewer", sites="North Clinic"),
    )
    assert response.status_code == 403


def test_site_scoped_actor_cannot_import_other_site_reports() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/imports/reports",
        files={
            "file": (
                "reports.jsonl",
                '{"report_id":"R-SCOPE-IMPORT","case_id":"C-SCOPE-IMPORT","report_datetime":"2026-03-19T10:00:00Z","modality":"CT","site":"Demo Hospital","report_text":"Impression: No acute abnormality."}',
                "application/x-ndjson",
            )
        },
        headers=_auth_headers("north-analyst", "analyst", sites="North Clinic"),
    )
    assert response.status_code == 403
    assert "Demo Hospital" in response.json()["detail"]
