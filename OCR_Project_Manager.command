#!/bin/bash
# OCR Project Manager 起動スクリプト
# このファイルをデスクトップに置いてダブルクリックで起動

APP_DIR="$HOME/ocr-project-manager"

# Flaskがなければインストール
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Flaskをインストール中..."
    pip3 install flask
fi

# アプリ起動
echo "OCR Project Manager を起動します..."
cd "$APP_DIR"
python3 app.py
