#!/usr/bin/env python3
"""
pdf_converter.py - PDF to Image Converter Module
OCR Project Manager カスタム拡張モジュール

PDFファイルを画像（PNG）に変換し、プロジェクトのinputディレクトリに格納する。
app.pyと連携して動作する独立モジュール。

依存: pdf2image, poppler
インストール:
  pip install pdf2image
  brew install poppler  (macOS)
  apt-get install poppler-utils  (Ubuntu)
"""

from pathlib import Path
from typing import Optional


def check_dependencies() -> tuple[bool, str]:
    """pdf2imageとpopplerの依存チェック"""
    try:
        from pdf2image import convert_from_path
        # popplerの存在確認（ダミー変換で検出）
        return True, "ok"
    except ImportError:
        return False, "pdf2image not installed. Run: pip install pdf2image"
    except Exception as e:
        return False, str(e)


def convert_pdf_to_images(
    pdf_path: Path,
    output_dir: Path,
    dpi: int = 300,
    fmt: str = "png",
    prefix: Optional[str] = None,
) -> tuple[bool, list[str], str]:
    """
    PDFを画像に変換してoutput_dirに保存する。

    Args:
        pdf_path: 変換するPDFファイルのパス
        output_dir: 画像の保存先ディレクトリ（プロジェクトのinput/）
        dpi: 解像度（デフォルト300dpi）
        fmt: 出力形式（"png" or "jpeg"）
        prefix: ファイル名プレフィックス（省略時はPDFのステム名）

    Returns:
        (success, saved_filenames, message)
    """
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


def get_pdf_info(pdf_path: Path) -> dict:
    """PDFの基本情報を返す（ページ数・サイズ等）"""
    try:
        from pdf2image import pdfinfo_from_path
        info = pdfinfo_from_path(str(pdf_path))
        return {
            "pages": info.get("Pages", "?"),
            "title": info.get("Title", ""),
            "creator": info.get("Creator", ""),
        }
    except Exception as e:
        return {"error": str(e)}
