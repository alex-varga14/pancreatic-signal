from __future__ import annotations

import copy

import pytest
from pydantic import ValidationError

from app.schemas.ontology import OntologyConfig
from app.services.ontology import load_ontology, validate_ontology_payload


def test_bundled_ontology_validates_against_schema() -> None:
    payload = copy.deepcopy(load_ontology())
    config = validate_ontology_payload(payload)
    assert isinstance(config, OntologyConfig)
    assert config.scoring.method in {"additive", "max", "weighted_sum"}
    assert any(family.code == "PDAC_EXPLICIT_SUSPICION" for family in config.families)


def test_ontology_rejects_unknown_scoring_method() -> None:
    payload = copy.deepcopy(load_ontology())
    payload["scoring"] = {**payload.get("scoring", {}), "method": "totally-bogus"}
    with pytest.raises(ValidationError):
        validate_ontology_payload(payload)


def test_ontology_rejects_duplicate_family_codes() -> None:
    payload = copy.deepcopy(load_ontology())
    payload["families"] = [*payload["families"], copy.deepcopy(payload["families"][0])]
    with pytest.raises(ValidationError):
        validate_ontology_payload(payload)
