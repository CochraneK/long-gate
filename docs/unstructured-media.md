# Local unstructured media privacy paths

Long Gate treats images, scanned PDFs, and audio as **private local inputs by default**.

These commands do not grant network egress.

## Image metadata inspection

Install:

```bash
pip install 'long-gate[media]'
```

Inspect dimensions and EXIF presence without returning EXIF values:

```bash
longgate image-inspect photo.jpg
```

The result reports:
- image type;
- width / height / mode;
- EXIF tag count;
- whether GPS metadata is present;
- `release_allowed: false`.

Pixel content is not declared safe merely because metadata is clean.

## Local image OCR

Install:

```bash
pip install 'long-gate[ocr]'
```

A local Tesseract executable must also already be installed on the machine.

Run:

```bash
longgate image-ocr-local scan.png
```

Long Gate returns only aggregate OCR/PII counts. OCR text is not printed and no remote OCR fallback is attempted.

## Scanned-PDF OCR

```bash
longgate pdf-ocr-local scan.pdf --max-pages 50
```

Pages are rendered locally through PDFium and OCR runs locally through Tesseract. The page cap is explicit to avoid silently processing an unbounded document.

The OCR text remains in local process memory for inspection and is not granted egress permission.

## Audio baseline

The current baseline supports local WAV metadata inspection:

```bash
longgate audio-inspect interview.wav
```

It reports channels, sample rate, frame count, and duration. It **does not claim to inspect or de-identify speech content**.

That means:
- `content_inspected: false`;
- `release_allowed: false`;
- audio remains network-blocked.

Future local speech-to-text can be added behind the same fail-closed boundary, but the present implementation does not pretend metadata inspection is content privacy.
