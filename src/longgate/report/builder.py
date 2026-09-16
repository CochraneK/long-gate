from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any


def _pill(text: str, cls: str = "neutral") -> str:
    return f'<span class="pill {cls}">{escape(text)}</span>'


def build_report(data: dict[str, Any], path: Path) -> None:
    status = data["status"]
    status_cls = "ok" if status == "PASS" else "bad"
    profiles = data["profiles"]
    events = data["events"]
    audit = data["audit"]
    decision = data["decision"]

    rows = []
    for p in profiles:
        cls = p["data_class"]
        rows.append(
            "<tr>"
            f"<td><code>{escape(p['name'])}</code></td>"
            f"<td>{escape(p['dtype'])}</td>"
            f"<td>{_pill(cls, 'warn' if cls in {'identifier','quasi_identifier','sensitive','free_text'} else 'neutral')}</td>"
            f"<td>{escape(p['strategy'])}</td>"
            f"<td>{p['unique']}</td>"
            "</tr>"
        )

    timeline = "".join(
        f'<div class="event"><span>{escape(e["time"])}</span><b>{escape(e["name"])}</b><small>{escape(e["detail"])}</small></div>'
        for e in events
    )
    reasons = audit.get("reasons") or ["No blocking reason recorded."]
    reason_html = "".join(f"<li>{escape(r)}</li>" for r in reasons)
    near = audit.get("near_copy_rate")
    near_text = "n/a" if near is None else f"{near:.2%}"

    html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; font-src data:;">
<title>Long Gate Trust Report</title>
<style>
:root{{--bg:#0b1020;--panel:#11182b;--panel2:#151e35;--text:#eef3ff;--muted:#95a2be;--line:#27324b;--ok:#7ee2a8;--bad:#ff7d8b;--warn:#ffd479;--accent:#86a7ff}}
*{{box-sizing:border-box}} body{{margin:0;background:linear-gradient(180deg,#09101e,#0d1424 45%,#090e19);color:var(--text);font:15px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}}
.wrap{{max-width:1160px;margin:auto;padding:36px 22px 70px}} .hero{{padding:32px;border:1px solid var(--line);background:linear-gradient(135deg,#131d35,#0d1425);border-radius:24px;box-shadow:0 24px 70px #0005}}
.brand{{font-size:12px;letter-spacing:.22em;text-transform:uppercase;color:var(--accent)}} h1{{font-size:42px;margin:8px 0 6px}} h2{{font-size:22px;margin:0 0 16px}} .sub{{color:var(--muted);max-width:760px}}
.status{{display:flex;gap:14px;align-items:center;margin-top:24px;padding:18px;border-radius:16px;background:#0a1120;border:1px solid var(--line)}} .status strong{{font-size:20px}} .dot{{width:12px;height:12px;border-radius:50%;background:var(--{status_cls})}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:18px}} .card{{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:18px}} .metric{{font-size:28px;font-weight:750;margin-top:5px}} .label{{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}}
section{{margin-top:22px;background:var(--panel);border:1px solid var(--line);border-radius:20px;padding:22px}} .flow{{display:flex;align-items:stretch;gap:8px;flex-wrap:wrap}} .step{{flex:1;min-width:145px;background:var(--panel2);border:1px solid var(--line);border-radius:14px;padding:14px}} .arrow{{display:flex;align-items:center;color:var(--muted)}}
.pill{{display:inline-block;padding:3px 8px;border-radius:999px;background:#202a42;color:#cdd8ef;font-size:12px}} .pill.warn{{background:#41351a;color:var(--warn)}}
table{{width:100%;border-collapse:collapse}} th,td{{text-align:left;padding:11px 9px;border-bottom:1px solid var(--line);vertical-align:top}} th{{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.06em}} code{{color:#c4d1ff}}
.matrix td,.matrix th{{text-align:center}} .matrix td:first-child,.matrix th:first-child{{text-align:left}} .yes{{color:var(--ok);font-weight:700}} .no{{color:var(--bad);font-weight:700}}
.event{{display:grid;grid-template-columns:150px 180px 1fr;gap:12px;padding:10px 0;border-bottom:1px solid var(--line)}} .event span,.event small{{color:var(--muted)}} .note{{color:var(--muted);font-size:13px}} .footer{{margin-top:22px;color:var(--muted);font-size:12px;text-align:center}}
@media(max-width:800px){{.grid{{grid-template-columns:1fr 1fr}}.event{{grid-template-columns:1fr}}h1{{font-size:34px}}}}
</style>
</head>
<body><div class="wrap">
<div class="hero">
  <div class="brand">LONG GATE · TRUST REPORT</div>
  <h1>Privacy processing, made visible.</h1>
  <div class="sub">This report contains no source row values. It shows what Long Gate did, what was blocked, what could leave the trusted zone, and why.</div>
  <div class="status"><span class="dot"></span><div><div class="label">Gate status</div><strong>{escape(status)}</strong> · {escape(decision['reason'])}</div></div>
  <div class="grid">
    <div class="card"><div class="label">Rows</div><div class="metric">{data['rows']:,}</div></div>
    <div class="card"><div class="label">Columns</div><div class="metric">{data['columns']}</div></div>
    <div class="card"><div class="label">Backend</div><div class="metric" style="font-size:20px">{escape(data['backend'])}</div></div>
    <div class="card"><div class="label">Network send</div><div class="metric" style="font-size:20px">{'Staged only' if decision['allow'] else 'Blocked'}</div></div>
  </div>
</div>

<section><h2>Processing path</h2><div class="flow">
<div class="step"><b>1 · Source</b><div class="note">Local file · SHA-256 recorded</div></div><div class="arrow">→</div>
<div class="step"><b>2 · Inspect</b><div class="note">Schema + sensitivity · local</div></div><div class="arrow">→</div>
<div class="step"><b>3 · Synthesize</b><div class="note">No deterministic identity mapping</div></div><div class="arrow">→</div>
<div class="step"><b>4 · Audit</b><div class="note">Copy/linkage checks · local</div></div><div class="arrow">→</div>
<div class="step"><b>5 · Gate</b><div class="note">Default deny · safe payload only</div></div>
</div></section>

<section><h2>Who can see what</h2>
<table class="matrix"><thead><tr><th>Data</th><th>Local worker</th><th>Local model</th><th>Network AI</th></tr></thead><tbody>
<tr><td>Raw rows</td><td class="yes">YES</td><td class="yes">OPTIONAL</td><td class="no">NO</td></tr>
<tr><td>Real identifiers</td><td class="yes">YES</td><td class="yes">OPTIONAL</td><td class="no">NO</td></tr>
<tr><td>Pseudonym mapping</td><td class="yes">LOCAL ONLY</td><td class="no">NO</td><td class="no">NO</td></tr>
<tr><td>Audited synthetic rows</td><td class="yes">YES</td><td class="yes">YES</td><td class="{'yes' if decision['allow'] else 'no'}">{'ELIGIBLE' if decision['allow'] else 'NO'}</td></tr>
<tr><td>Aggregate results</td><td class="yes">YES</td><td class="yes">YES</td><td class="yes">ELIGIBLE</td></tr>
</tbody></table></section>

<section><h2>Privacy audit</h2>
<div class="grid">
<div class="card"><div class="label">Exact row overlap</div><div class="metric">{audit['exact_row_overlap']}</div></div>
<div class="card"><div class="label">Identifier overlap</div><div class="metric">{audit['identifier_overlap']}</div></div>
<div class="card"><div class="label">Quasi-combo overlap</div><div class="metric">{audit['quasi_combo_overlap']}</div></div>
<div class="card"><div class="label">Near-copy rate</div><div class="metric">{near_text}</div></div>
</div><ul>{reason_html}</ul>
<p class="note">These are v0.2 engineering checks, not a formal guarantee of anonymity or differential privacy. A backend marked demonstration-only can never pass the egress gate.</p>
</section>

<section><h2>Column treatment</h2><div style="overflow:auto"><table><thead><tr><th>Column</th><th>Type</th><th>Class</th><th>Strategy</th><th>Unique</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></section>
<section><h2>Run timeline</h2>{timeline}</section>
<section><h2>Provenance</h2><table><tbody>
<tr><th>Run ID</th><td><code>{escape(data['run_id'])}</code></td></tr>
<tr><th>Input SHA-256</th><td><code>{escape(data['input_sha256'])}</code></td></tr>
<tr><th>Policy</th><td><code>deny-by-default / v0.2</code></td></tr>
<tr><th>Long Gate version</th><td><code>{escape(data['version'])}</code></td></tr>
</tbody></table></section>
<div class="footer">Long Gate · self-contained offline report · no remote fonts, scripts, analytics, or network assets.</div>
</div></body></html>'''
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
