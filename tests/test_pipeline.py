import json
from pathlib import Path

from longgate.pipeline import run_pipeline


def test_demo_backend_falls_back_to_safe_aggregate(tmp_path: Path):
    source = Path(__file__).parents[1] / "examples" / "demo.csv"
    result = run_pipeline(source, tmp_path, backend_name="demo", seed=7)
    assert result.status == "PASS"
    assert result.release_class == "aggregate"
    assert result.report_path.exists()
    assert result.synthetic_path.exists()
    assert result.staged_payload is not None
    assert result.staged_payload.name == "safe_aggregate.json"
    manifest = json.loads((result.out_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["decision"]["allow"] is False
    assert manifest["release_resolution"]["row_level_release_allowed"] is False
    assert manifest["release_resolution"]["aggregate_fallback_used"] is True
    assert manifest["release_resolution"]["granted_release_class"] == "aggregate"
    assert manifest["network"]["network_transmission_performed"] is False


def test_report_does_not_embed_demo_names(tmp_path: Path):
    source = Path(__file__).parents[1] / "examples" / "demo.csv"
    result = run_pipeline(source, tmp_path, backend_name="demo", seed=11)
    html = result.report_path.read_text(encoding="utf-8")
    assert "Alice Example" not in html
    assert "+00-000-0000-0001" not in html
    assert "default-src 'none'" in html
