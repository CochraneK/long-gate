import json

from longgate.egress_inspect import inspect_har


def test_har_inspection_counts_sensitive_data_without_echoing_values(tmp_path):
    secret = "sk-test-value-that-must-never-be-reported"
    email = "person@example.com"
    har = {
        "log": {
            "entries": [
                {
                    "request": {
                        "method": "POST",
                        "url": "https://api.openai.com/v1/chat/completions?api_key=query-secret",
                        "headers": [
                            {"name": "Authorization", "value": f"Bearer {secret}"},
                            {"name": "Content-Type", "value": "application/json"},
                        ],
                        "cookies": [{"name": "session", "value": "cookie-secret"}],
                        "postData": {
                            "mimeType": "application/json",
                            "text": json.dumps(
                                {
                                    "messages": [{"role": "user", "content": f"Email {email}"}],
                                    "api_key": secret,
                                }
                            ),
                        },
                    }
                }
            ]
        }
    }
    path = tmp_path / "capture.har"
    path.write_text(json.dumps(har), encoding="utf-8")

    result = inspect_har(path)
    payload = result.to_dict()
    rendered = json.dumps(payload)

    assert result.entries == 1
    assert result.total_pii_hits >= 1
    assert result.entries_with_sensitive_headers == 1
    assert result.entries_with_sensitive_query == 1
    assert result.entries_with_secret_field_names == 1
    assert payload["requests"][0]["provider_hint"] == "OpenAI"
    assert "authorization" in payload["requests"][0]["sensitive_header_names"]
    assert "api_key" in payload["requests"][0]["sensitive_query_names"]
    assert secret not in rendered
    assert email not in rendered
    assert "query-secret" not in rendered
    assert "cookie-secret" not in rendered


def test_har_unknown_endpoint_is_only_marked_relay_possible(tmp_path):
    har = {
        "log": {
            "entries": [
                {
                    "request": {
                        "method": "POST",
                        "url": "https://ai-proxy.example.test/v1/chat",
                        "headers": [],
                        "cookies": [],
                        "postData": {"text": "{}"},
                    }
                }
            ]
        }
    }
    path = tmp_path / "proxy.har"
    path.write_text(json.dumps(har), encoding="utf-8")

    result = inspect_har(path)
    request = result.requests[0]
    assert request.endpoint_classification == "CUSTOM_OR_UNKNOWN_ENDPOINT"
    assert request.relay_possible is True
    assert request.provider_hint is None
