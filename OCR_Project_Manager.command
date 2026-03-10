#!/bin/bash
# OCR Project Manager 起動スクリプト
# このファイルをデスクトップに置いてダブルクリックで起動

APP_DIR="$HOME/ocr-project-manager"

# Flaskがなければインストール
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Flaskをインストール中..."
    pip3 install flask
fi

# ランチャー起動
echo "OCR Project Manager ランチャーを起動します..."
cd "$APP_DIR"
python3 start.py &
LAUNCHER_PID=$!

# ランチャーの終了を待つ
wait $LAUNCHER_PID

# アプリが起動しているのでウィンドウを維持
echo ""
echo "アプリが起動しました。このウィンドウは閉じても構いません。"
read -p "Enterで閉じる..."
