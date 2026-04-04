from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from app.core.paths import resolve_data_path

DISCOVERY_FIXTURE_ROOT = resolve_data_path("research", "discovery_fixtures")
DEFAULT_TIMEOUT_SECONDS = 20
USER_AGENT = "PancreaticSignalResearchIntel/0.1"


def collect_research_documents_for_source(
    source_descriptor: dict[str, Any],
    *,
    mode: str,
    max_documents_per_source: int | None = None,
) -> dict[str, Any]:
    polling_config = source_descriptor.get("polling_config") or {}
    requested_mode = str(mode or "auto").strip().lower() or "auto"
    default_mode = str(polling_config.get("default_mode") or "fixture").strip().lower() or "fixture"
    connector_id = str(polling_config.get("connector_id") or "fixture_catalog").strip() or "fixture_catalog"
    source_id = str(source_descriptor.get("source_id") or "").strip()
    page_size = _coerce_positive_int(max_documents_per_source) or _coerce_positive_int(
        polling_config.get("max_documents_per_run")
    ) or 5
    fetch_multiplier = _coerce_positive_int(polling_config.get("fetch_multiplier")) or (
        3 if _has_document_filters(polling_config) else 1
    )
    fetch_page_size = max(page_size, min(100, page_size * fetch_multiplier))
    effective_mode = default_mode if requested_mode == "auto" else requested_mode

    if effective_mode == "fixture":
        fixture_path = _resolve_fixture_path(polling_config.get("fixture_path"), source_id=source_id)
        batch = _load_fixture_documents(
            source_id=source_id,
            connector_id=connector_id,
            fixture_path=fixture_path,
            page_size=fetch_page_size,
        )
        return _apply_batch_filters(batch, polling_config=polling_config, page_size=page_size)

    if effective_mode != "live":
        raise ValueError(f"Unsupported discovery ingest mode '{effective_mode}' for source '{source_id}'.")

    if connector_id == "europe_pmc_search":
        batch = _fetch_europe_pmc_documents(
            source_id=source_id,
            connector_id=connector_id,
            query=str(polling_config.get("query") or ""),
            page_size=fetch_page_size,
        )
        return _apply_batch_filters(batch, polling_config=polling_config, page_size=page_size)
    if connector_id == "clinicaltrials_v2":
        batch = _fetch_clinical_trials_documents(
            source_id=source_id,
            connector_id=connector_id,
            query=str(polling_config.get("query") or ""),
            page_size=fetch_page_size,
        )
        return _apply_batch_filters(batch, polling_config=polling_config, page_size=page_size)
    if connector_id == "rss_feed":
        batch = _fetch_feed_documents(
            source_id=source_id,
            connector_id=connector_id,
            feed_url=str(polling_config.get("feed_url") or ""),
            page_size=fetch_page_size,
            document_type=str(polling_config.get("document_type") or "news"),
        )
        return _apply_batch_filters(batch, polling_config=polling_config, page_size=page_size)
    if connector_id == "github_repository_search":
        batch = _fetch_github_repository_documents(
            source_id=source_id,
            connector_id=connector_id,
            query=str(polling_config.get("query") or ""),
            page_size=fetch_page_size,
            sort=str(polling_config.get("sort") or "updated"),
            order=str(polling_config.get("order") or "desc"),
            auth_env_var=str(polling_config.get("auth_env_var") or "").strip() or None,
        )
        return _apply_batch_filters(batch, polling_config=polling_config, page_size=page_size)

    raise ValueError(
        f"Live discovery connector '{connector_id}' is not configured for source '{source_id}'."
    )


def _load_fixture_documents(
    *,
    source_id: str,
    connector_id: str,
    fixture_path: Path,
    page_size: int,
) -> dict[str, Any]:
    if not fixture_path.exists():
        raise ValueError(f"Discovery fixture not found for source '{source_id}': {fixture_path}")

    with fixture_path.open() as handle:
        payload = json.load(handle)

    documents = list(payload.get("documents") or [])[:page_size]
    fetched_at = _parse_datetime(payload.get("fetched_at")) or _utcnow()
    return {
        "source_id": source_id,
        "connector_id": connector_id,
        "mode": "fixture",
        "fetched_at": fetched_at,
        "query": payload.get("query"),
        "source_url": payload.get("source_url"),
        "documents": documents,
        "fixture_path": str(fixture_path),
    }


def _fetch_europe_pmc_documents(
    *,
    source_id: str,
    connector_id: str,
    query: str,
    page_size: int,
) -> dict[str, Any]:
    if not query:
        raise ValueError(f"Europe PMC connector for '{source_id}' is missing a query.")

    params = urlencode(
        {
            "query": query,
            "format": "json",
            "pageSize": page_size,
        }
    )
    source_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?{params}"
    payload = _read_json_url(source_url)
    results = (((payload.get("resultList") or {}).get("result")) or [])[:page_size]

    documents: list[dict[str, Any]] = []
    for item in results:
        authors = _split_author_string(item.get("authorString"))
        title = str(item.get("title") or "").strip()
        abstract_text = str(item.get("abstractText") or item.get("journalTitle") or "").strip()
        if not title:
            continue
        source_identifier = str(item.get("id") or item.get("pmid") or title).strip()
        documents.append(
            {
                "source_id": source_id,
                "source_identifier": source_identifier,
                "document_type": "paper",
                "title": title,
                "abstract_text": abstract_text,
                "url": _best_europe_pmc_url(item),
                "canonical_url": _best_europe_pmc_url(item),
                "pmid": _clean_identifier(item.get("pmid")),
                "doi": _clean_identifier(item.get("doi")),
                "authors": authors,
                "organizations": [],
                "published_at": _parse_datetime(item.get("firstPublicationDate") or item.get("pubYear")),
            }
        )

    return {
        "source_id": source_id,
        "connector_id": connector_id,
        "mode": "live",
        "fetched_at": _utcnow(),
        "query": query,
        "source_url": source_url,
        "documents": documents,
    }


def _fetch_clinical_trials_documents(
    *,
    source_id: str,
    connector_id: str,
    query: str,
    page_size: int,
) -> dict[str, Any]:
    if not query:
        raise ValueError(f"ClinicalTrials.gov connector for '{source_id}' is missing a query.")

    params = urlencode(
        {
            "query.term": query,
            "pageSize": page_size,
        }
    )
    source_url = f"https://clinicaltrials.gov/api/v2/studies?{params}"
    payload = _read_json_url(source_url)
    studies = list(payload.get("studies") or [])[:page_size]

    documents: list[dict[str, Any]] = []
    for study in studies:
        protocol = study.get("protocolSection") or {}
        identification = protocol.get("identificationModule") or {}
        description = protocol.get("descriptionModule") or {}
        sponsors = protocol.get("sponsorCollaboratorsModule") or {}
        status = protocol.get("statusModule") or {}

        nct_id = _clean_identifier(identification.get("nctId"))
        title = str(
            identification.get("briefTitle")
            or identification.get("officialTitle")
            or ""
        ).strip()
        abstract_text = str(
            description.get("briefSummary")
            or description.get("detailedDescription")
            or ""
        ).strip()
        if not title:
            continue

        lead_sponsor = ((sponsors.get("leadSponsor") or {}).get("name")) or "ClinicalTrials.gov"
        documents.append(
            {
                "source_id": source_id,
                "source_identifier": nct_id or title,
                "document_type": "trial",
                "title": title,
                "abstract_text": abstract_text,
                "url": f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else source_url,
                "canonical_url": f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else source_url,
                "nct_id": nct_id,
                "authors": ["ClinicalTrials.gov"],
                "organizations": [str(lead_sponsor).strip()],
                "published_at": _parse_datetime(
                    ((status.get("lastUpdatePostDateStruct") or {}).get("date"))
                    or status.get("lastUpdatePostDate")
                    or ((status.get("studyFirstPostDateStruct") or {}).get("date"))
                ),
            }
        )

    return {
        "source_id": source_id,
        "connector_id": connector_id,
        "mode": "live",
        "fetched_at": _utcnow(),
        "query": query,
        "source_url": source_url,
        "documents": documents,
    }


def _fetch_feed_documents(
    *,
    source_id: str,
    connector_id: str,
    feed_url: str,
    page_size: int,
    document_type: str,
) -> dict[str, Any]:
    if not feed_url:
        raise ValueError(f"Feed connector for '{source_id}' is missing a feed URL.")

    payload = _read_text_url(feed_url)
    root = ElementTree.fromstring(payload)
    entries = _find_feed_entries(root)[:page_size]
    documents: list[dict[str, Any]] = []

    for entry in entries:
        title = _child_text(entry, "title")
        abstract_text = _child_text(entry, "summary") or _child_text(entry, "description")
        link = _child_link(entry)
        published_at = (
            _parse_datetime(_child_text(entry, "updated"))
            or _parse_datetime(_child_text(entry, "published"))
            or _parse_datetime(_child_text(entry, "pubDate"))
        )
        author = _child_text(entry, "name") or _child_text(entry, "author")
        if not title:
            continue
        documents.append(
            {
                "source_id": source_id,
                "source_identifier": _child_text(entry, "id") or link or title,
                "document_type": document_type,
                "title": title,
                "abstract_text": abstract_text,
                "url": link,
                "canonical_url": link,
                "authors": [author] if author else [],
                "organizations": [],
                "published_at": published_at,
            }
        )

    return {
        "source_id": source_id,
        "connector_id": connector_id,
        "mode": "live",
        "fetched_at": _utcnow(),
        "query": None,
        "source_url": feed_url,
        "documents": documents,
    }


def _fetch_github_repository_documents(
    *,
    source_id: str,
    connector_id: str,
    query: str,
    page_size: int,
    sort: str,
    order: str,
    auth_env_var: str | None,
) -> dict[str, Any]:
    if not query:
        raise ValueError(f"GitHub connector for '{source_id}' is missing a query.")

    params = urlencode(
        {
            "q": query,
            "per_page": page_size,
            "sort": sort or "updated",
            "order": order or "desc",
        }
    )
    source_url = f"https://api.github.com/search/repositories?{params}"
    payload = _read_json_url(source_url, auth_env_var=auth_env_var)
    repositories = list(payload.get("items") or [])[:page_size]

    documents: list[dict[str, Any]] = []
    for repository in repositories:
        title = str(repository.get("full_name") or repository.get("name") or "").strip()
        description = str(repository.get("description") or "").strip()
        owner = repository.get("owner") or {}
        topics = [
            str(item).strip()
            for item in repository.get("topics") or []
            if str(item).strip()
        ]
        if not title:
            continue
        abstract_text = description or ", ".join(topics)
        documents.append(
            {
                "source_id": source_id,
                "source_identifier": str(repository.get("id") or title),
                "document_type": "repository",
                "title": title,
                "abstract_text": abstract_text,
                "url": str(repository.get("html_url") or "").strip() or None,
                "canonical_url": str(repository.get("html_url") or "").strip() or None,
                "authors": [str(owner.get("login") or "").strip()] if str(owner.get("login") or "").strip() else [],
                "organizations": [str(owner.get("login") or "").strip()] if str(owner.get("login") or "").strip() else [],
                "published_at": _parse_datetime(
                    repository.get("pushed_at") or repository.get("updated_at") or repository.get("created_at")
                ),
                "topics": topics,
                "language": repository.get("language"),
                "stargazers_count": repository.get("stargazers_count"),
                "forks_count": repository.get("forks_count"),
                "open_issues_count": repository.get("open_issues_count"),
                "archived": repository.get("archived"),
                "visibility": repository.get("visibility"),
            }
        )

    return {
        "source_id": source_id,
        "connector_id": connector_id,
        "mode": "live",
        "fetched_at": _utcnow(),
        "query": query,
        "source_url": source_url,
        "documents": documents,
    }


def _apply_batch_filters(
    batch: dict[str, Any],
    *,
    polling_config: dict[str, Any],
    page_size: int,
) -> dict[str, Any]:
    original_documents = list(batch.get("documents") or [])
    filtered_documents, filtered_out_count = _filter_documents(
        original_documents,
        polling_config=polling_config,
        page_size=page_size,
    )
    batch = dict(batch)
    batch["documents"] = filtered_documents
    batch["fetched_document_count"] = len(original_documents)
    batch["retained_document_count"] = len(filtered_documents)
    batch["filtered_out_count"] = filtered_out_count
    if _normalize_terms(polling_config.get("include_terms")):
        batch["include_terms"] = _normalize_terms(polling_config.get("include_terms"))
    if _normalize_terms(polling_config.get("exclude_terms")):
        batch["exclude_terms"] = _normalize_terms(polling_config.get("exclude_terms"))
    min_stars = _coerce_non_negative_int(polling_config.get("min_stars"))
    if min_stars is not None:
        batch["min_stars"] = min_stars
    return batch


def _filter_documents(
    documents: list[dict[str, Any]],
    *,
    polling_config: dict[str, Any],
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    include_terms = _normalize_terms(polling_config.get("include_terms"))
    exclude_terms = _normalize_terms(polling_config.get("exclude_terms"))
    min_stars = _coerce_non_negative_int(polling_config.get("min_stars"))

    kept: list[dict[str, Any]] = []
    filtered_out_count = 0
    for document in documents:
        searchable_text = _document_filter_text(document)
        if include_terms and not any(term in searchable_text for term in include_terms):
            filtered_out_count += 1
            continue
        if exclude_terms and any(term in searchable_text for term in exclude_terms):
            filtered_out_count += 1
            continue
        if min_stars is not None and document.get("stargazers_count") is not None:
            stars = _coerce_non_negative_int(document.get("stargazers_count")) or 0
            if stars < min_stars:
                filtered_out_count += 1
                continue
        kept.append(document)
        if len(kept) >= page_size:
            break
    filtered_out_count += max(0, len(documents) - filtered_out_count - len(kept))
    return kept, filtered_out_count


def _has_document_filters(polling_config: dict[str, Any]) -> bool:
    return bool(
        _normalize_terms(polling_config.get("include_terms"))
        or _normalize_terms(polling_config.get("exclude_terms"))
        or _coerce_non_negative_int(polling_config.get("min_stars")) is not None
    )


def _normalize_terms(value: object) -> list[str]:
    if isinstance(value, str):
        values = [value]
    else:
        values = list(value or [])
    return [str(item).strip().lower() for item in values if str(item).strip()]


def _document_filter_text(document: dict[str, Any]) -> str:
    parts = [
        str(document.get("title") or ""),
        str(document.get("abstract_text") or ""),
        " ".join(str(item) for item in document.get("authors") or []),
        " ".join(str(item) for item in document.get("organizations") or []),
        " ".join(str(item) for item in document.get("topics") or []),
        str(document.get("language") or ""),
    ]
    return " ".join(parts).lower()


def _read_json_url(url: str, *, auth_env_var: str | None = None) -> dict[str, Any]:
    with urlopen(_build_request(url, auth_env_var=auth_env_var), timeout=DEFAULT_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def _read_text_url(url: str) -> str:
    with urlopen(_build_request(url), timeout=DEFAULT_TIMEOUT_SECONDS) as response:
        return response.read().decode("utf-8")


def _build_request(url: str, *, auth_env_var: str | None = None) -> Request:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, application/atom+xml, application/rss+xml, text/xml, */*",
    }
    if "api.github.com" in url:
        headers["Accept"] = "application/vnd.github+json"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    if auth_env_var:
        token = str(os.environ.get(auth_env_var) or "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
    return Request(url, headers=headers)


def _resolve_fixture_path(value: object, *, source_id: str) -> Path:
    text = str(value or "").strip()
    if text:
        return resolve_data_path("research", text) if not text.startswith("/") else Path(text)
    return DISCOVERY_FIXTURE_ROOT / f"{source_id}.json"


def _find_feed_entries(root: ElementTree.Element) -> list[ElementTree.Element]:
    entries = [node for node in root.iter() if _local_name(node.tag) in {"entry", "item"}]
    return entries


def _child_text(element: ElementTree.Element, name: str) -> str:
    for child in element.iter():
        if child is element:
            continue
        if _local_name(child.tag) == name:
            return "".join(child.itertext()).strip()
    return ""


def _child_link(element: ElementTree.Element) -> str:
    for child in element.iter():
        if child is element:
            continue
        if _local_name(child.tag) != "link":
            continue
        href = str(child.attrib.get("href") or "").strip()
        if href:
            return href
        text = "".join(child.itertext()).strip()
        if text:
            return text
    return ""


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _split_author_string(value: object) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    return [item.strip().rstrip(".") for item in text.split(",") if item.strip()]


def _best_europe_pmc_url(item: dict[str, Any]) -> str | None:
    pmid = _clean_identifier(item.get("pmid"))
    doi = _clean_identifier(item.get("doi"))
    if pmid:
        return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
    if doi:
        return f"https://doi.org/{quote(doi)}"
    return None


def _coerce_positive_int(value: object) -> int | None:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _coerce_non_negative_int(value: object) -> int | None:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _clean_identifier(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _parse_datetime(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None

    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        parsed = None

    if parsed is None:
        for date_format in ("%Y-%m-%d", "%Y-%m", "%Y"):
            try:
                parsed = datetime.strptime(text, date_format)
                break
            except ValueError:
                continue

    if parsed is None:
        try:
            parsed = parsedate_to_datetime(text)
        except (TypeError, ValueError):
            return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)
