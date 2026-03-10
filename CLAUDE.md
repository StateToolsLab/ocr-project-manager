# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

**Standard launch (launcher UI):**
```bash
python3 start.py
# Opens http://localhost:5051 — choose v1 or v2 from the browser UI
```

**Direct launch — v1 (image OCR only):**
```bash
python3 app.py
# Opens http://localhost:5050
```

**Direct launch — v2 (adds PDF conversion + image crop):**
```bash
python3 app_v2.py
# Opens http://localhost:5050
```

**Install dependencies:**
```bash
pip3 install flask           # required
pip3 install Pillow          # required for EXIF correction and image crop
pip3 install pdf2image       # optional, for PDF support (v2)
brew install poppler         # optional, required by pdf2image (macOS)
```

NDLOCR-Lite must be installed separately at `~/ndlocr-lite/`. OCR calls invoke `~/ndlocr-lite/src/ocr.py` via subprocess.

## Architecture

The app is a local Flask server + single-page HTML frontend (`templates/index.html`). All state is stored as files under `~/OCR_Projects/`.

### File Layout (runtime data)
```
~/OCR_Projects/<project-name>/
├── input/          # source images (PNG/JPG/JPEG)
├── output/         # NDLOCR JSON results + edit overlays
│   ├── <stem>.json         # NDLOCR output
│   ├── <stem>_overlay.json # user edits (text, checked flag, paragraph_break)
│   └── crop/               # cropped image regions (v2)
└── meta.json       # project settings (page_order, confidence_threshold, etc.)
```

### Module Structure

| File | Role |
|---|---|
| `app.py` | Core Flask app. All project/page/OCR routes. Runs on port 5050. |
| `app_v2.py` | v2 entry point. Sets `PDF_ENABLED=true` env var, imports `app` + `app_extensions`. |
| `app_extensions.py` | Registers additional routes on `app`: PDF upload/conversion, image crop. |
| `pdf_converter.py` | Standalone module: `convert_pdf_to_images()`, `get_pdf_info()`. Depends on pdf2image + poppler. |
| `image_cropper.py` | Standalone module: `crop_image()`. Depends on Pillow. |
| `start.py` | Launcher UI on port 5051. Checks optional deps, lets user pick v1/v2, spawns `app.py` or `app_v2.py`. |
| `templates/index.html` | Full frontend SPA (vanilla JS, no build step). |

### Key Design Points

**OCR JSON lookup (`find_ocr_json`):** NDLOCR may shorten filenames (space-separated truncation). The lookup tries exact match → prefix match → scanning `imginfo.img_name` in JSON files. Always use this function when locating OCR output for a page.

**Overlay system:** User edits are never written back into NDLOCR's JSON. Instead, `<stem>_overlay.json` stores a dict keyed by block ID with `{text, checked, confidence, paragraph_break}`. On read, overlays are merged into the block list in memory.

**OCR execution:** Runs in a daemon thread. Progress is tracked in the in-memory `ocr_progress` dict (`{job_id: {status, message}}`). NDLOCR is invoked via subprocess pointing at `~/ndlocr-lite/src/ocr.py`. EXIF orientation correction and uppercase-extension normalization happen before passing images to NDLOCR.

**v2 extension pattern:** `app_extensions.py` imports `app` from `app.py` and registers routes directly on it. `app_v2.py` just imports both modules and runs the same `app` instance. New extensions should follow this same import pattern.

**PDF_ENABLED flag:** The frontend checks `pdf_enabled` (passed via `render_template`) to show/hide PDF upload UI. This is set via the `PDF_ENABLED` environment variable, only enabled in v2.

**No tests, no build step.** The frontend is plain HTML/CSS/JS served by Flask's `render_template`. Changes to `templates/index.html` take effect immediately (auto-reload is on in dev; in production `TEMPLATES_AUTO_RELOAD=True` is set explicitly).
