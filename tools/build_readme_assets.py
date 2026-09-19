#!/usr/bin/env python3
"""Generate bilingual README SVGs from canonical Long Gate project status."""
from __future__ import annotations

import html
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "project-status.json"
OUT = ROOT / "docs" / "assets" / "readme"

BG = "#071421"
PANEL = "#0c2133"
PANEL2 = "#102b42"
GRID = "#21465f"
TEXT = "#f5f7fb"
MUTED = "#a8bfd2"
ACCENT = "#5dd6c0"
BLUE = "#69a8ff"
HARDENED = "#5dd6c0"
IMPLEMENTED = "#69a8ff"
RESEARCH = "#f3c969"
PLANNED = "#8798aa"
DANGER = "#f07a7a"

STATE_COLOR = {
    "hardened": HARDENED,
    "implemented": IMPLEMENTED,
    "research": RESEARCH,
    "planned": PLANNED,
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def load_status() -> dict:
    return json.loads(STATUS.read_text(encoding="utf-8"))


def shell(title: str, subtitle: str, width: int, height: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">',
        f"<title>{esc(title)}</title>",
        f'<rect width="{width}" height="{height}" rx="30" fill="{BG}"/>',
        '<style>text{font-family:Inter,"Noto Sans SC","Microsoft YaHei","PingFang SC",'
        'system-ui,sans-serif}.title{font-size:48px;font-weight:800;fill:#f5f7fb}'
        '.sub{font-size:22px;fill:#a8bfd2}.h{font-size:23px;font-weight:760;fill:#f5f7fb}'
        '.b{font-size:18px;fill:#d7e2eb}.m{font-size:15px;fill:#8faabd}'
        '.metric{font-size:42px;font-weight:850;fill:#f5f7fb}</style>',
        f'<text x="{width/2}" y="72" text-anchor="middle" class="title">{esc(title)}</text>',
        f'<text x="{width/2}" y="108" text-anchor="middle" class="sub">{esc(subtitle)}</text>',
    ]


def defs() -> str:
    return (
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" '
        'orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#69a8ff"/></marker></defs>'
    )


def box(
    parts: list[str],
    x: int,
    y: int,
    width: int,
    height: int,
    title: str,
    body: str = "",
    stroke: str = GRID,
) -> None:
    parts.append(
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="22" '
        f'fill="{PANEL}" stroke="{stroke}" stroke-width="2"/>'
    )
    parts.append(f'<text x="{x + 24}" y="{y + 42}" class="h">{esc(title)}</text>')
    if body:
        parts.append(f'<text x="{x + 24}" y="{y + 72}" class="b">{esc(body)}</text>')


def arrow(
    parts: list[str],
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    label: str = "",
) -> None:
    parts.append(
        f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{BLUE}" stroke-width="4" '
        'stroke-linecap="round" marker-end="url(#arrow)"/>'
    )
    if label:
        parts.append(
            f'<text x="{(x1 + x2) / 2}" y="{(y1 + y2) / 2 - 10}" '
            f'text-anchor="middle" class="m">{esc(label)}</text>'
        )


def hero(data: dict, lang: str) -> str:
    zh = lang == "zh"
    counts = Counter(item["state"] for item in data["capabilities"])
    title = (
        "LONG GATE · 把敏感数据挡在门内"
        if zh
        else "LONG GATE · Keep sensitive data behind the gate"
    )
    subtitle = data["mission_zh"] if zh else data["mission_en"]
    parts = shell(title, subtitle, 1600, 520)
    parts.append(
        '<path d="M0 390 C260 310 430 470 720 390 S1260 300 1600 385 V520 H0 Z" '
        'fill="#0a2032"/>'
    )
    labels = [
        ("已加固" if zh else "HARDENED", counts["hardened"], HARDENED),
        ("已实现" if zh else "IMPLEMENTED", counts["implemented"], IMPLEMENTED),
        ("研究中" if zh else "RESEARCH", counts["research"], RESEARCH),
        ("计划中" if zh else "PLANNED", counts["planned"], PLANNED),
    ]
    for index, (label, value, color) in enumerate(labels):
        x = 120 + index * 360
        parts.append(
            f'<rect x="{x}" y="205" width="300" height="120" rx="22" fill="{PANEL}" '
            f'stroke="{color}" stroke-width="2"/>'
        )
        parts.append(f'<text x="{x + 26}" y="258" class="metric">{value}</text>')
        parts.append(f'<text x="{x + 26}" y="294" class="b">{esc(label)}</text>')
    footer = (
        "状态来自 project-status.json · README 图可重建"
        if zh
        else "State comes from project-status.json · README visuals are rebuildable"
    )
    parts.append(f'<text x="800" y="455" text-anchor="middle" class="m">{esc(footer)}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def trust_boundary(lang: str) -> str:
    zh = lang == "zh"
    title = (
        "数据不是被提醒保护，而是被能力边界保护"
        if zh
        else "Data is protected by capability boundaries, not reminders"
    )
    subtitle = (
        "原始数据留在本地；只有被支持、审计并明确批准的工件才能跨门"
        if zh
        else "Raw data stays local; only supported, audited, explicitly approved artifacts cross"
    )
    parts = shell(title, subtitle, 1600, 720)
    parts.append(defs())
    box(
        parts,
        70,
        190,
        330,
        190,
        "私密区" if zh else "PRIVATE ZONE",
        "原始数据 · 禁止联网" if zh else "raw data · no network",
        HARDENED,
    )
    box(
        parts,
        500,
        170,
        600,
        230,
        "LONG GATE",
        "策略 · 审计 · manifest · purpose · SHA-256"
        if zh
        else "policy · audit · manifest · purpose · SHA-256",
        ACCENT,
    )
    box(
        parts,
        1200,
        190,
        330,
        190,
        "联网区" if zh else "NETWORK ZONE",
        "只读已批准工件" if zh else "approved artifact only",
        BLUE,
    )
    arrow(parts, 400, 285, 500, 285, "本地证据" if zh else "local evidence")
    arrow(parts, 1100, 285, 1200, 285, "明确批准" if zh else "explicit approval")
    parts.append(
        f'<rect x="570" y="470" width="460" height="110" rx="22" fill="{PANEL2}" '
        f'stroke="{DANGER}" stroke-width="2"/>'
    )
    parts.append(
        f'<text x="800" y="515" text-anchor="middle" class="h">'
        f'{esc("原始 / 假名化行级数据" if zh else "RAW / PSEUDONYMIZED ROWS")}</text>'
    )
    parts.append(
        f'<text x="800" y="550" text-anchor="middle" class="b">'
        f'{esc("永不具备网络外发资格" if zh else "NEVER network eligible")}</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def capability_zones(lang: str) -> str:
    zh = lang == "zh"
    title = (
        "四个能力区，避免一个进程同时拥有所有权力"
        if zh
        else "Four capability zones keep dangerous powers separated"
    )
    subtitle = (
        "网络、私密数据、模型写入和可疑输入不放进同一个能力集合"
        if zh
        else "Network, private data, model writes, and suspicious input are deliberately separated"
    )
    parts = shell(title, subtitle, 1600, 720)
    zones = [
        (
            80,
            "配置区" if zh else "SETUP",
            ["network ✓", "private data ✕", "model vault write ✓"],
            BLUE,
        ),
        (
            470,
            "私密处理区" if zh else "PRIVATE",
            ["network ✕", "private data ✓", "model vault read-only"],
            HARDENED,
        ),
        (
            860,
            "隔离区" if zh else "QUARANTINE",
            ["network ✕", "untrusted input read-only", "bounded scratch"],
            RESEARCH,
        ),
        (
            1250,
            "联网区" if zh else "NETWORK",
            ["network ✓", "private data ✕", "approved safe workspace"],
            IMPLEMENTED,
        ),
    ]
    for x, name, lines, color in zones:
        parts.append(
            f'<rect x="{x}" y="185" width="270" height="300" rx="24" fill="{PANEL}" '
            f'stroke="{color}" stroke-width="3"/>'
        )
        parts.append(f'<text x="{x + 135}" y="237" text-anchor="middle" class="h">{esc(name)}</text>')
        for index, line in enumerate(lines):
            parts.append(f'<text x="{x + 28}" y="{300 + index * 48}" class="b">{esc(line)}</text>')
    note = (
        "默认禁止：同一进程既能读取原始私密数据，又能自由联网。"
        if zh
        else "Unsafe default: one process can read raw private data and freely access the network."
    )
    parts.append(f'<text x="800" y="610" text-anchor="middle" class="b">{esc(note)}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def observability(lang: str) -> str:
    zh = lang == "zh"
    title = (
        "Security Observability · 看见出站路径，但不制造第二份泄漏"
        if zh
        else "Security observability · see egress without creating a second leak"
    )
    subtitle = (
        "Secret → Endpoint → HAR → Quarantine：默认输出元数据与风险类别，不回显敏感值"
        if zh
        else "Secret → endpoint → HAR → quarantine: metadata and risk classes, not sensitive values"
    )
    parts = shell(title, subtitle, 1600, 650)
    parts.append(defs())
    boxes = [
        (
            70,
            "密钥" if zh else "SECRETS",
            ["Gitleaks", "工作树 + Git 历史" if zh else "current tree + history"],
            HARDENED,
        ),
        (
            450,
            "端点" if zh else "ENDPOINT",
            ["域名 · DNS · TLS" if zh else "hostname · DNS · TLS", "可能中转 ≠ 已证明" if zh else "relay-possible ≠ proven"],
            BLUE,
        ),
        (
            830,
            "HAR 抓包" if zh else "HAR",
            ["PII 计数 · 字段名" if zh else "PII counts · field names", "不回显正文" if zh else "no body echo"],
            RESEARCH,
        ),
        (
            1210,
            "隔离区" if zh else "QUARANTINE",
            ["断网 · 非 root" if zh else "no network · non-root", "只读输入" if zh else "read-only input"],
            HARDENED,
        ),
    ]
    for x, name, lines, color in boxes:
        parts.append(
            f'<rect x="{x}" y="210" width="310" height="220" rx="24" fill="{PANEL}" '
            f'stroke="{color}" stroke-width="2"/>'
        )
        parts.append(f'<text x="{x + 155}" y="265" text-anchor="middle" class="h">{esc(name)}</text>')
        for index, line in enumerate(lines):
            parts.append(
                f'<text x="{x + 155}" y="{325 + index * 38}" text-anchor="middle" '
                f'class="b">{esc(line)}</text>'
            )
    for x in (380, 760, 1140):
        arrow(parts, x, 320, x + 60, 320)
    note = (
        "这些只是证据；任何观测结果都不会自动授予外发权限。"
        if zh
        else "Evidence informs a decision. It never grants egress by itself."
    )
    parts.append(f'<text x="800" y="535" text-anchor="middle" class="b">{esc(note)}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def maturity(data: dict, lang: str) -> str:
    zh = lang == "zh"
    parts = shell(
        "能力成熟度" if zh else "Capability maturity",
        "Hardened / Implemented / Research / Planned 来自 canonical project status"
        if zh
        else "Hardened / Implemented / Research / Planned from canonical project status",
        1600,
        900,
    )
    labels = {
        "hardened": "已加固" if zh else "Hardened",
        "implemented": "已实现" if zh else "Implemented",
        "research": "研究中" if zh else "Research",
        "planned": "计划中" if zh else "Planned",
    }
    for index, item in enumerate(data["capabilities"]):
        col = 0 if index < 6 else 1
        row = index if index < 6 else index - 6
        x = 70 + col * 780
        y = 170 + row * 105
        label = item["label_zh"] if zh else item["label_en"]
        color = STATE_COLOR[item["state"]]
        parts.append(
            f'<rect x="{x}" y="{y}" width="700" height="78" rx="18" fill="{PANEL}" '
            f'stroke="{GRID}"/>'
        )
        parts.append(f'<circle cx="{x + 30}" cy="{y + 39}" r="9" fill="{color}"/>')
        parts.append(f'<text x="{x + 52}" y="{y + 34}" class="h">{esc(label)}</text>')
        parts.append(f'<text x="{x + 52}" y="{y + 59}" class="m">{esc(labels[item["state"]])}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def handoff(lang: str) -> str:
    zh = lang == "zh"
    parts = shell(
        "换电脑、换账号、换 Agent，也能从 Git 继续"
        if zh
        else "Switch computer, account, or agent — continue from Git",
        "handoff/ 是冷启动入口；代码、测试和 security invariants 仍是技术真相"
        if zh
        else "handoff/ is the cold-start bridge; code, tests, and security invariants remain technical truth",
        1600,
        650,
    )
    parts.append(defs())
    box(
        parts,
        90,
        200,
        350,
        220,
        "handoff/README.md",
        "阅读顺序 + canonical 边界" if zh else "read order + canonical boundaries",
        ACCENT,
    )
    box(
        parts,
        625,
        165,
        350,
        290,
        "AGENT_HANDOFF.md",
        "使命 · 已完成 · 下一步 · 禁区" if zh else "mission · done · next · do-not",
        BLUE,
    )
    box(
        parts,
        1160,
        200,
        350,
        220,
        "Canonical repo",
        "代码 · 测试 · 状态 · 安全不变量" if zh else "code · tests · status · invariants",
        HARDENED,
    )
    arrow(parts, 440, 310, 625, 310)
    arrow(parts, 975, 310, 1160, 310)
    parts.append(
        '<text x="800" y="535" text-anchor="middle" class="b">'
        "STATUS · TODO · DECISIONS · CONTEXT · CHATLOG · SESSION_LOG</text>"
    )
    parts.append("</svg>")
    return "\n".join(parts)


def render_all(data: dict) -> dict[str, str]:
    rendered: dict[str, str] = {}
    for lang in ("zh", "en"):
        rendered[f"{lang}/hero.svg"] = hero(data, lang)
        rendered[f"{lang}/trust-boundary.svg"] = trust_boundary(lang)
        rendered[f"{lang}/capability-zones.svg"] = capability_zones(lang)
        rendered[f"{lang}/security-observability.svg"] = observability(lang)
        rendered[f"{lang}/capability-maturity.svg"] = maturity(data, lang)
        rendered[f"{lang}/handoff.svg"] = handoff(lang)
    return rendered


def main() -> int:
    rendered = render_all(load_status())
    for relative, content in rendered.items():
        path = OUT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
    print(f"Generated {len(rendered)} README SVG assets from {STATUS.name}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
