from __future__ import annotations

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import Base

connect_args: dict[str, object] = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(settings.database_url, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_report_metadata_columns()


def _ensure_report_metadata_columns() -> None:
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("reports")}
    statements: list[str] = []

    if "patient_identifier" not in columns:
        statements.append("ALTER TABLE reports ADD COLUMN patient_identifier VARCHAR(255)")
    if "encounter_identifier" not in columns:
        statements.append("ALTER TABLE reports ADD COLUMN encounter_identifier VARCHAR(255)")
    if "accession_number" not in columns:
        statements.append("ALTER TABLE reports ADD COLUMN accession_number VARCHAR(255)")
    if "ordering_provider" not in columns:
        statements.append("ALTER TABLE reports ADD COLUMN ordering_provider VARCHAR(255)")
    if "source_system" not in columns:
        statements.append("ALTER TABLE reports ADD COLUMN source_system VARCHAR(512)")
    if "source_format" not in columns:
        statements.append("ALTER TABLE reports ADD COLUMN source_format VARCHAR(64)")
    if "import_source_id" not in columns:
        statements.append("ALTER TABLE reports ADD COLUMN import_source_id VARCHAR(512)")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
