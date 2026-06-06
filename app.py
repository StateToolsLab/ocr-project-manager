#!/usr/bin/env python3
"""OCR Project Manager - Local Flask App"""

import os
import sys
import json
import subprocess
import threading
import shutil
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_file

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Base directory for all projects
APP_DIR = Path(__file__).resolve().parent
PROJECTS_DIR = APP_DIR.parent / "OCR_Projects"
PROJECTS_DIR.mkdir(exist_ok=True)

# NDLOCR path
NDLOCR_PATH = Path(os.path.expanduser("~/ndlocr-lite"))
NDLOCR_GUI_MAIN = NDLOCR_PATH / "ndlocr-lite-gui" / "main.py"
NDLOCR_SRC = NDLOCR_PATH / "src"

# OCR progress tracking
ocr_progress = {}


def get_project_dir(project_name):
    return PROJECTS_DIR / project_name


def load_project_meta(project_path):
    meta_file = project_path / "meta.json"
    if meta_file.exists():
        with open(meta_file) as f:
            return json.load(f)
    return {}


def save_project_meta(project_path, meta):
    with open(project_path / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def find_ocr_json(output_dir, page_name):
    """NDLOCRはスペース区切りでファイル名を短縮する。完全一致→前方一致→imginfo検索の順で探す"""
    stem = Path(page_name).stem
    exact = output_dir / (stem + ".json")
    if exact.exists():
        return exact
    parts = stem.split(" ")
    for i in range(len(parts) - 1, 0, -1):
        candidate = " ".join(parts[:i]) + ".json"
        path = output_dir / candidate
        if path.exists():
            return path
    for json_file in output_dir.glob("*.json"):
        if json_file.name.endswith("_overlay.json"):
            continue
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("imginfo", {}).get("img_name") == page_name:
                return json_file
        except Exception:
            continue
    return None


def load_page_data(project_path, page_name):
    """Load OCR JSON and overlay (edits) for a page"""
    output_dir = project_path / "output"
    json_file = find_ocr_json(output_dir, page_name)
    if json_file is None:
        return None
    overlay_file = output_dir / (Path(page_name).stem + "_overlay.json")
    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)
    overlay = {}
    if overlay_file.exists():
        with open(overlay_file, encoding="utf-8") as f:
            overlay = json.load(f)

    # overlayの情報をブロックに埋め込む（IDベースで照合）
    # overlayキーがIDと一致する場合のみ適用
    blocks = data.get("contents", [[]])[0]
    for block in blocks:
        bid = str(block.get("id", ""))
        if bid in overlay:
            ov = overlay[bid]
            if "text" in ov:
                block["_text"] = ov["text"]
            if "checked" in ov:
                block["_checked"] = ov["checked"]
            if "confidence" in ov:
                block["_confidence"] = ov["confidence"]
            if "manual" in ov:
                block["manual"] = ov["manual"]

    return {"ocr": data, "overlay": overlay}


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    import os
    pdf_enabled = os.environ.get("PDF_ENABLED", "false").lower() == "true"
    return render_template("index.html", pdf_enabled=pdf_enabled)


@app.route("/api/projects", methods=["GET"])
def list_projects():
    projects = []
    if PROJECTS_DIR.exists():
        for p in sorted(PROJECTS_DIR.iterdir()):
            if not p.is_dir():
                continue
            if not (p / "meta.json").exists():
                continue
            meta = load_project_meta(p)
            if True:
                input_dir = p / "input"
                output_dir = p / "output"
                input_count = len(list(input_dir.glob("*.png")) + list(input_dir.glob("*.jpg")) + list(input_dir.glob("*.jpeg"))) if input_dir.exists() else 0
                output_count = len([f for f in output_dir.glob("*.json") if not f.name.endswith("_overlay.json")]) if output_dir.exists() else 0
                
                # Count checked blocks
                checked = 0
                total_blocks = 0
                if output_dir.exists():
                    for overlay_file in output_dir.glob("*_overlay.json"):
                        with open(overlay_file) as f:
                            ov = json.load(f)
                        for block_id, block_data in ov.items():
                            total_blocks += 1
                            if block_data.get("checked"):
                                checked += 1

                projects.append({
                    "name": p.name,
                    "created": meta.get("created", ""),
                    "description": meta.get("description", ""),
                    "input_count": input_count,
                    "output_count": output_count,
                    "checked": checked,
                    "total_blocks": total_blocks,
                    "page_order": meta.get("page_order", []),
                    "writing_direction": meta.get("writing_direction", "vertical"),
                })
    return jsonify(projects)


@app.route("/api/projects", methods=["POST"])
def create_project():
    data = request.json
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Project name required"}), 400

    project_path = get_project_dir(name)
    if project_path.exists():
        return jsonify({"error": "Project already exists"}), 400

    project_path.mkdir()
    (project_path / "input").mkdir()
    (project_path / "output").mkdir()

    meta = {
        "created": datetime.now().isoformat(),
        "description": data.get("description", ""),
        "page_order": [],
        "confidence_threshold": 0.9,
        "writing_direction": data.get("writing_direction", "vertical"),
    }
    save_project_meta(project_path, meta)
    return jsonify({"success": True, "name": name})


@app.route("/api/projects/<project_name>/edit", methods=["POST"])
def edit_project(project_name):
    project_path = get_project_dir(project_name)
    if not project_path.exists():
        return jsonify({"error": "Project not found"}), 404

    data = request.json
    new_name = data.get("name", "").strip()
    new_desc = data.get("description", "")
    new_writing_direction = data.get("writing_direction", None)

    # Update description
    meta = load_project_meta(project_path)
    meta["description"] = new_desc
    if new_writing_direction is not None:
        meta["writing_direction"] = new_writing_direction

    # Rename folder if name changed
    if new_name and new_name != project_name:
        new_path = get_project_dir(new_name)
        if new_path.exists():
            return jsonify({"error": "同名のプロジェクトが既に存在します"}), 400
        project_path.rename(new_path)
        save_project_meta(new_path, meta)
    else:
        save_project_meta(project_path, meta)

    return jsonify({"success": True, "name": new_name or project_name})


@app.route("/api/projects/<project_name>", methods=["DELETE"])
def delete_project(project_name):
    project_path = get_project_dir(project_name)
    if project_path.exists():
        shutil.rmtree(project_path)
    return jsonify({"success": True})


@app.route("/api/projects/<project_name>/pages", methods=["GET"])
def list_pages(project_name):
    project_path = get_project_dir(project_name)
    meta = load_project_meta(project_path)
    input_dir = project_path / "input"
    output_dir = project_path / "output"

    if not input_dir.exists():
        return jsonify([])

    # Collect all images
    images = []
    for ext in ["*.png", "*.jpg", "*.jpeg", "*.PNG", "*.JPG", "*.JPEG"]:
        images.extend(input_dir.glob(ext))

    # Sort by filename
    images = sorted(images, key=lambda x: x.name)

    # Apply saved order
    saved_order = meta.get("page_order", [])
    if saved_order:
        order_map = {name: i for i, name in enumerate(saved_order)}
        images = sorted(images, key=lambda x: order_map.get(x.name, 9999))

    pages = []
    for img in images:
        json_file = find_ocr_json(output_dir, img.name)
        overlay_file = output_dir / (img.stem + "_overlay.json")

        has_ocr = json_file is not None
        checked_count = 0
        total_count = 0

        if has_ocr:
            with open(json_file, encoding="utf-8") as f:
                ocr_data = json.load(f)
            blocks = ocr_data.get("contents", [[]])[0]
            total_count = len(blocks)

            if overlay_file.exists():
                with open(overlay_file, encoding="utf-8") as f:
                    overlay = json.load(f)
                checked_count = sum(1 for v in overlay.values() if v.get("checked"))

        pages.append({
            "name": img.name,
            "has_ocr": has_ocr,
            "checked_count": checked_count,
            "total_count": total_count,
        })

    return jsonify(pages)


@app.route("/api/projects/<project_name>/pages/order", methods=["POST"])
def save_page_order(project_name):
    project_path = get_project_dir(project_name)
    meta = load_project_meta(project_path)
    meta["page_order"] = request.json.get("order", [])
    save_project_meta(project_path, meta)
    return jsonify({"success": True})


@app.route("/api/projects/<project_name>/upload", methods=["POST"])
def upload_images(project_name):
    project_path = get_project_dir(project_name)
    input_dir = project_path / "input"
    input_dir.mkdir(exist_ok=True)

    files = request.files.getlist("files")
    saved = []
    for f in files:
        if f.filename:
            dest = input_dir / f.filename
            f.save(str(dest))
            saved.append(f.filename)

    return jsonify({"saved": saved})


@app.route("/api/projects/<project_name>/pages/<filename>", methods=["DELETE"])
def delete_page(project_name, filename):
    project_path = get_project_dir(project_name)
    input_file = project_path / "input" / filename
    output_dir = project_path / "output"
    stem = Path(filename).stem

    # 入力画像を削除
    if input_file.exists():
        input_file.unlink()

    # 関連するOCR出力ファイルを削除（JSON/TXT/XML/overlay）
    for pattern in [stem + ".json", stem + ".txt", stem + ".xml", stem + "_overlay.json"]:
        f = output_dir / pattern
        if f.exists():
            f.unlink()

    # NDLOCRの短縮名ファイルも削除
    json_file = find_ocr_json(output_dir, filename)
    if json_file and json_file.exists():
        base = json_file.stem
        for ext in [".json", ".txt", ".xml"]:
            f = output_dir / (base + ext)
            if f.exists():
                f.unlink()

    # page_orderからも削除
    meta = load_project_meta(project_path)
    order = meta.get("page_order", [])
    if filename in order:
        order.remove(filename)
        meta["page_order"] = order
        save_project_meta(project_path, meta)

    return jsonify({"success": True})


@app.route("/api/projects/<project_name>/image/<filename>")
def serve_image(project_name, filename):
    project_path = get_project_dir(project_name)
    image_path = project_path / "input" / filename
    if image_path.exists():
        return send_file(str(image_path))
    return "Not found", 404


def fix_image_orientation(input_file):
    """EXIFのOrientationタグに従って画像を回転補正し、補正済みの一時ファイルパスを返す。
    補正不要な場合はNoneを返す（元ファイルをそのまま使う）。"""
    try:
        from PIL import Image, ImageOps
        import tempfile
        img = Image.open(str(input_file))
        # ImageOps.exif_transposeが最も確実（Pillow 6.0.0+）
        img_fixed = ImageOps.exif_transpose(img)
        # 変換が発生したか確認（サイズが変わったかどうかで判断）
        if img_fixed is img:
            return None  # 変換なし
        suffix = Path(input_file).suffix or '.jpg'
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp.close()
        img_fixed.save(tmp.name, quality=95)
        return Path(tmp.name)
    except Exception:
        return None


def run_ocr_single(input_file, output_dir, job_id, simple_mode=False):
    """1枚OCR実行→即座に画像名でリネーム保存"""
    import tempfile, glob
    tmp_dir = Path(tempfile.mkdtemp())

    # EXIF回転補正（iPhoneなどで必要）
    corrected_file = fix_image_orientation(input_file)
    if corrected_file is None:
        # exif_transposeが効かない場合、EXIFを直接読んで強制補正
        try:
            from PIL import Image as _PIL_Image
            import tempfile as _tf
            _img = _PIL_Image.open(str(input_file))
            _exif = _img._getexif() or {}
            _orient = _exif.get(274, 1)  # 274 = Orientation tag
            _rotation_map = {3: 180, 6: 270, 8: 90}
            if _orient in _rotation_map:
                _img_rot = _img.rotate(_rotation_map[_orient], expand=True)
                _suffix = Path(input_file).suffix or '.jpg'
                _tmp = _tf.NamedTemporaryFile(suffix=_suffix, delete=False)
                _tmp.close()
                _img_rot.save(_tmp.name, quality=95)
                corrected_file = Path(_tmp.name)
        except Exception:
            pass
    ocr_source = corrected_file if corrected_file else input_file

    # NDLOCRは拡張子が小文字でないと画像を認識しない（JPG→jpg等）
    if ocr_source.suffix != ocr_source.suffix.lower():
        import tempfile as _tf2
        _suffix_lower = ocr_source.suffix.lower()
        _tmp2 = _tf2.NamedTemporaryFile(suffix=_suffix_lower, delete=False)
        _tmp2.close()
        import shutil as _shutil2
        _shutil2.copy2(str(ocr_source), _tmp2.name)
        # 古いcorrected_fileがあれば削除
        if corrected_file and corrected_file != ocr_source and corrected_file.exists():
            corrected_file.unlink(missing_ok=True)
        corrected_file = Path(_tmp2.name)
        ocr_source = corrected_file
    # NDLOCRは出力先フォルダが存在しないと失敗するため明示的に作成
    tmp_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(NDLOCR_SRC)
        cmd = [
            sys.executable, str(NDLOCR_SRC / "ocr.py"),
            "--sourceimg", str(ocr_source),
            "--output", str(tmp_dir),
        ]
        if simple_mode:
            cmd += ["--simple-mode", "true"]
        with open(os.devnull, 'r') as devnull_r, open(os.devnull, 'w') as devnull_w:
            proc = subprocess.Popen(
                cmd,
                stdin=devnull_r,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True,
                env=env,
            )
            try:
                stdout_data, stderr_data = proc.communicate(timeout=120)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()
                return False, "OCRタイムアウト"
        stdout_str = stdout_data.decode('utf-8', errors='replace')
        stderr_str = stderr_data.decode('utf-8', errors='replace')
        if proc.returncode != 0:
            return False, stderr_str[:300]
        # NDLOCRはエラーをstdoutに出してreturncodeを0にする場合がある
        if 'Images are not found' in stdout_str:
            return False, f'EXIF補正失敗またはNDLOCRが画像を認識できません: {stdout_str[:200]}'

        # tmp_dirに出力されたJSONを探す
        json_files = [f for f in tmp_dir.glob("*.json")]
        if not json_files:
            return False, f"JSONが出力されませんでした / returncode={proc.returncode} / stdout={stdout_str[:200]} / stderr={stderr_str[:200]}"

        # 画像のstemをそのまま使ったファイル名でoutput_dirに保存
        target_stem = input_file.stem
        for ext in [".json", ".txt", ".xml"]:
            src = tmp_dir / (json_files[0].stem + ext)
            if src.exists():
                dst = output_dir / (target_stem + ext)
                import shutil
                shutil.copy2(str(src), str(dst))
                # JSONの中のimginfoも正しいのでそのまま
        return True, "完了"
    except Exception as e:
        return False, str(e)
    finally:
        import shutil
        shutil.rmtree(str(tmp_dir), ignore_errors=True)
        # EXIF補正で作成した一時ファイルを削除
        if corrected_file and corrected_file.exists():
            corrected_file.unlink(missing_ok=True)


@app.route("/api/projects/<project_name>/ocr/<filename>", methods=["POST"])
def run_ocr(project_name, filename):
    project_path = get_project_dir(project_name)
    input_file = project_path / "input" / filename
    output_dir = project_path / "output"

    if not input_file.exists():
        return jsonify({"error": "Image not found"}), 404

    job_id = f"{project_name}/{filename}"
    ocr_progress[job_id] = {"status": "running", "message": "OCR処理中..."}

    def run():
        ok, msg = run_ocr_single(input_file, output_dir, job_id)
        if ok:
            ocr_progress[job_id] = {"status": "done", "message": "完了"}
        else:
            ocr_progress[job_id] = {"status": "error", "message": msg}

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"job_id": job_id})


@app.route("/api/projects/<project_name>/ocr_all", methods=["POST"])
def run_ocr_all(project_name):
    """1枚ずつ順番にOCR実行してリネーム保存（上書き防止）"""
    project_path = get_project_dir(project_name)
    input_dir = project_path / "input"
    output_dir = project_path / "output"

    # 未処理の画像のみ対象
    images = sorted(
        [f for ext in ["*.png","*.jpg","*.jpeg","*.PNG","*.JPG","*.JPEG"]
         for f in input_dir.glob(ext)],
        key=lambda x: x.name
    )
    images = [img for img in images if find_ocr_json(output_dir, img.name) is None]

    job_id = f"{project_name}/all"
    total = len(images)
    ocr_progress[job_id] = {"status": "running", "message": f"0/{total} 処理中..."}

    def run():
        for i, img in enumerate(images):
            ocr_progress[job_id] = {"status": "running", "message": f"{i}/{total} 処理中: {img.name}"}
            ok, msg = run_ocr_single(img, output_dir, job_id)
            if not ok:
                ocr_progress[job_id] = {"status": "error", "message": f"{img.name}: {msg}"}
                return
        ocr_progress[job_id] = {"status": "done", "message": f"{total}枚完了"}

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"job_id": job_id, "total": total})


@app.route("/api/ocr_progress/<path:job_id>")
def get_ocr_progress(job_id):
    return jsonify(ocr_progress.get(job_id, {"status": "unknown"}))


@app.route("/api/projects/<project_name>/page/<filename>")
def get_page_data(project_name, filename):
    project_path = get_project_dir(project_name)
    meta = load_project_meta(project_path)
    data = load_page_data(project_path, filename)
    if data is None:
        return jsonify({"error": "No OCR data"}), 404
    data["confidence_threshold"] = meta.get("confidence_threshold", 0.9)
    return jsonify(data)


@app.route("/api/projects/<project_name>/page/<filename>/delete_block", methods=["POST"])
def delete_block(project_name, filename):
    """指定ブロックをJSONから削除する"""
    project_path = get_project_dir(project_name)
    output_dir = project_path / "output"
    json_file = find_ocr_json(output_dir, filename)
    if json_file is None:
        return jsonify({"error": "OCR JSON not found"}), 404

    block_id = request.json.get("block_id")
    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)

    data["contents"][0] = [b for b in data["contents"][0] if b.get("id") != block_id]

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return jsonify({"success": True})


@app.route("/api/projects/<project_name>/page/<filename>/reorder", methods=["POST"])
def reorder_blocks(project_name, filename):
    """ブロックの順序とIDを振り直したものをJSONに保存する"""
    project_path = get_project_dir(project_name)
    output_dir = project_path / "output"
    json_file = find_ocr_json(output_dir, filename)
    if json_file is None:
        return jsonify({"error": "OCR JSON not found"}), 404

    new_blocks = request.json.get("blocks")
    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)

    if new_blocks is not None:
        data["contents"][0] = new_blocks
    
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return jsonify({"success": True})


@app.route("/api/projects/<project_name>/page/<filename>/ocr_patch", methods=["POST"])
def patch_ocr(project_name, filename):
    """手動追加ブロックをJSONに書き込む"""
    project_path = get_project_dir(project_name)
    output_dir = project_path / "output"
    json_file = find_ocr_json(output_dir, filename)
    if json_file is None:
        return jsonify({"error": "OCR JSON not found"}), 404

    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)

    new_block = request.json.get("block")
    if new_block:
        if not data.get("contents"):
            data["contents"] = [[]]
        # 重複IDチェック
        existing_ids = {b.get("id") for b in data["contents"][0]}
        if new_block.get("id") not in existing_ids:
            data["contents"][0].append(new_block)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return jsonify({"success": True})


@app.route("/api/projects/<project_name>/page/<filename>/overlay", methods=["POST"])
def save_overlay(project_name, filename):
    project_path = get_project_dir(project_name)
    output_dir = project_path / "output"
    overlay_file = output_dir / (Path(filename).stem + "_overlay.json")

    overlay_data = request.json
    with open(overlay_file, "w", encoding="utf-8") as f:
        json.dump(overlay_data, f, ensure_ascii=False, indent=2)

    return jsonify({"success": True})


@app.route("/api/projects/<project_name>/settings", methods=["POST"])
def save_settings(project_name):
    project_path = get_project_dir(project_name)
    meta = load_project_meta(project_path)
    data = request.json
    if "confidence_threshold" in data:
        meta["confidence_threshold"] = float(data["confidence_threshold"])
    save_project_meta(project_path, meta)
    return jsonify({"success": True})


@app.route("/api/projects/<project_name>/export", methods=["POST"])
def export_project(project_name):
    project_path = get_project_dir(project_name)
    meta = load_project_meta(project_path)
    output_dir = project_path / "output"
    input_dir = project_path / "input"

    data = request.json
    fmt = data.get("format", "txt")
    pages_order = data.get("pages", [])
    separator_template = data.get("separator", None)  # None = 区切りなし
    para_separator = data.get("para_separator", None)   # None = 段落区切り無効, '' = 空行
    use_indent = data.get("indent", False)  # 段落先頭に一字下げ（全角スペース）を付与

    # If no order given, use saved order or filename sort
    if not pages_order:
        saved_order = meta.get("page_order", [])
        if saved_order:
            pages_order = saved_order
        else:
            images = sorted(input_dir.glob("*.png")) + sorted(input_dir.glob("*.jpg"))
            pages_order = [img.name for img in sorted(images, key=lambda x: x.name)]

    # ページごとにブロックを収集
    pages_blocks = []
    for page_idx, page_name in enumerate(pages_order):
        json_file = find_ocr_json(output_dir, page_name)
        overlay_file = output_dir / (Path(page_name).stem + "_overlay.json")

        if json_file is None:
            continue

        with open(json_file, encoding="utf-8") as f:
            ocr_data = json.load(f)

        overlay = {}
        if overlay_file.exists():
            with open(overlay_file, encoding="utf-8") as f:
                overlay = json.load(f)

        blocks = ocr_data.get("contents", [[]])[0]
        page_texts = []
        for block in blocks:
            block_id = str(block.get("id", ""))
            text = overlay.get(block_id, {}).get("text") or block.get("text", "")
            if text.strip():
                page_texts.append({
                    "page": page_name,
                    "page_num": page_idx + 1,
                    "id": block.get("id"),
                    "text": text,
                    "confidence": block.get("confidence", 1.0),
                    "boundingBox": block.get("boundingBox"),
                })
        pages_blocks.append((page_name, page_idx + 1, page_texts))

    if fmt == "txt":
        parts = []
        for page_name, page_num, page_block_list in pages_blocks:
            if separator_template:
                sep = separator_template.replace("{n}", str(page_num))
                parts.append(sep)
            # 段落区切り対応
            page_lines = []
            overlay_file = output_dir / (Path(page_name).stem + "_overlay.json")
            overlay = {}
            if overlay_file.exists():
                with open(overlay_file, encoding="utf-8") as f:
                    overlay = json.load(f)
            for b in page_block_list:
                bid = str(b.get("id", ""))
                ov = overlay.get(bid, {})
                if para_separator is not None and ov.get("paragraph_break") and page_lines:
                    page_lines.append(para_separator if para_separator else "")
                text = b["text"]
                # 一字下げ：¶ブロックの先頭に全角スペースを付与（まだない場合のみ）
                if use_indent and ov.get("paragraph_break") and not text.startswith("\u3000"):
                    text = "\u3000" + text
                page_lines.append(text)
            parts.append("\n".join(page_lines))
        content = "\n".join(parts)
        export_file = project_path / f"{project_name}_export.txt"
        with open(export_file, "w", encoding="utf-8") as f:
            f.write(content)
        return send_file(str(export_file), as_attachment=True)

    elif fmt == "json":
        # pages_blocksをフラットなリストに変換
        combined_blocks = []
        for page_name, page_num, blocks in pages_blocks:
            for b in blocks:
                combined_blocks.append(b)
        export_file = project_path / f"{project_name}_export.json"
        with open(export_file, "w", encoding="utf-8") as f:
            json.dump(combined_blocks, f, ensure_ascii=False, indent=2)
        return send_file(str(export_file), as_attachment=True)

    return jsonify({"error": "Unknown format"}), 400




@app.route("/api/projects/<project_name>/page/<filename>/reocr_block", methods=["POST"])
def reocr_block(project_name, filename):
    """選択ブロックのboundingBoxでクロップして再OCR実行"""
    import tempfile
    from PIL import Image
    project_path = get_project_dir(project_name)
    input_path = project_path / "input" / filename
    if not input_path.exists():
        return jsonify({"error": "Image not found"}), 404

    data = request.json
    bb = data.get("boundingBox")
    if not bb:
        return jsonify({"error": "boundingBox required"}), 400

    xs = [p[0] for p in bb]
    ys = [p[1] for p in bb]
    x1, y1 = int(min(xs)), int(min(ys))
    x2, y2 = int(max(xs)), int(max(ys))

    tmp_dir = Path(tempfile.mkdtemp())
    try:
        img = Image.open(str(input_path))
        crop = img.crop((x1, y1, x2, y2))
        crop_path = tmp_dir / "reocr_crop.png"
        crop.save(str(crop_path))

        tmp_out = tmp_dir / "out"
        tmp_out.mkdir()
        simple_mode = data.get("simple_mode", False)
        ok, msg = run_ocr_single(crop_path, tmp_out, "reocr", simple_mode=simple_mode)
        if not ok:
            return jsonify({"error": msg}), 500

        json_files = list(tmp_out.glob("*.json"))
        if not json_files:
            return jsonify({"error": "OCR結果が取得できませんでした"}), 500

        with open(json_files[0], encoding="utf-8") as f:
            result = json.load(f)

        blocks = result.get("contents", [[]])[0]
        text = "\n".join(b.get("text", "") for b in blocks if b.get("text", "").strip())
        return jsonify({"text": text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        import shutil as _sh
        _sh.rmtree(str(tmp_dir), ignore_errors=True)



# ── 校正辞書 ──────────────────────────────────────────────────────────────────
def load_dict(dict_file):
    if dict_file.exists():
        with open(dict_file, encoding="utf-8") as f:
            return json.load(f)
    return {"rules": []}

def save_dict(dict_file, data):
    with open(dict_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def new_rule_id(rules):
    if not rules:
        return "r1"
    nums = [int(r["id"][1:]) for r in rules if r["id"].startswith("r")]
    return f"r{max(nums)+1}" if nums else "r1"

@app.route("/api/projects/<project_name>/correction_dict", methods=["GET"])
def get_project_dict(project_name):
    dict_file = get_project_dir(project_name) / "correction_dict.json"
    return jsonify(load_dict(dict_file))

@app.route("/api/projects/<project_name>/correction_dict", methods=["POST"])
def add_project_rule(project_name):
    data = request.json
    dict_file = get_project_dir(project_name) / "correction_dict.json"
    d = load_dict(dict_file)
    rule = {
        "id": new_rule_id(d["rules"]),
        "from": data.get("from", ""),
        "to": data.get("to", ""),
        "type": data.get("type", "char"),
        "note": data.get("note", ""),
        "created": datetime.now().isoformat(),
    }
    d["rules"].append(rule)
    save_dict(dict_file, d)
    return jsonify({"success": True, "rule": rule})

@app.route("/api/projects/<project_name>/correction_dict/<rule_id>", methods=["DELETE"])
def delete_project_rule(project_name, rule_id):
    dict_file = get_project_dir(project_name) / "correction_dict.json"
    d = load_dict(dict_file)
    d["rules"] = [r for r in d["rules"] if r["id"] != rule_id]
    save_dict(dict_file, d)
    return jsonify({"success": True})

@app.route("/api/projects/<project_name>/correction_dict/<rule_id>", methods=["PUT"])
def update_project_rule(project_name, rule_id):
    data = request.json
    dict_file = get_project_dir(project_name) / "correction_dict.json"
    d = load_dict(dict_file)
    for r in d["rules"]:
        if r["id"] == rule_id:
            r.update({k: v for k, v in data.items() if k != "id"})
    save_dict(dict_file, d)
    return jsonify({"success": True})

@app.route("/api/projects/<project_name>/apply_correction", methods=["POST"])
def apply_correction(project_name):
    project_path = get_project_dir(project_name)
    input_dir = project_path / "input"
    output_dir = project_path / "output"

    d = load_dict(project_path / "correction_dict.json")
    rules = [{**r, "source": "project"} for r in d["rules"]]
    if not rules:
        return jsonify({"success": True, "applied": 0})

    applied = 0
    images = [f for ext in ["*.png","*.jpg","*.jpeg","*.PNG","*.JPG","*.JPEG"]
              for f in input_dir.glob(ext)]

    for img in images:
        json_file = find_ocr_json(output_dir, img.name)
        if not json_file:
            continue
        overlay_file = output_dir / (img.stem + "_overlay.json")
        with open(json_file, encoding="utf-8") as f:
            ocr_data = json.load(f)
        overlay = {}
        if overlay_file.exists():
            with open(overlay_file, encoding="utf-8") as f:
                overlay = json.load(f)

        blocks = ocr_data.get("contents", [[]])[0]
        for block in blocks:
            bid = str(block.get("id", ""))
            ov = overlay.get(bid, {})
            if ov.get("checked"):
                continue
            text = ov.get("text") or block.get("text", "")
            original = text
            matched_rule = None
            for rule in rules:
                if rule["from"] in text:
                    text = text.replace(rule["from"], rule["to"])
                    matched_rule = rule
            if matched_rule and text != original:
                overlay.setdefault(bid, {})
                overlay[bid]["text"] = text
                overlay[bid]["original_ocr_text"] = original
                overlay[bid]["correction_applied"] = True
                overlay[bid]["correction_rule_id"] = matched_rule["id"]
                applied += 1

        with open(overlay_file, "w", encoding="utf-8") as f:
            json.dump(overlay, f, ensure_ascii=False, indent=2)

    return jsonify({"success": True, "applied": applied})

@app.route("/api/projects/<project_name>/suggestions/analyze", methods=["POST"])
def analyze_suggestions(project_name):
    """overlay内の編集済みテキストとOCR原文の差分から候補を生成"""
    import difflib
    from collections import Counter
    project_path = get_project_dir(project_name)
    output_dir = project_path / "output"
    threshold = request.json.get("threshold", 2)

    pattern_counter = Counter()
    for overlay_file in output_dir.glob("*_overlay.json"):
        stem = overlay_file.stem.replace("_overlay", "")
        json_file = find_ocr_json(output_dir, stem + ".png") or find_ocr_json(output_dir, stem + ".jpg")
        if not json_file:
            continue
        with open(json_file, encoding="utf-8") as f:
            ocr_data = json.load(f)
        with open(overlay_file, encoding="utf-8") as f:
            overlay = json.load(f)
        blocks = ocr_data.get("contents", [[]])[0]
        for block in blocks:
            bid = str(block.get("id", ""))
            ov = overlay.get(bid, {})
            orig = block.get("text", "").strip()
            corr = ov.get("text", "").strip()
            if orig and corr and orig != corr:
                matcher = difflib.SequenceMatcher(None, orig, corr)
                for op, i1, i2, j1, j2 in matcher.get_opcodes():
                    if op != "equal":
                        from_str = orig[i1:i2]
                        to_str = corr[j1:j2]
                        if from_str and to_str:
                            pattern_counter[(from_str, to_str)] += 1

    now = datetime.now().isoformat()
    result = [
        {
            "id": str(int(datetime.now().timestamp() * 1000) + i),
            "from": k[0],
            "to": k[1],
            "count": v,
            "status": "pending",
            "first_seen": now,
            "last_seen": now,
        }
        for i, (k, v) in enumerate(pattern_counter.most_common(20))
        if v >= threshold
    ]
    return jsonify(result)



# ── PDF変換 ───────────────────────────────────────────────────────────────────
pdf_progress = {}
PDF_SIZE_LIMIT = 1 * 1024 * 1024 * 1024  # 1GB

def convert_pdf_to_images(pdf_path, output_dir, dpi=300, fmt="png", prefix=None):
    try:
        from pdf2image import convert_from_path
    except ImportError:
        return False, [], "pdf2image not installed. Run: pip install pdf2image"
    if not pdf_path.exists():
        return False, [], f"PDF not found: {pdf_path}"
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = prefix or pdf_path.stem
    try:
        pages = convert_from_path(str(pdf_path), dpi=dpi)
    except Exception as e:
        return False, [], f"PDF conversion failed: {e}"
    saved = []
    digits = len(str(len(pages)))
    for i, page in enumerate(pages, start=1):
        filename = f"{prefix}_{str(i).zfill(digits)}.{fmt}"
        out_path = output_dir / filename
        page.save(str(out_path), fmt.upper() if fmt != "jpg" else "JPEG")
        saved.append(filename)
    return True, saved, f"{len(saved)}ページを変換しました"

@app.route("/api/pdf/check")
def pdf_check():
    try:
        from pdf2image import convert_from_path
        return jsonify({"available": True, "message": "ok"})
    except ImportError:
        return jsonify({"available": False, "message": "pdf2image not installed"})

@app.route("/api/projects/<project_name>/upload_pdf", methods=["POST"])
def upload_pdf(project_name):
    import tempfile
    project_path = get_project_dir(project_name)
    if not project_path.exists():
        return jsonify({"error": "Project not found"}), 404
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files["file"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "PDFファイルのみ対応しています"}), 400
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > PDF_SIZE_LIMIT:
        return jsonify({"error": "ファイルサイズが上限（1GB）を超えています"}), 400
    dpi = int(request.form.get("dpi", 300))
    job_id = f"pdf_{project_name}_{file.filename}"
    pdf_progress[job_id] = {"status": "converting", "message": "変換中..."}
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file.save(tmp.name)
        tmp_path = Path(tmp.name)
    def run():
        try:
            prefix = Path(file.filename).stem
            input_dir = project_path / "input"
            ok, saved, msg = convert_pdf_to_images(tmp_path, input_dir, dpi=dpi, prefix=prefix)
            if not ok:
                pdf_progress[job_id] = {"status": "error", "message": msg}
                return
            meta = load_project_meta(project_path)
            existing = set(meta.get("page_order", []))
            for name in saved:
                if name not in existing:
                    meta.setdefault("page_order", []).append(name)
            save_project_meta(project_path, meta)
            pdf_progress[job_id] = {"status": "done", "message": msg, "files": saved}
        finally:
            tmp_path.unlink(missing_ok=True)
    threading.Thread(target=run, daemon=True).start()
    return jsonify({"job_id": job_id})

@app.route("/api/pdf_progress/<path:job_id>")
def get_pdf_progress(job_id):
    return jsonify(pdf_progress.get(job_id, {"status": "unknown"}))

@app.route("/api/pdf/info", methods=["POST"])
def pdf_info():
    import tempfile
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files["file"]
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file.save(tmp.name)
        tmp_path = Path(tmp.name)
    try:
        from pdf2image import pdfinfo_from_path
        info = pdfinfo_from_path(str(tmp_path))
        return jsonify({
            "pages": info.get("Pages", "?"),
            "title": info.get("Title", ""),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        tmp_path.unlink(missing_ok=True)



# ── 図表クロップ ──────────────────────────────────────────────────────────────
@app.route("/api/projects/<project_name>/page/<filename>/crop", methods=["POST"])
def crop_page_image(project_name, filename):
    from PIL import Image, ImageOps
    project_path = get_project_dir(project_name)
    input_path = project_path / "input" / filename
    if not input_path.exists():
        return jsonify({"error": "Image not found"}), 404

    data = request.json
    x1 = float(data.get("x1", 0))
    y1 = float(data.get("y1", 0))
    x2 = float(data.get("x2", 0))
    y2 = float(data.get("y2", 0))
    title = data.get("title", "図").strip()
    caption = data.get("caption", "").strip()

    if not title:
        return jsonify({"error": "タイトルを入力してください"}), 400

    crop_dir = project_path / "output" / "crop"
    crop_dir.mkdir(parents=True, exist_ok=True)

    safe_title = "".join(c for c in title if c not in r'\/:*?"<>|').strip() or "crop"
    filename_out = f"{safe_title}.png"
    out_path = crop_dir / filename_out
    counter = 1
    while out_path.exists():
        filename_out = f"{safe_title}_{counter}.png"
        out_path = crop_dir / filename_out
        counter += 1

    try:
        img = Image.open(str(input_path))
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass
        box = (int(min(x1,x2)), int(min(y1,y2)), int(max(x1,x2)), int(max(y1,y2)))
        img.crop(box).save(str(out_path), "PNG")
        return jsonify({
            "success": True,
            "filename": filename_out,
            "title": title,
            "caption": caption,
            "message": f"クロップ画像を保存しました: {filename_out}",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    import webbrowser
    print("OCR Project Manager 起動中...")
    print(f"プロジェクトフォルダ: {PROJECTS_DIR}")
    threading.Timer(1.0, lambda: webbrowser.open("http://localhost:5049")).start()
    app.run(host="127.0.0.1", port=5049, debug=False)
