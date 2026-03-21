import json
from functools import lru_cache

from app.core.paths import resolve_data_path

ONTOLOGY_PATH = resolve_data_path("ontologies", "pancreatic_signal_rules.json")


@lru_cache(maxsize=1)
def load_ontology() -> dict:
    with ONTOLOGY_PATH.open() as f:
        return json.load(f)
