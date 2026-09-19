from longgate.endpoint_provenance import classify_endpoint_host, inspect_endpoint


def test_official_provider_endpoint_is_not_marked_as_relay():
    classification, provider, relay_possible = classify_endpoint_host("api.openai.com")
    assert classification == "OFFICIAL_PROVIDER_ENDPOINT"
    assert provider == "OpenAI"
    assert relay_possible is False


def test_known_router_is_explicitly_classified():
    classification, provider, relay_possible = classify_endpoint_host("openrouter.ai")
    assert classification == "KNOWN_ROUTER_OR_AGGREGATOR"
    assert provider == "OpenRouter"
    assert relay_possible is True


def test_custom_endpoint_is_relay_possible_not_proven():
    result = inspect_endpoint("https://relay.example.test/v1", connect=False)
    assert result.classification == "CUSTOM_OR_UNKNOWN_ENDPOINT"
    assert result.provider_hint is None
    assert result.relay_possible is True
    assert result.network_used is False
    assert result.resolved_ips == []
    assert result.tls is None
    assert "cannot prove" in result.evidence_limit
