from pathlib import Path
import json

from longgate.pipeline import run_pipeline


def test_demo_backend_is_fail_closed(tmp_path: Path):
    source = Path(__file__).parents[1] / "examples" / "demo.csv"
    result = run_pipeline(source, tmp_path, backend_name="demo", seed=7)
    assert result.status == "BLOCKED"
    assert result.report_path.exists()
    assert result.synthetic_path.exists()
    assert result.staged_payload is None
    manifest = json.loads((result.out_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["decision"]["allow"] is False
    assert manifest["network"]["network_transmission_performed"] is False


def test_report_does_not_embed_demo_names(tmp_path: Path):
    source = Path(__file__).parents[1] / "examples" / "demo.csv"
    result = run_pipeline(source, tmp_path, backend_name="demo", seed=11)
    html = result.report_path.read_text(encoding="utf-8")
    assert "Alice Example" not in html
    assert "+00-000-0000-0001" not in html
    assert "default-src 'none'" in html
