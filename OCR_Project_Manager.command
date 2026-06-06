#!/bin/bash
# OCR Project Manager 起動スクリプト

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$APP_DIR/venv"
PYTHON="$VENV/bin/python3"
PIP="$VENV/bin/pip"

# venvがなければ作成
if [ ! -f "$PYTHON" ]; then
    echo "Python仮想環境を作成中..."
    python3 -m venv "$VENV"
    if [ $? -ne 0 ]; then
        echo "エラー: venvの作成に失敗しました"
        read -p "Enterで閉じる..."
        exit 1
    fi
fi

# 依存ライブラリがなければインストール
if ! "$PYTHON" -c "import flask" 2>/dev/null; then
    echo "ライブラリをインストール中..."
    "$PIP" install flask Pillow pdf2image --quiet
fi

# アプリ起動
echo "OCR Project Manager を起動します..."
cd "$APP_DIR"
exec "$PYTHON" app.py < /dev/null
