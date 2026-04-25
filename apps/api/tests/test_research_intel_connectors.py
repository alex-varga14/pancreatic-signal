from app.services import research_intel_connectors as connectors


def test_github_repository_connector_normalizes_repository_results(monkeypatch) -> None:
    def fake_read_json_url(url: str, *, auth_env_var: str | None = None) -> dict[str, object]:
        assert "api.github.com/search/repositories" in url
        assert auth_env_var == "GITHUB_TOKEN"
        return {
            "items": [
                {
                    "id": 101,
                    "full_name": "pancreatic-signal/pdac-benchmark-kit",
                    "description": "Open-source PDAC benchmark and dataset tooling.",
                    "html_url": "https://github.com/pancreatic-signal/pdac-benchmark-kit",
                    "owner": {"login": "pancreatic-signal"},
                    "topics": ["pancreatic", "pdac", "benchmark"],
                    "language": "Python",
                    "stargazers_count": 12,
                    "forks_count": 2,
                    "open_issues_count": 1,
                    "archived": False,
                    "visibility": "public",
                    "updated_at": "2026-04-03T10:00:00Z",
                }
            ]
        }

    monkeypatch.setattr(connectors, "_read_json_url", fake_read_json_url)

    batch = connectors.collect_research_documents_for_source(
        {
            "source_id": "open_source_watch",
            "polling_config": {
                "connector_id": "github_repository_search",
                "default_mode": "live",
                "query": "\"pancreatic cancer\"",
                "auth_env_var": "GITHUB_TOKEN",
                "include_terms": ["pancreatic", "pdac"],
                "min_stars": 1,
            },
        },
        mode="live",
        max_documents_per_source=5,
    )

    assert batch["connector_id"] == "github_repository_search"
    assert batch["documents"]
    document = batch["documents"][0]
    assert document["title"] == "pancreatic-signal/pdac-benchmark-kit"
    assert document["document_type"] == "repository"
    assert document["authors"] == ["pancreatic-signal"]
    assert document["organizations"] == ["pancreatic-signal"]
    assert document["stargazers_count"] == 12
    assert batch["retained_document_count"] == 1


def test_feed_connector_filters_broad_results_to_pancreatic_relevance(monkeypatch) -> None:
    feed_xml = """
    <rss version="2.0">
      <channel>
        <item>
          <title>Pancreatic biomarker update</title>
          <description>New pancreatic liquid biopsy evidence for high-risk surveillance.</description>
          <link>https://example.org/pancreatic</link>
          <pubDate>Fri, 04 Apr 2026 10:00:00 GMT</pubDate>
        </item>
        <item>
          <title>Breast oncology update</title>
          <description>Irrelevant for this focused watchtower.</description>
          <link>https://example.org/breast</link>
          <pubDate>Fri, 04 Apr 2026 09:00:00 GMT</pubDate>
        </item>
        <item>
          <title>General cancer policy update</title>
          <description>Broad policy notice without organ-specific relevance.</description>
          <link>https://example.org/general</link>
          <pubDate>Fri, 04 Apr 2026 08:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>
    """

    monkeypatch.setattr(connectors, "_read_text_url", lambda url: feed_xml)

    batch = connectors.collect_research_documents_for_source(
        {
            "source_id": "nci",
            "polling_config": {
                "connector_id": "rss_feed",
                "default_mode": "live",
                "feed_url": "https://example.org/rss.xml",
                "document_type": "guidance",
                "include_terms": ["pancreatic", "pancreas", "pdac"],
            },
        },
        mode="live",
        max_documents_per_source=5,
    )

    assert len(batch["documents"]) == 1
    assert batch["documents"][0]["title"] == "Pancreatic biomarker update"
    assert batch["filtered_out_count"] == 2
