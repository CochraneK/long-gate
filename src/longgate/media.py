from __future__ import annotations

import math
import wave
from dataclasses import asdict, dataclass
from pathlib import Path

from .pii import scan_text


MAX_IMAGE_PIXELS = 100_000_000


class MediaDependencyMissing(RuntimeError):
    pass


@dataclass(frozen=True)
class ImageInspection:
    path: str
    kind: str
    width: int
    height: int
    mode: str
    exif_tag_count: int
    gps_metadata_present: bool
    content_inspected: bool
    release_allowed: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class OCRInspection:
    path: str
    kind: str
    units_processed: int
    extracted_characters: int
    pii_hits: int
    pii_by_entity: dict[str, int]
    release_allowed: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class AudioInspection:
    path: str
    kind: str
    channels: int
    sample_rate_hz: int
    frames: int
    duration_seconds: float
    content_inspected: bool
    release_allowed: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _pillow_image(path: Path):
    try:
        from PIL import Image
    except ImportError as exc:
        raise MediaDependencyMissing(
            "Image inspection requires: pip install 'long-gate[media]'"
        ) from exc
    return Image.open(path)


def _validate_image_dimensions(width: int, height: int) -> None:
    if width < 1 or height < 1:
        raise ValueError("Image dimensions must be positive.")
    if width * height > MAX_IMAGE_PIXELS:
        raise ValueError(
            "Image exceeds Long Gate's local pixel safety limit."
        )


def inspect_image_file(path: str | Path) -> ImageInspection:
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}:
        raise ValueError(f"Unsupported image type: {suffix}")

    with _pillow_image(source) as image:
        exif = image.getexif()
        gps_present = 34853 in exif
        width, height = image.size
        _validate_image_dimensions(int(width), int(height))
        mode = str(image.mode)

    return ImageInspection(
        path=source.name,
        kind=suffix.lstrip("."),
        width=int(width),
        height=int(height),
        mode=mode,
        exif_tag_count=len(exif),
        gps_metadata_present=gps_present,
        content_inspected=False,
        release_allowed=False,
        reason=(
            "Image metadata was inspected locally. Pixel content is not "
            "declared privacy-safe and network egress remains blocked."
        ),
    )


def _ocr_pil_image(image: object) -> str:
    try:
        import pytesseract
    except ImportError as exc:
        raise MediaDependencyMissing(
            "Local OCR requires: pip install 'long-gate[ocr]' and a local "
            "Tesseract executable."
        ) from exc
    try:
        return str(pytesseract.image_to_string(image))
    except Exception as exc:
        raise RuntimeError(
            "Local OCR failed. Long Gate does not use a network OCR fallback."
        ) from exc


def ocr_image_local(path: str | Path) -> OCRInspection:
    source = Path(path)
    with _pillow_image(source) as image:
        width, height = image.size
        _validate_image_dimensions(int(width), int(height))
        text = _ocr_pil_image(image)
    findings = scan_text(text)
    return OCRInspection(
        path=source.name,
        kind="image-ocr",
        units_processed=1,
        extracted_characters=len(text),
        pii_hits=findings.total_hits,
        pii_by_entity=findings.by_entity,
        release_allowed=False,
        reason=(
            "OCR ran locally and only aggregate PII counts are returned. "
            "OCR output remains local-only and does not gain egress permission."
        ),
    )


def _render_pdf_pages(path: Path, max_pages: int) -> list[object]:
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise MediaDependencyMissing(
            "Scanned-PDF OCR requires: pip install 'long-gate[ocr]'"
        ) from exc
    document = pdfium.PdfDocument(str(path))
    pages: list[object] = []
    render_scale = 2.0
    try:
        count = min(len(document), max_pages)
        for index in range(count):
            page = document[index]
            width, height = page.get_size()
            rendered_width = math.ceil(float(width) * render_scale)
            rendered_height = math.ceil(float(height) * render_scale)
            _validate_image_dimensions(rendered_width, rendered_height)
            bitmap = page.render(scale=render_scale)
            pages.append(bitmap.to_pil())
    finally:
        document.close()
    return pages


def ocr_pdf_local(
    path: str | Path,
    max_pages: int = 50,
) -> OCRInspection:
    source = Path(path)
    if source.suffix.lower() != ".pdf":
        raise ValueError("Scanned-PDF OCR accepts PDF files only.")
    if max_pages < 1:
        raise ValueError("max_pages must be at least 1.")

    pages = _render_pdf_pages(source, max_pages)
    chunks: list[str] = []
    for image in pages:
        try:
            width, height = image.size
            _validate_image_dimensions(int(width), int(height))
            chunks.append(_ocr_pil_image(image))
        finally:
            close = getattr(image, "close", None)
            if callable(close):
                close()
    text = "\n".join(chunks)
    findings = scan_text(text)
    return OCRInspection(
        path=source.name,
        kind="pdf-ocr",
        units_processed=len(pages),
        extracted_characters=len(text),
        pii_hits=findings.total_hits,
        pii_by_entity=findings.by_entity,
        release_allowed=False,
        reason=(
            "PDF pages were rendered and OCR-scanned locally. Extracted text "
            "and images remain local-only; no network OCR fallback is allowed."
        ),
    )


def inspect_audio_file(path: str | Path) -> AudioInspection:
    source = Path(path)
    if source.suffix.lower() != ".wav":
        raise ValueError(
            "The baseline audio privacy path supports WAV metadata only."
        )
    try:
        with wave.open(str(source), "rb") as audio:
            channels = int(audio.getnchannels())
            sample_rate = int(audio.getframerate())
            frames = int(audio.getnframes())
    except (wave.Error, EOFError) as exc:
        raise ValueError("Invalid or unsupported WAV file.") from exc

    duration = frames / sample_rate if sample_rate else 0.0
    return AudioInspection(
        path=source.name,
        kind="wav",
        channels=channels,
        sample_rate_hz=sample_rate,
        frames=frames,
        duration_seconds=round(duration, 6),
        content_inspected=False,
        release_allowed=False,
        reason=(
            "Audio metadata was inspected locally. Speech/content has not been "
            "de-identified, so audio remains network-blocked."
        ),
    )
