#!/usr/bin/env python3
"""
app_extensions.py - OCR Project Manager 拡張モジュール
PDF変換・画像クロップ等の拡張ルートをここに追加していく。
app_v2.py からimportされることで、appインスタンスにルートが登録される。
"""

import tempfile
import threading
from pathlib import Path
from flask import request, jsonify
from app import app, get_project_dir, load_project_meta, save_project_meta
from pdf_converter import convert_pdf_to_images, check_dependencies, get_pdf_info
from image_cropper import crop_image

# PDF変換の進捗管理（OCR進捗と同じ仕組み）
pdf_progress = {}

PDF_SIZE_LIMIT = 1 * 1024 * 1024 * 1024  # 1GB


# ─── PDF依存チェック ──────────────────────────────────────────────────────────
@app.route("/api/pdf/check")
def pdf_check():
    ok, msg = check_dependencies()
    return jsonify({"available": ok, "message": msg})


# ─── PDFアップロード → 画像変換 → input/に格納 ────────────────────────────
@app.route("/api/projects/<project_name>/upload_pdf", methods=["POST"])
def upload_pdf(project_name):
    project_path = get_project_dir(project_name)
    if not project_path.exists():
        return jsonify({"error": "Project not found"}), 404

    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400

    file = request.files["file"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "PDFファイルのみ対応しています"}), 400

    # ファイルサイズチェック
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > PDF_SIZE_LIMIT:
        return jsonify({"error": f"ファイルサイズが上限（1GB）を超えています"}), 400

    dpi = int(request.form.get("dpi", 300))
    job_id = f"pdf_{project_name}_{file.filename}"
    pdf_progress[job_id] = {"status": "converting", "message": "変換中..."}

    # 一時ファイルに保存
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

            # page_orderに追記
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


# ─── PDF変換進捗確認 ──────────────────────────────────────────────────────────
@app.route("/api/pdf_progress/<path:job_id>")
def get_pdf_progress(job_id):
    return jsonify(pdf_progress.get(job_id, {"status": "unknown"}))


# ─── PDF情報取得（ページ数確認用） ────────────────────────────────────────────
@app.route("/api/pdf/info", methods=["POST"])
def pdf_info():
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files["file"]
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file.save(tmp.name)
        tmp_path = Path(tmp.name)
    try:
        info = get_pdf_info(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)
    return jsonify(info)


# ─── 画像クロップ ─────────────────────────────────────────────────────────────
@app.route("/api/projects/<project_name>/page/<filename>/crop", methods=["POST"])
def crop_page_image(project_name, filename):
    """
    画像の指定範囲をクロップして output/crop/<title>.png に保存し、
    OCR JSONにfigureブロックを追加する。
    """
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
    ok, saved_filename, msg = crop_image(input_path, crop_dir, x1, y1, x2, y2, title)

    if not ok:
        return jsonify({"error": msg}), 500

    return jsonify({
        "success": True,
        "filename": saved_filename,
        "title": title,
        "caption": caption,
        "message": msg,
    })
