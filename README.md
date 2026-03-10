# OCR Project Manager

*日本語は下にあります / Japanese follows below.*

A workflow manager for [NDLOCR-Lite](https://github.com/ndl-lab/ndlocr-lite) — the OCR engine developed by the National Diet Library of Japan.

Upload scanned pages, run OCR, review and correct results block by block, and export clean text — all in your browser, all offline.

**UI supports Japanese and English** (toggle in the top-right corner).

---

![OCR Project Manager](docs/screenshot_main.png)

![Export modal](docs/screenshot_export.png)

*Sample document: 「モテツボ 真面目系男子の恋愛解体新書」（キマイラ著、セルバ出版、2024）*

---

## What's New in v2

- **PDF import** — upload a PDF and it is automatically converted to per-page images
- **Image crop** — drag a region on any page to save a cropped image to `output/crop/`
- **Smart launcher** — `start.py` checks v2 dependencies on startup; falls back to the stable v1 automatically if any are missing

---

## Features

### Project Management
- Auto-generates folder structure per project
- Edit project name and description
- Delete projects

### Image Management
- Drag & drop image upload (PNG / JPG, multiple files)
- **PDF upload with automatic page conversion** *(v2)*
- Auto-sort by filename on upload
- Drag-and-drop page reordering
- Delete individual pages

### OCR Execution
- Single-page OCR
- Batch OCR (unprocessed pages only)
- Safe output management that prevents filename conflicts

### Verification & Editing
- Confidence score display with adjustable threshold
- Visual overlay on images: orange = review required, green = confirmed, blue = selected
- Adjustable overlay opacity slider
- Block-level text editing
- Confirmed flag per block (sets confidence to 1.00)
- ¶ button to mark paragraph breaks at the block level
- Drag-and-drop block reordering
- Direct input of target position number for quick block repositioning
- Auto-renumbering of block IDs after reorder or delete
- Draw a region on the image to manually add a text block with custom text
- **Image crop to file** *(v2)* — save any region as a standalone image
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

| Requirement | Version | Note |
|---|---|---|
| Python | 3.8+ | |
| Flask | 2.3+ | |
| [NDLOCR-Lite](https://github.com/ndl-lab/ndlocr-lite) | latest | Install separately |
| Pillow | any | v2 — image crop & EXIF correction |
| pdf2image | any | v2 — PDF import |
| poppler | any | v2 — PDF import (`brew install poppler` on Mac) |

Pillow, pdf2image, and poppler are **optional**. If any are missing, the launcher opens a setup UI and starts v1 instead.

---

## Installation

### 1. Install NDLOCR-Lite

```bash
git clone https://github.com/ndl-lab/ndlocr-lite
cd ndlocr-lite/ndlocr-lite-gui
pip3 install -r ../requirements.txt
```

Verify:

```bash
PYTHONPATH=~/ndlocr-lite/src python3 ~/ndlocr-lite/ndlocr-lite-gui/main.py
```

### 2. Install OCR Project Manager

```bash
git clone https://github.com/StateToolsLab/ocr-project-manager.git ~/ocr-project-manager
cd ~/ocr-project-manager
pip3 install flask
```

For v2 features (optional):

```bash
pip3 install Pillow pdf2image
brew install poppler   # Mac
# sudo apt install poppler-utils   # Linux
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

The launcher checks your environment and opens the app automatically:

- **All v2 dependencies found** → v2 starts directly at `http://localhost:5050`
- **Any dependency missing** → a setup UI opens at `http://localhost:5051`, where you can install missing packages or start v1 instead

On first launch, macOS may show a security warning. Use **right-click → Open** to bypass it.

---

## Data Storage

```
~/OCR_Projects/
└── project-name/
    ├── input/         # Source images
    ├── output/
    │   ├── *.json     # OCR results
    │   ├── *_overlay.json  # Edit data
    │   └── crop/      # Cropped images (v2)
    └── meta.json      # Project settings
```

---

## Changelog

### v2 (2026-03)
- PDF import with automatic page-by-page conversion
- Image crop — save any page region as a standalone file
- Smart launcher with v1 fallback
- Blue highlight for selected block in overlay
- Bug fix: overlay rect turning black after block reorder or selection change

### v1
- Initial release

---

## Credits

This tool uses [NDLOCR-Lite](https://github.com/ndl-lab/ndlocr-lite) by the National Diet Library of Japan.  
License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

---
---

# OCR Project Manager（日本語）

[NDLOCR-Lite](https://github.com/ndl-lab/ndlocr-lite)（国立国会図書館）を使ったOCR作業を、ローカルブラウザ上で一元管理できるツールです。

画像のアップロード、OCR実行、結果の検証・編集、テキストの統合出力までを一つのUIで完結できます。インターネット接続不要、すべてローカルで動作します。

**UIは日本語・英語に対応しています（画面右上で切り替え）。**

---

## v2 新機能

- **PDFインポート** — PDFをアップロードするとページごとに画像へ自動変換
- **画像クロップ** — ページ上をドラッグして指定範囲を `output/crop/` に保存
- **スマートランチャー** — 起動時にv2依存ライブラリを自動チェック、不足時はv1で起動

---

## 主な機能

### プロジェクト管理
- プロジェクト単位でフォルダを自動生成・管理
- プロジェクト名・説明の編集
- プロジェクト単位での削除

### 画像管理
- 画像のドラッグ&ドロップアップロード（PNG / JPG、複数可）
- **PDFアップロード → ページ画像への自動変換** *(v2)*
- アップロード時にファイル名順で自動ソート
- ページリストでのドラッグによる並び替え
- ページ単位での削除

### OCR実行
- 1ページずつのOCR実行
- 一括OCR実行（未処理ページのみ対象）
- ファイル名衝突を防ぐ安全な出力管理

### 結果の検証・編集
- OCR結果の信頼度スコア表示・閾値設定
- 閾値以下のブロックをオレンジ、確認済みを緑、選択中を青で画像上にハイライト表示
- ハイライトの透過度をスライダーで調整
- ブロック単位のテキスト編集
- ブロックの確認済みフラグ（チェックすると信頼度1.00に上書き）
- ¶ボタンで段落区切りをブロック単位で設定
- ブロックのドラッグによる並び替え
- 移動先番号を直接入力して移動
- 並び替え・削除後にIDを自動で再採番
- 画像上をドラッグして範囲指定→テキスト手動入力でブロックを追加
- **画像クロップ保存** *(v2)* — 指定範囲を独立した画像ファイルとして保存
- ブロック単位の削除
- 一括確認済み / 閾値以上を一括OK / 全て削除

### テキストプレビュー
- 画面下部に現在ページの全テキストを結合表示
- ワンクリックでクリップボードにコピー
- ブロック編集後に再読込みボタンで更新

### 統合出力
- ページ範囲の指定（開始〜終了ページを選択）
- ページ区切り文字の挿入（`{n}`でページ番号を埋め込み可）
- 段落区切りの反映（¶設定されたブロックの前に区切りを挿入）
- TXT形式（テキストのみ）
- JSON形式（座標・信頼度付き）
- 出力前にプレビューで確認、コピーボタンでそのままコピーも可能

---

## 動作環境

| ライブラリ | バージョン | 備考 |
|---|---|---|
| Python | 3.8以上 | |
| Flask | 2.3以上 | |
| [NDLOCR-Lite](https://github.com/ndl-lab/ndlocr-lite) | 最新 | 別途インストール必要 |
| Pillow | 任意 | v2 — 画像クロップ・EXIF補正 |
| pdf2image | 任意 | v2 — PDFインポート |
| poppler | 任意 | v2 — PDFインポート（Mac: `brew install poppler`） |

Pillow・pdf2image・popplerは **v2拡張機能のみ必要**です。不足している場合、ランチャーがセットアップ画面を表示し、v1として起動します。

---

## インストール手順

### 1. NDLOCR-Liteをインストール

```bash
git clone https://github.com/ndl-lab/ndlocr-lite
cd ndlocr-lite/ndlocr-lite-gui
pip3 install -r ../requirements.txt
```

動作確認：

```bash
PYTHONPATH=~/ndlocr-lite/src python3 ~/ndlocr-lite/ndlocr-lite-gui/main.py
```

### 2. OCR Project Managerをインストール

```bash
git clone https://github.com/StateToolsLab/ocr-project-manager.git ~/ocr-project-manager
cd ~/ocr-project-manager
pip3 install flask
```

v2拡張機能を使う場合（任意）：

```bash
pip3 install Pillow pdf2image
brew install poppler        # Mac
# sudo apt install poppler-utils   # Linux
```

### 3. 起動スクリプトに実行権限を付与（Mac）

```bash
chmod +x ~/ocr-project-manager/OCR_Project_Manager.command
```

### 4. デスクトップにショートカットを作成（Mac）

```bash
ln -s ~/ocr-project-manager/OCR_Project_Manager.command ~/Desktop/OCR_Project_Manager.command
```

---

## 起動方法

デスクトップの `OCR_Project_Manager.command` をダブルクリック。

起動時に環境を自動チェックします：

- **v2依存ライブラリが全て揃っている場合** → v2が `http://localhost:5050` で直接起動
- **不足がある場合** → セットアップ画面が `http://localhost:5051` で開き、インストール案内またはv1での起動を選択できます

初回起動時はMacのセキュリティ警告が出ます。**右クリック→「開く」** で起動してください。

---

## プロジェクトデータの保存場所

```
~/OCR_Projects/
└── プロジェクト名/
    ├── input/              # 元画像
    ├── output/
    │   ├── *.json          # OCR結果
    │   ├── *_overlay.json  # 編集データ
    │   └── crop/           # クロップ画像（v2）
    └── meta.json           # プロジェクト設定
```

---

## 更新履歴

### v2（2026年3月）
- PDFインポート（ページごとに自動変換）
- 画像クロップ保存機能
- スマートランチャー（v1フォールバック付き）
- オーバーレイ選択ブロックの青ハイライト
- バグ修正：ブロック並び替え・切り替え後にオーバーレイが黒くなる問題

### v1
- 初回リリース

---

## クレジット

OCRエンジンとして [NDLOCR-Lite](https://github.com/ndl-lab/ndlocr-lite)（国立国会図書館）を使用しています。  
ライセンス：[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
