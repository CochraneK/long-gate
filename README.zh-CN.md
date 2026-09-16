<div align="center">

# Long Gate

### 让 AI 理解敏感数据，而不是把敏感数据交给 AI。

**面向 AI Agent 的 local-first 隐私网关与能力边界。**

[English](README.md) · [Safe Demo](https://long-gate-demo-production.up.railway.app) · [5 分钟上手](docs/getting-started.md) · [FAQ](docs/faq.md)

</div>

---

## 30 秒看懂 Long Gate

很多 AI 隐私方案依赖一句话：

> “你可以访问这个文件，但请不要泄露它。”

Long Gate 的立场不同：

> **如果联网 AI 不应该看到原始数据，就不要给它读取原始数据的能力。**

Long Gate 把任务拆成不同披露等级：

```text
原始敏感数据（本地）
        │
        ├─ 只问字段 / 类型 ─────→ 只给 schema
        │
        ├─ 探索 / 原型分析 ─────→ 本地生成 synthetic twin
        │
        └─ 正式统计 ───────────→ 真实数据本地精确计算
                                      │
                                      ↓
                                聚合结果 / 安全工件
                                      │
                                  LONG GATE
                                      │
                                      ↓
                                  联网 AI
```

原始 row-level 数据和 pseudonymized row-level 数据默认都不能越过 Long Gate。

---

## 最简单的本地 AI 配置

你不需要先学习 GGUF、Q4_K_M、llama.cpp。

### 1. 安装

```bash
pip install -e '.[models,local-llm]'
```

### 2. 一条命令配置本地模型

```bash
longgate model setup
```

Long Gate 会自动：

1. 检测系统 RAM；
2. 从受控的 curated catalog 选择模型；
3. 下载固定的 Hugging Face revision；
4. 校验 SHA-256；
5. 写入本地 Model Vault；
6. 设置为默认模型。

当前推荐：

| 系统内存 | 默认模型 | GGUF 大小 |
|---:|---|---:|
| 约 8 GB | `qwen3-4b` | 约 2.5 GB |
| 约 16 GB | `qwen3-8b` | 约 5.03 GB |
| 约 24 GB+ | `qwen3-14b` | 约 9 GB |

然后：

```bash
longgate model verify auto
```

### 3. 私密数据处理时直接使用本地默认模型

```bash
longgate semantic-transform-local interview.txt \
  --model auto \
  --out preview.txt
```

这里的 `auto` 只会解析已经安装并重新校验过的本地模型，**不会联网下载**。

---

## “Long Gate 会下载模型”与“模型必须本地”冲突吗？

不冲突。

Long Gate 把两个阶段拆开：

```text
MODEL SETUP MODE
网络：YES
敏感数据：NO
Model Vault：WRITE

        ↓ 完成安装

PRIVATE PROCESSING MODE
网络：NO
敏感数据：YES
Model Vault：READ ONLY
```

危险的不是“模型曾经从互联网下载”。

危险的是：

> **同一个进程既能读取原始敏感数据，又能自由联网。**

Long Gate 要切断的是这个组合。

---

## 让你自己的 AI 帮你配置

运行：

```bash
longgate setup-prompt
```

复制输出，粘贴给你的 coding assistant / computer-use agent。

这个提示词会明确要求它：

- 不打开、不搜索、不读取任何真实敏感数据；
- 只在 Setup Mode 联网；
- 自动创建虚拟环境；
- 安装 Long Gate；
- 运行 `longgate model setup`；
- 校验模型；
- 不使用云端模型或可配置远程 HTTP endpoint 处理私密数据；
- 最后告诉你真正离线处理时该运行哪条命令。

也可以直接查看：

[AI 自动配置提示词](docs/ai-setup-prompt.md)

---

## Windows / macOS / Linux

### Windows

在已经 clone 的仓库里：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
```

### macOS / Linux

```bash
bash scripts/bootstrap.sh
```

完整手把手教程：

[Getting Started — 5 minutes](docs/getting-started.md)

遇到 llama.cpp、磁盘空间、R、PDF 等问题：

[Troubleshooting](docs/troubleshooting.md)

---

## 精确统计不需要上传原始表格

Long Gate 不要求拿 synthetic 数据替代正式统计。

例如：

```bash
longgate exact study.csv ols \
  --outcome score \
  --predictor age \
  --predictor group
```

真实数据留在本机，本地执行器计算：

```text
β / SE / CI / p / N / R²
```

随后 aggregate guard 再检查结果。

还支持固定模板式 R：

```bash
longgate exact study.csv ols \
  --engine r \
  --outcome score \
  --predictor age
```

R engine 不接受任意 R 脚本。

---

## 非结构化文本目前仍然 fail-closed

Long Gate 可以本地检查：

- TXT
- Markdown
- DOCX
- PDF text layer

也可以使用本地 GGUF 做 semantic preview。

但目前：

```text
release_allowed = false
```

即使没有检测到姓名、邮箱或长文本复制，也不代表已经证明“语义匿名”。

---

## 当前安全边界

```text
RAW rows                → NEVER network eligible
PSEUDONYMIZED rows      → NEVER network eligible
UNKNOWN purpose         → BLOCK
final PII hit           → BLOCK
free text               → LOCAL ONLY
semantic preview        → LOCAL ONLY
path escapes SafeRoot   → BLOCK
```

Long Gate 没有 `--force-release`。

---

## Trust Report

每次结构化 pipeline 都会生成离线、自包含的 Trust Report，展示：

- 什么留在本地；
- 谁能看到什么；
- 哪些列被识别为 identifier / sensitive；
- 哪些 privacy attacks 被检查；
- 是否移除了 identifier；
- egress scan 是否通过；
- 是否发生网络传输；
- 输入 hash、策略、版本和 provenance。

公开静态示例：

[Long Gate Safe Demo](https://long-gate-demo-production.up.railway.app)

---

## 它不声称什么

Long Gate 当前**不声称**：

- synthetic data 自动等于匿名；
- 已获得 HIPAA / GDPR / NHS 等认证；
- row-level synthetic 已达到生产级安全释放；
- semantic rewrite 自动等于匿名；
- 能抵御被攻陷的宿主操作系统/管理员；
- PDF 零命中就代表文档没有隐私风险。

这些限制会明确写出来，而不是藏在脚注里。

---

## 参与项目

我们尤其欢迎：

- membership / linkage / attribute inference attacks；
- multilingual / Chinese PII；
- differential privacy adapters；
- semantic privacy evaluation；
- local sandbox / capability isolation；
- reproducible research；
- Trust Report UX；
- attack benchmark fixtures。

查看：

- [Roadmap](ROADMAP.md)
- [Contributing](CONTRIBUTING.md)
- [Threat Model](docs/threat-model.md)
- [Benchmarks](docs/benchmarks.md)
- [FAQ](docs/faq.md)

---

<div align="center">

### 敏感数据应该有边界。

如果你也认为 AI 不该靠一句“请不要看”来保护私密数据，欢迎 ⭐ Long Gate。

</div>
