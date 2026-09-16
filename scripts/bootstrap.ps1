$ErrorActionPreference = "Stop"

Write-Host "[Long Gate] MODEL SETUP MODE"
Write-Host "This script installs software/models only. Do not pass private data to it."

$Python = "py"
try {
    & $Python -3 --version | Out-Null
} catch {
    Write-Error "Python 3 was not found. Install Python 3.10+ first."
    exit 1
}

& $Python -3 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e ".[models,local-llm,documents,stats]"

& .\.venv\Scripts\longgate.exe doctor
& .\.venv\Scripts\longgate.exe model setup
& .\.venv\Scripts\longgate.exe model verify auto

Write-Host ""
Write-Host "[Long Gate] READY"
Write-Host "Private processing example:"
Write-Host ".\.venv\Scripts\longgate.exe semantic-transform-local interview.txt --model auto --out preview.txt"
Write-Host ""
Write-Host "For hardened private processing, disable network access before using real sensitive data."
