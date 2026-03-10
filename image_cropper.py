#!/usr/bin/env python3
"""
image_cropper.py - Image Crop Module
OCR Project Manager 拡張モジュール

画像の指定範囲をクロップして output/crop/ に保存する。
app_extensions.py から呼び出される。

依存: Pillow
インストール: pip install Pillow
"""

from pathlib import Path
from typing import Optional


def check_dependencies() -> tuple[bool, str]:
    """Pillowの依存チェック"""
    try:
        from PIL import Image
        return True, "ok"
    except ImportError:
        return False, "Pillow not installed. Run: pip install Pillow"


def crop_image(
    input_path: Path,
    output_dir: Path,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    title: str,
    fmt: str = "png",
) -> tuple[bool, str, str]:
    """
    画像の指定範囲をクロップして保存する。

    Args:
        input_path: 元画像のパス
        output_dir: 保存先ディレクトリ（output/crop/）
        x1, y1, x2, y2: クロップ範囲（画像座標系のピクセル値）
        title: 保存ファイル名（拡張子なし）
        fmt: 出力形式（"png" or "jpeg"）

    Returns:
        (success, saved_filename, message)
    """
    try:
        from PIL import Image
    except ImportError:
        return False, "", "Pillow not installed. Run: pip install Pillow"

    if not input_path.exists():
        return False, "", f"Image not found: {input_path}"

    output_dir.mkdir(parents=True, exist_ok=True)

    # ファイル名のサニタイズ（パス区切り文字等を除去）
    safe_title = "".join(c for c in title if c not in r'\/:*?"<>|').strip()
    if not safe_title:
        safe_title = "crop"

    filename = f"{safe_title}.{fmt}"
    out_path = output_dir / filename

    # 重複時は連番を付与
    counter = 1
    while out_path.exists():
        filename = f"{safe_title}_{counter}.{fmt}"
        out_path = output_dir / filename
        counter += 1

    try:
        img = Image.open(str(input_path))

        # EXIF回転補正
        try:
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # 座標をint変換してクロップ
        box = (int(min(x1, x2)), int(min(y1, y2)), int(max(x1, x2)), int(max(y1, y2)))
        cropped = img.crop(box)
        save_fmt = "JPEG" if fmt in ("jpg", "jpeg") else "PNG"
        cropped.save(str(out_path), save_fmt)

        return True, filename, f"クロップ画像を保存しました: {filename}"

    except Exception as e:
        return False, "", f"クロップ失敗: {e}"
