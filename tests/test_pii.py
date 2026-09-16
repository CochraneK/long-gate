import pandas as pd

from longgate.pii import scan_dataframe_values, scan_text


def test_value_scanner_counts_without_returning_values():
    df = pd.DataFrame({
        "notes": ["contact test@example.com", "call +44 7700 900123", None],
        "x": [1, 2, 3],
    })
    result = scan_dataframe_values(df)
    assert result.total_hits >= 2
    payload = str(result.to_dict())
    assert "test@example.com" not in payload
    assert "7700" not in payload


def test_scan_text_detects_email():
    result = scan_text('{"email":"person@example.com"}')
    assert result.by_entity["email"] == 1
