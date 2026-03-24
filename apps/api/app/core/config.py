from urllib.parse import urlsplit

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "pancreatic-signal-api"
    app_version: str = "0.1.0"
    app_env: str = "development"
    database_url: str = "sqlite:///./pancreatic_signal.db"
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"
    request_id_header_name: str = "X-Request-ID"
    mock_auth_enabled: bool = True
    mock_auth_default_user_id: str = "demo-reviewer"
    mock_auth_default_display_name: str = "Demo Reviewer"
    mock_auth_default_role: str = "admin"
    mock_auth_default_sites: str = ""
    auth_role_alias_map: str = ""
    auth_proxy_provider_preset: str = "generic"
    auth_proxy_identity_header_name: str = "X-Trusted-Identity"
    auth_proxy_user_id_field: str = "sub"
    auth_proxy_display_name_field: str = "name"
    auth_proxy_role_field: str = "role"
    auth_proxy_sites_field: str = "sites"
    auth_proxy_groups_field: str = "groups"
    auth_proxy_group_role_map: str = ""
    auth_user_id_header_name: str = "X-User-ID"
    auth_user_name_header_name: str = "X-User-Name"
    auth_user_role_header_name: str = "X-User-Role"
    auth_user_sites_header_name: str = "X-User-Sites"
    research_id_salt: str = "pancreatic-signal-research"
    fhir_reference_identifier_source_order: str = "resolved_identifier,reference_identifier,resolved_id,reference_tail"
    fhir_source_system_source_order: str = "meta_source,performer,results_interpreter,encounter_service_provider"
    fhir_accession_source_order: str = (
        "report_identifier_typed,based_on_identifier_typed,based_on_reference_identifier_typed,report_identifier,based_on_identifier,based_on_reference_identifier"
    )
    hl7_patient_identifier_field_order: str = "PID-3,PID-2"
    hl7_source_system_field_order: str = "MSH-3,MSH-4"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def fhir_reference_identifier_source_order_list(self) -> list[str]:
        return _split_csv(self.fhir_reference_identifier_source_order)

    @property
    def fhir_source_system_source_order_list(self) -> list[str]:
        return _split_csv(self.fhir_source_system_source_order)

    @property
    def fhir_accession_source_order_list(self) -> list[str]:
        return _split_csv(self.fhir_accession_source_order)

    @property
    def hl7_patient_identifier_field_order_list(self) -> list[str]:
        return _split_csv(self.hl7_patient_identifier_field_order)

    @property
    def hl7_source_system_field_order_list(self) -> list[str]:
        return _split_csv(self.hl7_source_system_field_order)

    @property
    def database_backend(self) -> str:
        scheme = urlsplit(self.database_url).scheme or self.database_url.split("://", 1)[0]
        return scheme.split("+", 1)[0]


settings = Settings()


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]
