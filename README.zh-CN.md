<div align="center">

# Long Gate

### 让 AI 理解敏感数据，而不是把敏感数据交给 AI。

**面向 AI Agent 的 local-first 隐私网关与能力边界。**

[English](README.md) · [5 分钟上手](docs/getting-started.md) · [Roadmap](ROADMAP.md)

</div>

---

## 30 秒看懂

Long Gate 不依赖一句“请不要泄露”。它的原则是：

> **如果联网 AI 不应该看到原始数据，就不要给它读取原始数据的能力。**

当前 pre-1.0 基线：

```text
原始 row-level 数据            → 不允许联网
pseudonymized row-level       → 不允许联网
row-level synthetic           → 硬锁
安全 disclosure-limited aggregate → 可进入明确审批链
本地 AI 语义脱敏结果             → 当前仍 local-only
```

---

# 现在最简单的用法

安装本地模型与文档处理能力：

```bash
git clone https://github.com/CochraneK/long-gate.git
cd long-gate
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e '.[models,local-llm,documents]'
```

先只看机器适合什么：

```bash
longgate setup --recommend-only
```

Long Gate 会**本地**检测：

- 操作系统 / 架构；
- CPU 逻辑核心数；
- RAM；
- Model Vault 所在磁盘剩余空间；
- 本机有 `nvidia-smi` 时的 NVIDIA GPU / VRAM；
- FAST / BALANCED / QUALITY 三档模型适配情况。

不下载时只做推荐；真正配置：

```bash
longgate setup
```

会自动完成：

```text
硬件检查
  ↓
RAM-led 模型推荐
  ↓
下载固定 revision
  ↓
SHA-256 校验
  ↓
写入 Model Vault
  ↓
READY
```

Setup Mode 可以联网，但不应该挂载或打开私密数据。

---

# 两条主路径

```mermaid
flowchart TD
    START["你有私密数据"] --> SETUP["1 · longgate setup"]
    SETUP --> KIND{"数据类型？"}

    KIND -->|"表格"| TABLE["2A · longgate run"]
    TABLE --> TR["Structured Trust Report"]
    TR --> SAFE{"有可释放 aggregate？"}
    SAFE -->|"有"| APPROVE["本地 path + SHA-256 + purpose 批准"]
    APPROVE --> MCP["longgate-mcp"]
    MCP --> AI["联网 AI 只读被批准工件"]
    SAFE -->|"没有"| L1["LOCAL_ONLY + next_actions"]

    KIND -->|"TXT / Markdown / DOCX / PDF"| DEID["2B · longgate deidentify"]
    DEID --> LOOP["本地 AI 脱敏 + 审计 + 有界重试"]
    LOOP --> SR["格式保真脱敏报告"]
    SR --> RESULT{"结果"}
    RESULT -->|"机械证据通过"| REVIEW["MANUAL_REVIEW_CANDIDATE"]
    RESULT -->|"仍有风险"| L2["LOCAL_ONLY"]
    REVIEW --> HOLD["当前仍然不自动上云"]
```

最重要的一点：

> **处理成功 ≠ 已获准给联网 AI 看。**

---

# 路线 A：私密表格

```bash
longgate inspect study.csv
longgate run study.csv --profile research --backend auto
```

Structured release ladder：

```text
row-level synthetic
   ↓ pre-1.0 hard-lock
disclosure-limited aggregate
   ↓ 如果仍不适合
LOCAL_ONLY + next_actions
```

真实统计可以继续留在本机：

```bash
longgate exact study.csv describe
longgate exact study.csv correlation
longgate exact study.csv ols --outcome score --predictor age --predictor group
```

---

# 路线 B：私密文本——先保格式，再按需做语义泛化

Long Gate 现在把两件不同的事明确拆开，不再让一个 `deidentify` 命令同时承担“保留原文件”和“自由摘要改写”。

## B1 · TXT / Markdown 格式保真脱敏副本

```bash
longgate deidentify interview.md
```

默认输出：

```text
interview.deidentified.md
interview.deidentified.md.audit.json
interview.deidentified.md.trust-report.html
```

`deidentify` 会保持原有标题、段落、换行和非敏感正文，只把明确识别出的直接标识符替换成稳定占位符，例如 `[EMAIL_001]`、`[PHONE_001]`。同一个直接标识符在单文件内保持一致映射。

安全约束：

- 绝不覆盖原文件；
- 在任何写操作之前固定原文件 SHA-256；
- 输出采用同目录临时文件 + 原子替换；
- 输出必须保持与输入相同扩展名；
- 当前只支持 TXT / Markdown；其他格式 fail-closed，不伪装成“已保真处理”；
- 当前仍需人工复核姓名、组织、地点、别名、罕见事件与组合身份线索；
- `release_allowed = false`，生成脱敏副本不等于获准联网。

## B2 · 强语义泛化 / 身份脱离摘要

如果你的目标不是“保留原文件继续使用”，而是得到一个更抽象的 identity-detached summary，则使用：

```bash
longgate semantic-summarize interview.txt \
  --model auto \
  --out summary.txt
```

这保留原来的本地 GGUF 流程：

```text
原始私密文档
  ↓
deterministic 本地 pre-scrub
  ↓
已验证本地 GGUF
  ↓
语义级 identity-detached abstraction
  ↓
始终和 ORIGINAL source 比较
  ↓
PII / 数字 / n-gram / distinctive token 审计
  ↓
最多 3 轮有界 remediation
  ↓
MANUAL_REVIEW_CANDIDATE 或 LOCAL_ONLY
```

如果本地模型因为 token 上限返回截断结果，Long Gate 现在会直接失败关闭，不接受“半截脱敏文本”。

需要检查模型文件和最小本地推理时：

```bash
longgate doctor --deep --model auto
```

两条路径都遵守同一个原则：**脱敏质量判断 ≠ 网络外发授权。**

---
# 当前 Semantic evidence

`semantic-release-evidence-v1` 进入人工复核候选的机械阈值：

- direct PII = 0；
- 原文精确数字复用 = 0；
- character n-gram reuse ≤ 1%；
- distinctive token reuse ≤ 5%；
- 输出长度 ≥ 80 字符。

后续仍要继续研究：

- rare-event leakage；
- relationship leakage；
- combination uniqueness；
- 多语言 semantic attacks；
- 长文档 privacy-aware segmentation + cross-chunk audit。

---

# 硬件推荐

```bash
longgate hardware
```

当前 curated tiers：

| 档位 | 模型 | 用途 |
|---|---|---|
| FAST | `qwen3-4b` Q4_K_M | 更轻、更快 |
| BALANCED | `qwen3-8b` Q4_K_M | 中等内存的平衡选择 |
| QUALITY | `qwen3-14b` Q4_K_M | 更强语义泛化 |

最终默认仍以 RAM 为主要依据，因为 GPU offload 还取决于本机 llama.cpp build。

GPU 探测失败不会联网查询，也不会阻止 CPU-only 使用。

---

# 让联网 AI 读安全结果

当前这条自动批准链适用于 **supported structured egress artifact**，例如 disclosure-limited aggregate，不适用于 semantic text。

```bash
longgate approve-egress \
  longgate-runs/LG-123/egress/safe_aggregate.json \
  --workspace longgate-runs/LG-123/egress \
  --ledger ./longgate-policy/approvals.jsonl \
  --purpose "interpret aggregate statistics"
```

批准要求同时匹配：

```text
Long Gate egress manifest
+ policy allow=true
+ final scan passed
+ artifact filename
+ artifact SHA-256
+ exact purpose
```

任意复制进 `egress/` 的文件不能被批准；批准后改文件，hash 失效。

MCP 侧只有：

```text
gate_info()
list_safe_files(purpose)
read_safe_text(relative_path, purpose)
```

没有 arbitrary filesystem、shell、Python、approval creation 或 `--force-release`。

---

# Setup Mode 和 Private Processing 必须分开

```text
MODEL SETUP MODE
网络：YES
私密数据：NO
Model Vault：WRITE

PRIVATE PROCESSING MODE
网络：NO
私密数据：YES
Model Vault：READ ONLY
```

Long Gate 真正要切断的是：

> **同一个进程既能读原始敏感数据，又能自由联网。**

---

# 其他 local-only 能力

```bash
longgate document-inspect report.docx
longgate document-inspect transcript.pdf
longgate image-inspect photo.jpg
longgate image-ocr-local scan.png
longgate pdf-ocr-local scanned.pdf --max-pages 50
longgate audio-inspect interview.wav
```

OCR 没有云端 fallback。

---

# 当前硬安全边界

```text
RAW rows                         → NEVER network eligible
PSEUDONYMIZED rows               → NEVER network eligible
ROW-LEVEL synthetic              → pre-1.0 HARD LOCK
semantic de-identification       → LOCAL ONLY baseline
semantic retries                 → 最多 3 轮
semantic Trust Report            → 不嵌入 narrative content
UNKNOWN purpose                  → BLOCK
final structured PII hit         → BLOCK
任意复制进 egress 的文件           → 不能批准
批准后 artifact 改变              → hash 不再匹配
hardware detection failure       → 不使用远程 fallback
```

---

# Long Gate 不声称什么

目前不声称：

- synthetic data 自动匿名；
- semantic de-identification 自动匿名；
- orchestration layer 自带 formal differential privacy；
- HIPAA / GDPR / NHS 等合规认证；
- row-level synthetic 已获 production release certification；
- 任意文本 / 图片 / 音频 / PDF 已获得语义匿名保证；
- 能抵御已经被攻陷的 host OS / administrator。

---

# 核心理念

1. **Capabilities beat prompts**：不该读 raw data，就不给读取能力。
2. **Purpose determines disclosure**：只披露完成任务所需的最小表示。
3. **Evidence is not authorization**：测试通过不等于自动获得网络权限。
4. **Blocked should lead somewhere safer**：优先 remediation / 降级，而不是弱化政策。
5. **Local AI is a transformer, not the privacy authority**：模型输出还要独立审计。

---

## 文档

- [Getting Started](docs/getting-started.md)
- [Local semantic privacy path](docs/semantic-preview.md)
- [Local Model Guide](docs/models.md)
- [Security invariants](docs/security-invariants.md)
- [Threat model](docs/threat-model.md)
- [Agent boundary](docs/agent-boundary.md)
- [Roadmap](ROADMAP.md)

---

Long Gate 自身代码使用 Apache-2.0 License。
