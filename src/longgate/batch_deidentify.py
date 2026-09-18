from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from dataclasses import asdict, dataclass
from pathlib import Path

from .document_deidentify import deidentify_file_copy
from .format_deidentify import DirectIdentifierMapper
from .utils import atomic_write_bytes, sha256_file, write_json

_BATCH_FORMAT = "long-gate-batch-deidentify-v1"
_BATCH_KEY_NAME = ".longgate-batch.key"
_BATCH_STATE_NAME = ".longgate-batch-state.json"
_BATCH_KEY_BYTES = 32
SUPPORTED_BATCH_SUFFIXES = {
    ".txt",
    ".md",
    ".markdown",
    ".html",
    ".htm",
    ".xlsx",
    ".docx",
}


@dataclass(frozen=True)
class BatchDeidentifyResult:
    status: str
    output_dir: str
    state_path: str
    total_files: int
    processed_files: int
    resumed_files: int
    manual_review_files: int
    local_only_files: int
    release_allowed: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _token(secret: bytes, namespace: str, value: str) -> str:
    payload = f"{namespace}\0{value}".encode("utf-8")
    return hmac.new(secret, payload, hashlib.sha256).hexdigest()


def _checkpoint_mac(secret: bytes, state: dict[str, object]) -> str:
    payload = {key: value for key, value in state.items() if key != "checkpoint_mac"}
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hmac.new(
        secret,
        b"long-gate-batch-checkpoint-v1\0" + encoded,
        hashlib.sha256,
    ).hexdigest()


def _seal_state(secret: bytes, state: dict[str, object]) -> dict[str, object]:
    sealed = dict(state)
    sealed["checkpoint_mac"] = _checkpoint_mac(secret, sealed)
    return sealed


def _read_secret(path: Path) -> bytes:
    secret = path.read_bytes()
    if len(secret) != _BATCH_KEY_BYTES:
        raise ValueError("Invalid batch key length; refusing to resume.")
    return secret


def _load_state(path: Path, secret: bytes) -> dict[str, object]:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Batch checkpoint is unreadable or invalid.") from exc
    if not isinstance(state, dict) or state.get("format") != _BATCH_FORMAT:
        raise ValueError("Unsupported or invalid batch checkpoint format.")
    checkpoint_mac = state.get("checkpoint_mac")
    if not isinstance(checkpoint_mac, str) or not hmac.compare_digest(
        checkpoint_mac,
        _checkpoint_mac(secret, state),
    ):
        raise ValueError("Batch checkpoint authentication failed.")
    if not isinstance(state.get("mapper_state"), dict):
        raise ValueError("Batch checkpoint is missing entity-map state.")
    if not isinstance(state.get("completed"), dict):
        raise ValueError("Batch checkpoint is missing completed-file state.")
    root_token = state.get("input_root_token")
    if not isinstance(root_token, str) or not hmac.compare_digest(
        root_token, root_token.lower()
    ):
        raise ValueError("Batch checkpoint root token is invalid.")
    if not all(character in "0123456789abcdef" for character in root_token):
        raise ValueError("Batch checkpoint root token is invalid.")
    if len(root_token) != 64:
        raise ValueError("Batch checkpoint root token is invalid.")
    return state


def _collect_files(root: Path, *, recursive: bool) -> list[Path]:
    candidates = root.rglob("*") if recursive else root.iterdir()
    return sorted(
        (
            path
            for path in candidates
            if path.is_file()
            and not path.is_symlink()
            and path.suffix.lower() in SUPPORTED_BATCH_SUFFIXES
        ),
        key=lambda path: path.relative_to(root).as_posix().casefold(),
    )


def _count_status(
    record: dict[str, object],
    manual_review_files: int,
    local_only_files: int,
) -> tuple[int, int]:
    if record.get("status") == "LOCAL_ONLY":
        local_only_files += 1
    else:
        manual_review_files += 1
    return manual_review_files, local_only_files


def deidentify_batch(
    input_dir: str | Path,
    output_dir: str | Path,
    *,
    recursive: bool = False,
    resume: bool = False,
) -> BatchDeidentifyResult:
    """De-identify a directory with a shared HMAC-backed entity map and checkpoints."""
    source_root = Path(input_dir).expanduser().resolve()
    output_root = Path(output_dir).expanduser().resolve()
    if not source_root.is_dir():
        raise NotADirectoryError(source_root)
    if output_root == source_root or output_root.is_relative_to(source_root):
        raise ValueError("Batch output directory must be outside the input directory.")

    state_path = output_root / _BATCH_STATE_NAME
    key_path = output_root / _BATCH_KEY_NAME

    if resume:
        if not state_path.is_file() or not key_path.is_file():
            raise ValueError("No complete batch checkpoint/key pair exists to resume.")
        secret = _read_secret(key_path)
        state = _load_state(state_path, secret)
        expected_root = _token(secret, "input-root", str(source_root))
        if not hmac.compare_digest(str(state["input_root_token"]), expected_root):
            raise ValueError("Batch checkpoint belongs to a different input directory.")
        mapper = DirectIdentifierMapper(
            key_secret=secret,
            state=state["mapper_state"],
        )
    else:
        if state_path.exists() or key_path.exists():
            raise ValueError(
                "Batch state already exists. Use --resume or choose a fresh output directory."
            )
        if output_root.exists() and any(output_root.iterdir()):
            raise ValueError("Fresh batch output directory must be empty.")
        output_root.mkdir(parents=True, exist_ok=True)
        secret = secrets.token_bytes(_BATCH_KEY_BYTES)
        atomic_write_bytes(key_path, secret)
        mapper = DirectIdentifierMapper(key_secret=secret)
        state = {
            "format": _BATCH_FORMAT,
            "input_root_token": _token(secret, "input-root", str(source_root)),
            "mapper_state": mapper.export_state(),
            "completed": {},
        }
        state = _seal_state(secret, state)
        write_json(state_path, state)

    files = _collect_files(source_root, recursive=recursive)
    if not files:
        raise ValueError("No supported files were found in the input directory.")

    completed = state["completed"]
    if not isinstance(completed, dict):
        raise ValueError("Batch checkpoint completed state is invalid.")

    processed_files = 0
    resumed_files = 0
    manual_review_files = 0
    local_only_files = 0

    for source in files:
        relative = source.relative_to(source_root)
        relative_text = relative.as_posix()
        path_token = _token(secret, "relative-path", relative_text)
        destination = output_root / relative
        input_sha256 = sha256_file(source)

        previous = completed.get(path_token)
        if resume and isinstance(previous, dict):
            expected_output_sha = previous.get("output_sha256")
            if (
                previous.get("input_sha256") == input_sha256
                and isinstance(expected_output_sha, str)
                and destination.is_file()
                and sha256_file(destination) == expected_output_sha
            ):
                resumed_files += 1
                manual_review_files, local_only_files = _count_status(
                    previous,
                    manual_review_files,
                    local_only_files,
                )
                continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        result = deidentify_file_copy(source, destination, mapper=mapper)
        record: dict[str, object] = {
            "input_sha256": input_sha256,
            "output_sha256": result.output_sha256,
            "status": result.status,
        }
        completed[path_token] = record
        state["mapper_state"] = mapper.export_state()
        state["completed"] = completed
        state = _seal_state(secret, state)
        completed = state["completed"]
        write_json(state_path, state)

        processed_files += 1
        manual_review_files, local_only_files = _count_status(
            record,
            manual_review_files,
            local_only_files,
        )

    status = (
        "COMPLETED_WITH_LOCAL_ONLY"
        if local_only_files
        else "COMPLETED_LOCAL_REVIEW_REQUIRED"
    )
    return BatchDeidentifyResult(
        status=status,
        output_dir=str(output_root),
        state_path=str(state_path),
        total_files=len(files),
        processed_files=processed_files,
        resumed_files=resumed_files,
        manual_review_files=manual_review_files,
        local_only_files=local_only_files,
        release_allowed=False,
    )
