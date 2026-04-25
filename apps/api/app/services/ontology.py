from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.core.paths import resolve_data_path
from app.schemas.ontology import OntologyConfig

ONTOLOGY_PATH = resolve_data_path("ontologies", "pancreatic_signal_rules.json")


@lru_cache(maxsize=1)
def load_ontology() -> dict:
    with ONTOLOGY_PATH.open() as f:
        return json.load(f)


def validate_ontology_payload(payload: dict) -> OntologyConfig:
    """Validate a candidate ontology dict against ``OntologyConfig``.

    Used by the autoresearch experiment driver to reject ill-formed proposals
    before they reach the triage engine. Raises ``ValidationError`` on failure.
    """
    return OntologyConfig.model_validate(payload)


def load_ontology_from_path(path: Path | str) -> dict:
    """Load and validate an ontology JSON from an arbitrary path.

    The runtime triage engine still uses :func:`load_ontology` against the
    bundled file. This helper is intended for offline scripts (autoresearch
    drivers, CI lints) that need to validate proposals without touching the
    cached production ontology.
    """
    candidate_path = Path(path)
    with candidate_path.open() as f:
        payload = json.load(f)
    validate_ontology_payload(payload)
    return payload
