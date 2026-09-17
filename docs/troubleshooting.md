# Troubleshooting

## `longgate model setup` cannot detect RAM

Pass it explicitly:

```bash
longgate model setup --ram-gb 16
```

The RAM recommendation is approximate. Context length, GPU offload, the operating system, and other applications also consume memory.

---

## Model download fails

Check:

1. Internet access is available in **Model Setup Mode**.
2. You have enough free disk space. Long Gate checks the selected Model Vault before downloading and reserves roughly the model size plus 1 GB of headroom.
3. Hugging Face is reachable from your network.
4. The Model Vault directory is writable.

If the default drive is full, move the Model Vault:

```bash
export LONGGATE_MODEL_VAULT=/larger/drive/longgate-models
longgate model setup
```

Windows PowerShell:

```powershell
$env:LONGGATE_MODEL_VAULT = "D:\LongGate\models"
longgate model setup
```

Retry:

```bash
longgate model setup
```

Long Gate downloads a pinned upstream revision and verifies SHA-256. A checksum mismatch fails closed.

---

## SHA-256 verification fails

Do not bypass the check.

Run:

```bash
longgate model verify auto
```

If the file is corrupted or does not match the curated catalog:

1. move/delete the affected GGUF file;
2. rerun `longgate model setup`;
3. verify again.

Do not add a force flag.

---

## `llama-cpp-python` fails to install

The upstream package may compile native code when a compatible wheel is not available.
This is why Long Gate keeps `local-llm` optional during the first installation.

On Windows, check the Python version first:

```powershell
python --version
longgate doctor
```

For the quickest CPU-only setup, create a Python 3.12 environment and use the
upstream wheel index:

```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[models,documents,local-llm]"
python -m pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

If pip still says `Building wheel`, it did not find a matching wheel and is
compiling from source. Either use Python 3.12 with the CPU index above or
install the Windows C++ build toolchain and allow the longer build.

Start with:

```bash
python -m pip install -U pip
python -m pip install llama-cpp-python
```

Typical build requirements:

- Windows: Visual Studio C++ Build Tools or another supported compiler toolchain;
- macOS: Xcode command-line tools;
- Linux: GCC or Clang plus normal build tools.

### Apple Silicon / Metal

The upstream project publishes a Metal wheel index for compatible systems:

```bash
python -m pip install llama-cpp-python \
  --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/metal
```

### NVIDIA CUDA

The upstream project also publishes CUDA-specific wheel indexes.

Use the wheel matching your installed CUDA version rather than guessing.

Long Gate intentionally does not auto-select a GPU wheel because mismatched CUDA/runtime combinations are machine-specific.

After installing:

```bash
longgate doctor
```

---

## `Rscript` is missing

R exact analysis is optional.

Python exact analysis works without R.

Check:

```bash
longgate doctor
```

If you want the R engine, install R locally and ensure `Rscript` is on `PATH`.

---

## PDF shows zero PII hits but visibly contains names

That can happen for scanned/image-only PDFs.

The current PDF path reads the PDF text layer and does not OCR image content.

Zero extracted PII hits therefore **do not grant release permission**.

---

## Model setup works, but private processing should be offline

Correct.

Model provisioning and private processing are intentionally different capability zones.

Recommended hardened pattern:

```text
setup worker:
  network = YES
  private mount = NO
  model vault = WRITE

private worker:
  network = NO
  private mount = YES
  model vault = READ ONLY
```

See `docker-compose.model-setup.yml` and `docker-compose.hardened.yml`.

---

## I want to use a different GGUF

Advanced users may pass a local file path directly:

```bash
longgate semantic-transform-local interview.txt \
  --model /absolute/path/custom.gguf \
  --out preview.txt
```

This path does not download the file and does not add it to the curated catalog.

For reproducibility and supply-chain metadata, the built-in Model Vault aliases are preferred.

---

## I want Long Gate to support another model officially

Open a feature request with:

- official upstream repository;
- license;
- exact GGUF filename;
- immutable upstream revision;
- SHA-256;
- approximate file size;
- why it improves the curated catalog.

The catalog should stay small and reviewable.
