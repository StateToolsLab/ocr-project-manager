# OCR Project Manager

*English README is available at [README.en.md](README.en.md).*

NDLOCRを使ったOCR作業を、ローカルブラウザ上で一元管理できるツールです。

画像のアップロード、OCR実行、結果の検証・編集、テキストの統合出力までを一つのUIで完結できます。

**UIは日本語・英語に対応しています（画面右上で切り替え）。**

---

## 主な機能

### プロジェクト管理
- プロジェクト単位でフォルダを自動生成・管理
- プロジェクト名・説明の編集
- プロジェクト単位での削除

### 画像管理
- 画像のドラッグ&ドロップアップロード（複数可）
- アップロード時にファイル名順で自動ソート
- ページリストでのドラッグによる並び替え
- ページ単位での削除

### OCR実行
- 1ページずつのOCR実行
- 一括OCR実行（未処理ページのみ対象）
- ファイル名衝突を防ぐ安全な出力管理

### 結果の検証・編集
- OCR結果の信頼度スコア表示・閾値設定
- 閾値以下のブロックをオレンジ、確認済みを緑で画像上にハイライト表示
- ハイライトの透過度をスライダーで調整
- ブロック単位のテキスト編集
- ブロックの確認済みフラグ（チェックすると信頼度1.00に上書き）
- ¶ボタンで段落区切りをブロック単位で設定
- ブロックのドラッグによる並び替え
- 移動先番号を直接入力して移動
- 並び替え・削除後にIDを自動で再採番
- 画像上をドラッグして範囲指定→テキスト手動入力でブロックを追加
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

- macOS / Windows / Linux
- Python 3.8以上
- [NDLOCR-Lite](https://github.com/ndl-lab/ndlocr-lite)（別途インストール必要）

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
pip3 install flask
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

ブラウザが自動で `http://localhost:5050` を開きます。

初回起動時はMacのセキュリティ警告が出ます。**右クリック→「開く」** で起動してください。

---

## プロジェクトデータの保存場所

`~/OCR_Projects/` 以下に各プロジェクトフォルダが作成されます。

```
~/OCR_Projects/
└── プロジェクト名/
    ├── input/       # 元画像
    ├── output/      # OCR結果JSON・編集データ
    └── meta.json    # プロジェクト設定
```

---

## クレジット

OCRエンジンとして [NDLOCR-Lite](https://github.com/ndl-lab/ndlocr-lite)（国立国会図書館）を使用しています。  
ライセンス：[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
