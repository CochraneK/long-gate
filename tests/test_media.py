from __future__ import annotations

import sys
import types
import wave
from pathlib import Path

import pytest

import longgate.media as media


class _FakeImage:
    size = (640, 480)
    mode = "RGB"

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def getexif(self):
        return {34853: "redacted-gps-placeholder", 271: "camera"}

    def close(self):
        return None


def test_image_metadata_path_stays_local(monkeypatch, tmp_path: Path):
    path = tmp_path / "photo.jpg"
    path.write_bytes(b"not-used")
    monkeypatch.setattr(
        media,
        "_pillow_image",
        lambda _path: _FakeImage(),
    )
    result = media.inspect_image_file(path)
    assert result.width == 640
    assert result.height == 480
    assert result.gps_metadata_present is True
    assert result.content_inspected is False
    assert result.release_allowed is False
    assert "redacted-gps-placeholder" not in str(result.to_dict())


def test_image_ocr_returns_counts_not_text(monkeypatch, tmp_path: Path):
    path = tmp_path / "scan.png"
    path.write_bytes(b"not-used")
    monkeypatch.setattr(
        media,
        "_pillow_image",
        lambda _path: _FakeImage(),
    )
    monkeypatch.setattr(
        media,
        "_ocr_pil_image",
        lambda _image: "Contact person@example.com",
    )
    result = media.ocr_image_local(path)
    assert result.pii_hits >= 1
    assert result.release_allowed is False
    assert "person@example.com" not in str(result.to_dict())


def test_pdf_ocr_is_local_and_bounded(monkeypatch, tmp_path: Path):
    path = tmp_path / "scan.pdf"
    path.write_bytes(b"not-used")
    pages = [_FakeImage(), _FakeImage()]
    monkeypatch.setattr(
        media,
        "_render_pdf_pages",
        lambda _path, max_pages: pages[:max_pages],
    )
    monkeypatch.setattr(
        media,
        "_ocr_pil_image",
        lambda _image: "Call +44 7700 900123",
    )
    result = media.ocr_pdf_local(path, max_pages=1)
    assert result.units_processed == 1
    assert result.pii_hits >= 1
    assert result.release_allowed is False
    assert "+44 7700 900123" not in str(result.to_dict())


def test_pdf_page_pixel_limit_is_checked_before_render(monkeypatch, tmp_path: Path):
    path = tmp_path / "huge.pdf"
    path.write_bytes(b"not-used")
    render_called = False

    class FakePage:
        def get_size(self):
            return (100_000.0, 100_000.0)

        def render(self, *, scale):
            nonlocal render_called
            render_called = True
            raise AssertionError(f"render should not run at scale={scale}")

    class FakeDocument:
        def __init__(self, _path):
            self.page = FakePage()

        def __len__(self):
            return 1

        def __getitem__(self, _index):
            return self.page

        def close(self):
            return None

    monkeypatch.setitem(
        sys.modules,
        "pypdfium2",
        types.SimpleNamespace(PdfDocument=FakeDocument),
    )

    with pytest.raises(ValueError, match="pixel safety limit"):
        media._render_pdf_pages(path, 1)
    assert render_called is False


def test_pdf_ocr_rejects_unbounded_zero_pages(tmp_path: Path):
    path = tmp_path / "scan.pdf"
    path.write_bytes(b"not-used")
    with pytest.raises(ValueError):
        media.ocr_pdf_local(path, max_pages=0)


def test_wav_metadata_path_never_marks_content_safe(tmp_path: Path):
    path = tmp_path / "voice.wav"
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\x00\x00" * 800)

    result = media.inspect_audio_file(path)
    assert result.channels == 1
    assert result.sample_rate_hz == 8000
    assert result.duration_seconds == pytest.approx(0.1)
    assert result.content_inspected is False
    assert result.release_allowed is False


def test_giant_image_is_rejected_before_privacy_processing(
    monkeypatch,
    tmp_path: Path,
):
    class GiantImage(_FakeImage):
        size = (200_000, 200_000)

    path = tmp_path / "huge.jpg"
    path.write_bytes(b"not-used")
    monkeypatch.setattr(
        media,
        "_pillow_image",
        lambda _path: GiantImage(),
    )
    with pytest.raises(ValueError, match="pixel safety limit"):
        media.inspect_image_file(path)
