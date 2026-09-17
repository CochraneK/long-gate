from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "research" / "datasets" / "tab-v1.json"
RAW_BASE = "https://raw.githubusercontent.com"


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: str | Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1 or manifest.get("id") != "tab-v1":
        raise ValueError("Expected TAB v1 dataset manifest.")
    commit = manifest.get("repository_commit")
    if not isinstance(commit, str) or len(commit) != 40:
        raise ValueError("TAB manifest must pin a full repository commit SHA.")
    files = manifest.get("files")
    if not isinstance(files, dict) or not {"train", "dev", "test", "license"} <= files.keys():
        raise ValueError("TAB manifest must define train/dev/test/license files.")
    return manifest


def _raw_url(repository: str, commit: str, relative_path: str) -> str:
    parts = repository.rstrip("/").split("/")
    if len(parts) < 2:
        raise ValueError("Invalid canonical_repository URL.")
    owner, repo = parts[-2], parts[-1]
    return f"{RAW_BASE}/{owner}/{repo}/{commit}/{relative_path}"


def download_bytes(url: str, *, timeout: int = 60) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "long-gate-research-artifact/1"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310 - HTTPS pinned GitHub host built internally
        final_url = response.geturl()
        if not final_url.startswith("https://raw.githubusercontent.com/"):
            raise RuntimeError(f"Unexpected TAB download redirect: {final_url}")
        return response.read()


def prepare_tab(
    output_dir: str | Path,
    *,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    downloader=download_bytes,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    output = Path(output_dir).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)

    repository = str(manifest["canonical_repository"])
    commit = str(manifest["repository_commit"])
    file_records: dict[str, dict[str, object]] = {}

    for role, relative_path in manifest["files"].items():
        relative_path = str(relative_path)
        url = _raw_url(repository, commit, relative_path)
        payload = downloader(url)
        target = output / Path(relative_path).name
        target.write_bytes(payload)
        file_records[str(role)] = {
            "filename": target.name,
            "source_path": relative_path,
            "source_url": url,
            "sha256": _sha256_bytes(payload),
            "bytes": len(payload),
        }

    provenance = {
        "schema_version": 1,
        "dataset_id": manifest["id"],
        "release_label": manifest["release_label"],
        "canonical_repository": repository,
        "repository_commit": commit,
        "license": manifest["license"],
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "files": file_records,
        "note": (
            "Downloaded from immutable upstream Git commit. Corpus bytes are kept in the "
            "local research data cache and are not vendored into the Long Gate repository."
        ),
    }
    (output / "tab-provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return provenance


def verify_prepared_tab(
    output_dir: str | Path,
    *,
    manifest_path: str | Path = DEFAULT_MANIFEST,
) -> list[str]:
    errors: list[str] = []
    output = Path(output_dir).expanduser().resolve()
    provenance_path = output / "tab-provenance.json"
    if not provenance_path.is_file():
        return ["missing tab-provenance.json"]

    manifest = load_manifest(manifest_path)
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    if provenance.get("repository_commit") != manifest.get("repository_commit"):
        errors.append("prepared TAB commit does not match pinned manifest commit")
    if provenance.get("license") != manifest.get("license"):
        errors.append("prepared TAB license metadata does not match manifest")

    files = provenance.get("files")
    if not isinstance(files, dict):
        return errors + ["invalid TAB provenance files object"]

    for role, relative_path in manifest["files"].items():
        record = files.get(role)
        if not isinstance(record, dict):
            errors.append(f"missing provenance record for {role}")
            continue
        target = output / Path(str(relative_path)).name
        if not target.is_file():
            errors.append(f"missing prepared TAB file: {target.name}")
            continue
        expected = record.get("sha256")
        actual = _sha256_file(target)
        if expected != actual:
            errors.append(f"TAB checksum mismatch: {target.name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download/verify TAB v1 from the exact upstream Git commit pinned by Long Gate."
    )
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    if args.verify_only:
        errors = verify_prepared_tab(args.out, manifest_path=args.manifest)
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        print("Prepared TAB dataset verified")
        return 0

    provenance = prepare_tab(args.out, manifest_path=args.manifest)
    print(json.dumps(provenance, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
