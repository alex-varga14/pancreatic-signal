from __future__ import annotations

import base64
import json
from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status

from app.core.config import settings
from app.schemas.auth import ActorCapabilities, ActorRole, AuthenticatedActor

_VALID_ROLES: set[str] = {"viewer", "reviewer", "navigator", "analyst", "admin"}
_ROLE_RANK = {
    "viewer": 0,
    "reviewer": 1,
    "navigator": 2,
    "analyst": 3,
    "admin": 4,
}
_GENERIC_PROXY_FIELDS = {
    "user_id_field": "sub",
    "display_name_field": "name",
    "role_field": "role",
    "sites_field": "sites",
    "groups_field": "groups",
}
_PROXY_PRESETS = {
    "generic": {
        "provider": "generic-proxy",
        **_GENERIC_PROXY_FIELDS,
    },
    "authentik": {
        "provider": "authentik",
        "user_id_field": "preferred_username",
        "display_name_field": "name",
        "role_field": "role",
        "sites_field": "sites",
        "groups_field": "groups",
    },
    "keycloak": {
        "provider": "keycloak",
        "user_id_field": "preferred_username",
        "display_name_field": "name",
        "role_field": "realm_access.roles",
        "sites_field": "sites",
        "groups_field": "groups",
    },
    "oauth2-proxy": {
        "provider": "oauth2-proxy",
        "user_id_field": "email",
        "display_name_field": "name",
        "role_field": "role",
        "sites_field": "sites",
        "groups_field": "groups",
    },
}


def get_current_actor(request: Request) -> AuthenticatedActor:
    proxy_identity = request.headers.get(settings.auth_proxy_identity_header_name)
    if proxy_identity:
        actor = _build_proxy_actor(proxy_identity)
        request.state.actor = actor
        return actor

    header_user_id = request.headers.get(settings.auth_user_id_header_name)
    header_role = request.headers.get(settings.auth_user_role_header_name)
    header_name = request.headers.get(settings.auth_user_name_header_name)
    header_sites = request.headers.get(settings.auth_user_sites_header_name)

    header_override = any([header_user_id, header_role, header_name, header_sites])
    if header_override:
        user_id = header_user_id or _mock_actor_user_id()
        role = _coerce_role(
            header_role or settings.mock_auth_default_role,
            source="header",
        )
        display_name = header_name or user_id
        actor = _build_actor(
            user_id=user_id,
            display_name=display_name,
            role=role,
            auth_mode="header",
            provider="header",
            site_scope=_parse_site_scope(header_sites),
        )
        request.state.actor = actor
        return actor

    if settings.mock_auth_enabled:
        actor = _build_actor(
            user_id=_mock_actor_user_id(),
            display_name=settings.mock_auth_default_display_name or _mock_actor_user_id(),
            role=_coerce_role(settings.mock_auth_default_role, source="mock"),
            auth_mode="mock",
            provider="mock",
            site_scope=_parse_site_scope(settings.mock_auth_default_sites),
        )
        request.state.actor = actor
        return actor

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=(
            "Authentication required. Supply a trusted identity header or "
            f"{settings.auth_user_id_header_name} and {settings.auth_user_role_header_name}."
        ),
    )


def require_roles(*allowed_roles: ActorRole) -> Callable[[AuthenticatedActor], AuthenticatedActor]:
    allowed = {role.lower() for role in allowed_roles}

    def dependency(actor: AuthenticatedActor = Depends(get_current_actor)) -> AuthenticatedActor:
        if actor.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Role '{actor.role}' cannot access this route. "
                    f"Allowed roles: {', '.join(sorted(allowed))}."
                ),
            )
        return actor

    return dependency


def validate_requested_site_access(actor: AuthenticatedActor, site: str | None) -> str | None:
    if not site:
        return site
    if actor_can_access_site(actor, site):
        return site
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Actor '{actor.user_id}' cannot access site '{site}'.",
    )


def require_case_site_access(
    actor: AuthenticatedActor,
    case_site: str | None,
    *,
    not_found_on_denied: bool = True,
) -> None:
    if actor_can_access_site(actor, case_site):
        return

    status_code = status.HTTP_404_NOT_FOUND if not_found_on_denied else status.HTTP_403_FORBIDDEN
    detail = "Case not found" if not_found_on_denied else f"Actor '{actor.user_id}' cannot access this site."
    raise HTTPException(status_code=status_code, detail=detail)


def actor_can_access_site(actor: AuthenticatedActor, site: str | None) -> bool:
    normalized_scope = _normalized_site_scope(actor.site_scope)
    if normalized_scope is None:
        return True
    if not site:
        return False
    return site.strip().lower() in normalized_scope


def _build_proxy_actor(raw_identity: str) -> AuthenticatedActor:
    payload = _parse_proxy_identity(raw_identity)
    proxy_settings = _resolved_proxy_settings()

    user_id = _read_required_string_claim(payload, proxy_settings["user_id_field"])
    display_name = _read_optional_string_claim(payload, proxy_settings["display_name_field"]) or user_id

    role = (
        _read_role_claim(payload, proxy_settings["role_field"])
        or _role_from_groups(_read_string_list_claim(payload, proxy_settings["groups_field"]))
        or "viewer"
    )

    return _build_actor(
        user_id=user_id,
        display_name=display_name,
        role=role,
        auth_mode="proxy",
        provider=proxy_settings["provider"],
        site_scope=_read_site_scope_claim(payload, proxy_settings["sites_field"]),
    )


def _build_actor(
    *,
    user_id: str,
    display_name: str,
    role: ActorRole,
    auth_mode: str,
    provider: str,
    site_scope: list[str] | None,
) -> AuthenticatedActor:
    return AuthenticatedActor(
        user_id=user_id,
        display_name=display_name,
        role=role,
        auth_mode=auth_mode,
        provider=provider,
        site_scope=site_scope,
        capabilities=_build_capabilities(role),
    )


def _build_capabilities(role: ActorRole) -> ActorCapabilities:
    can_review_cases = role in {"reviewer", "navigator", "admin"}
    can_import_reports = role in {"analyst", "navigator", "admin"}
    can_export_data = role in {"analyst", "navigator", "admin"}
    can_manage_research_intel = role in {"analyst", "navigator", "admin"}

    return ActorCapabilities(
        can_view_cases=True,
        can_review_cases=can_review_cases,
        can_submit_feedback=can_review_cases,
        can_import_reports=can_import_reports,
        can_export_data=can_export_data,
        can_view_feedback_summary=True,
        can_manage_research_intel=can_manage_research_intel,
        can_promote_research_intel=can_manage_research_intel,
    )


def _mock_actor_user_id() -> str:
    return settings.mock_auth_default_user_id or "demo-reviewer"


def _coerce_role(role: str, *, source: str) -> ActorRole:
    normalized = _normalize_role_alias(role)
    if normalized not in _VALID_ROLES:
        if source == "mock":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Mock auth role '{role}' is misconfigured.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{role}'. Expected one of: {', '.join(sorted(_VALID_ROLES))}.",
        )
    return normalized  # type: ignore[return-value]


def _normalize_role_alias(role: str) -> str:
    normalized = role.strip().lower()
    alias_map = _parse_pair_mapping(settings.auth_role_alias_map)
    return alias_map.get(normalized, normalized)


def _read_role_claim(payload: dict[str, object], field: str) -> ActorRole | None:
    raw_value = _read_claim_value(payload, field)
    if raw_value is None:
        return None
    if isinstance(raw_value, str):
        return _coerce_role(raw_value, source="proxy")
    if isinstance(raw_value, list):
        matched_roles = _roles_from_values(raw_value)
        if matched_roles:
            return max(matched_roles, key=lambda role: _ROLE_RANK[role])
        return None
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Trusted identity field '{field}' must be a string or list of strings.",
    )


def _roles_from_values(values: list[object]) -> list[ActorRole]:
    matched: list[ActorRole] = []
    for value in values:
        if not isinstance(value, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Trusted identity role collections must contain only strings.",
            )
        normalized = _normalize_role_alias(value)
        if normalized in _VALID_ROLES:
            matched.append(normalized)  # type: ignore[arg-type]
    return matched


def _role_from_groups(groups: list[str]) -> ActorRole | None:
    group_role_map = _parse_pair_mapping(settings.auth_proxy_group_role_map)
    matched_roles = [
        _coerce_role(mapped_role, source="proxy")
        for group in groups
        if (mapped_role := group_role_map.get(group.strip().lower()))
    ]
    if not matched_roles:
        return None
    return max(matched_roles, key=lambda role: _ROLE_RANK[role])


def _resolved_proxy_settings() -> dict[str, str]:
    preset_key = settings.auth_proxy_provider_preset.strip().lower().replace("_", "-") or "generic"
    preset = _PROXY_PRESETS.get(preset_key)
    if preset is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unknown auth proxy provider preset '{settings.auth_proxy_provider_preset}'.",
        )

    return {
        "provider": preset["provider"],
        "user_id_field": _resolve_proxy_field(settings.auth_proxy_user_id_field, "user_id_field", preset),
        "display_name_field": _resolve_proxy_field(
            settings.auth_proxy_display_name_field,
            "display_name_field",
            preset,
        ),
        "role_field": _resolve_proxy_field(settings.auth_proxy_role_field, "role_field", preset),
        "sites_field": _resolve_proxy_field(settings.auth_proxy_sites_field, "sites_field", preset),
        "groups_field": _resolve_proxy_field(settings.auth_proxy_groups_field, "groups_field", preset),
    }


def _resolve_proxy_field(configured_value: str, key: str, preset: dict[str, str]) -> str:
    generic_default = _GENERIC_PROXY_FIELDS[key]
    if configured_value == generic_default:
        return preset[key]
    return configured_value


def _parse_proxy_identity(raw_identity: str) -> dict[str, object]:
    for candidate in (raw_identity, _decode_base64url_json(raw_identity)):
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
        break

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            f"Invalid trusted identity header '{settings.auth_proxy_identity_header_name}'. "
            "Expected JSON object or base64url-encoded JSON object."
        ),
    )


def _decode_base64url_json(raw_identity: str) -> str | None:
    try:
        padded = raw_identity + "=" * (-len(raw_identity) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode("utf-8"))
        return decoded.decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None


def _read_required_string_claim(payload: dict[str, object], field: str) -> str:
    value = _read_optional_string_claim(payload, field)
    if value:
        return value
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Trusted identity header is missing required field '{field}'.",
    )


def _read_optional_string_claim(payload: dict[str, object], field: str) -> str | None:
    raw_value = _read_claim_value(payload, field)
    if raw_value is None:
        return None
    if isinstance(raw_value, str):
        value = raw_value.strip()
        return value or None
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Trusted identity field '{field}' must be a string.",
    )


def _read_site_scope_claim(payload: dict[str, object], field: str) -> list[str] | None:
    raw_value = _read_claim_value(payload, field)
    if raw_value is None:
        return None
    if isinstance(raw_value, str):
        return _parse_site_scope(raw_value)
    if isinstance(raw_value, list):
        parsed = [
            item.strip()
            for item in raw_value
            if isinstance(item, str) and item.strip()
        ]
        return list(dict.fromkeys(parsed)) or None
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Trusted identity field '{field}' must be a string or list of strings.",
    )


def _read_string_list_claim(payload: dict[str, object], field: str) -> list[str]:
    raw_value = _read_claim_value(payload, field)
    if raw_value is None:
        return []
    if isinstance(raw_value, str):
        return [item for item in (part.strip() for part in raw_value.split(",")) if item]
    if isinstance(raw_value, list):
        parsed = []
        for item in raw_value:
            if not isinstance(item, str):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Trusted identity field '{field}' must contain only strings.",
                )
            if item.strip():
                parsed.append(item.strip())
        return parsed
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Trusted identity field '{field}' must be a string or list of strings.",
    )


def _read_claim_value(payload: dict[str, object], field: str) -> object | None:
    current: object | None = payload
    for segment in field.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(segment)
        if current is None:
            return None
    return current


def _parse_pair_mapping(raw_value: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for pair in raw_value.split(","):
        item = pair.strip()
        if not item or ":" not in item:
            continue
        left, right = item.split(":", 1)
        left_n = left.strip().lower()
        right_n = right.strip().lower()
        if left_n and right_n:
            mapping[left_n] = right_n
    return mapping


def _parse_site_scope(raw_value: str | None) -> list[str] | None:
    if raw_value is None:
        return None

    parsed = [
        site
        for site in dict.fromkeys(item.strip() for item in raw_value.split(","))
        if site
    ]
    return parsed or None


def _normalized_site_scope(site_scope: list[str] | None) -> set[str] | None:
    if site_scope is None:
        return None
    return {site.strip().lower() for site in site_scope if site.strip()}
