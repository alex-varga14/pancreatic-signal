from typing import Literal

from pydantic import BaseModel

ActorRole = Literal["viewer", "reviewer", "navigator", "analyst", "admin"]
AuthMode = Literal["mock", "header", "proxy"]


class ActorCapabilities(BaseModel):
    can_view_cases: bool
    can_review_cases: bool
    can_submit_feedback: bool
    can_import_reports: bool
    can_export_data: bool
    can_view_feedback_summary: bool
    can_manage_research_intel: bool
    can_promote_research_intel: bool


class AuthenticatedActor(BaseModel):
    user_id: str
    display_name: str
    role: ActorRole
    auth_mode: AuthMode
    provider: str
    site_scope: list[str] | None = None
    capabilities: ActorCapabilities
