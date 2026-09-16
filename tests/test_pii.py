from longgate.pii import scan_structured_strings
import pandas as pd

from longgate.pii import scan_dataframe_values, scan_text


def test_value_scanner_counts_without_returning_values():
    df = pd.DataFrame(
        {
            "notes": ["contact test@example.com", "call +44 7700 900123", None],
            "x": [1, 2, 3],
        }
    )
    result = scan_dataframe_values(df)
    assert result.total_hits >= 2
    payload = str(result.to_dict())
    assert "test@example.com" not in payload
    assert "7700" not in payload


def test_scan_text_detects_email():
    result = scan_text('{"email":"person@example.com"}')
    assert result.by_entity["email"] == 1


def test_structured_scan_ignores_numeric_phone_like_decimals():
    result = scan_structured_strings(
        {
            "std": 0.875595035770913,
            "nested": {"mean": 3.0276503540974917},
        }
    )
    assert result.total_hits == 0


def test_structured_scan_still_detects_string_pii():
    result = scan_structured_strings(
        {"group": "person@example.com"}
    )
    assert result.total_hits >= 1
