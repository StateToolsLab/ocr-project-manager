# OCR Project Manager

*日本語版READMEは [README.md](README.md) をご覧ください。*

A local browser-based tool for managing OCR workflows powered by NDLOCR — the OCR engine developed by the National Diet Library of Japan.

Covers everything from image upload, OCR execution, result verification and editing, to final text export — all in one UI.

**UI supports Japanese and English** (toggle in the top-right corner).

---

## Features

### Project Management
- Auto-generates folder structure per project
- Edit project name and description
- Delete projects

### Image Management
- Drag & drop image upload (multiple files)
- Auto-sort by filename on upload
- Drag-and-drop page reordering
- Delete individual pages

### OCR Execution
- Single-page OCR
- Batch OCR (unprocessed pages only)
- Safe output management that prevents filename conflicts

### Verification & Editing
- Confidence score display with adjustable threshold
- Visual overlay on images: orange = review required, green = confirmed
- Adjustable overlay opacity slider
- Block-level text editing
- Confirmed flag per block (sets confidence to 1.00)
- ¶ button to mark paragraph breaks at the block level
- Drag-and-drop block reordering
- Direct input of target position number for quick block repositioning
- Auto-renumbering of block IDs after reorder or delete
- Draw a region on the image to manually add a text block with custom text
- Delete individual blocks
- Bulk actions: Check All / Check Above Threshold / Delete All

### Text Preview Panel
- Displays all block text for the current page combined at the bottom of the screen
- One-click copy to clipboard
- Reload button to refresh after block edits

### Export
- Page range selection (choose start and end page)
- Page separator insertion (use `{n}` to embed page number)
- Paragraph break reflection (inserts separator before blocks marked with ¶)
- TXT format (plain text)
- JSON format (with coordinates and confidence scores)
- Preview before export, with a Copy button to grab text directly without saving a file

---

## Requirements

- macOS / Windows / Linux
- Python 3.8+
- [NDLOCR-Lite](https://github.com/ndl-lab/ndlocr-lite) (required, install separately)

---

## Installation

### 1. Install NDLOCR-Lite

```bash
git clone https://github.com/ndl-lab/ndlocr-lite
cd ndlocr-lite/ndlocr-lite-gui
pip3 install -r ../requirements.txt
```

Verify installation:

```bash
PYTHONPATH=~/ndlocr-lite/src python3 ~/ndlocr-lite/ndlocr-lite-gui/main.py
```

### 2. Install OCR Project Manager

```bash
git clone https://github.com/StateToolsLab/ocr-project-manager.git ~/ocr-project-manager
pip3 install flask
```

### 3. Set execute permission (Mac)

```bash
chmod +x ~/ocr-project-manager/OCR_Project_Manager.command
```

### 4. Create desktop shortcut (Mac)

```bash
ln -s ~/ocr-project-manager/OCR_Project_Manager.command ~/Desktop/OCR_Project_Manager.command
```

---

## Usage

Double-click `OCR_Project_Manager.command` on the desktop.

Your browser will automatically open `http://localhost:5050`.

On first launch, macOS may show a security warning. Use **right-click → Open** to bypass it.

---

## Data Storage

Project data is stored under `~/OCR_Projects/`:

```
~/OCR_Projects/
└── project-name/
    ├── input/       # Source images
    ├── output/      # OCR result JSON, edit data
    └── meta.json    # Project settings
```

---

## Credits

This tool uses [NDLOCR-Lite](https://github.com/ndl-lab/ndlocr-lite) by the National Diet Library of Japan.  
License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
