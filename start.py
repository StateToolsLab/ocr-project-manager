#!/usr/bin/env python3
"""
start.py - OCR Project Manager ランチャー
起動フロー:
  1. Windowsチェック
  2. flaskチェック
  3. v2必須ライブラリチェック（全部OK→v2直接起動、不足→ランチャーUI）
"""

import subprocess
import sys
import threading
import webbrowser

server_should_stop = threading.Event()


# ── チェック関数 ──────────────────────────────────────────────────────────────
def check_flask():
    try:
        import flask  # noqa
        return True
    except ImportError:
        return False


def check_modules():
    results = []

    # Pillow (画像クロップ・EXIF補正)
    try:
        import PIL  # noqa
        results.append({"name": "Pillow", "ok": True, "install": None, "note": "画像クロップ"})
    except ImportError:
        results.append({"name": "Pillow", "ok": False, "install": "pip3 install Pillow", "note": "画像クロップ"})

    # pdf2image
    try:
        import pdf2image  # noqa
        results.append({"name": "pdf2image", "ok": True, "install": None, "note": "PDF変換"})
    except ImportError:
        results.append({"name": "pdf2image", "ok": False, "install": "pip3 install pdf2image", "note": "PDF変換"})

    # poppler (pdftoppm コマンドで確認)
    import shutil
    if shutil.which("pdftoppm"):
        results.append({"name": "poppler", "ok": True, "install": None, "note": "PDF変換"})
    else:
        results.append({"name": "poppler", "ok": False, "install": "brew install poppler", "note": "PDF変換"})

    return results


def launch_version(version):
    """指定バージョンのappをサブプロセスで起動する"""
    import os
    script = "app_v2.py" if version == "v2" else "app.py"
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script)
    subprocess.Popen(
        [sys.executable, script_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


# ── HTML ─────────────────────────────────────────────────────────────────────
LAUNCHER_HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OCR Project Manager — Launcher</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@300;400;600&family=JetBrains+Mono:wght@300;400&display=swap');

  :root {
    --bg:      #0f0f0f;
    --bg2:     #161616;
    --bg3:     #1e1e1e;
    --border:  #2a2a2a;
    --border2: #333;
    --text:    #e8e0d5;
    --text2:   #9a9080;
    --text3:   #5a5248;
    --accent:  #c8a96e;
    --accent2: #8b6f47;
    --warn:    #d4826a;
    --ok:      #6a9d6e;
    --font-serif: 'Noto Serif JP', serif;
    --font-mono:  'JetBrains Mono', monospace;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font-serif);
    font-size: 14px;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
  }

  .container {
    width: 100%;
    max-width: 520px;
  }

  /* ── Header ── */
  .logo {
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 0.25em;
    color: var(--accent);
    text-transform: uppercase;
    margin-bottom: 4px;
  }
  .logo span { color: var(--text3); }
  h1 {
    font-size: 22px;
    font-weight: 300;
    color: var(--text);
    letter-spacing: 0.05em;
    margin-bottom: 32px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border);
  }

  /* ── Section ── */
  .section-label {
    font-family: var(--font-mono);
    font-size: 9px;
    letter-spacing: 0.2em;
    color: var(--text3);
    text-transform: uppercase;
    margin-bottom: 10px;
  }

  /* ── Warning Banner ── */
  .warn-banner {
    background: rgba(212, 130, 106, 0.08);
    border: 1px solid rgba(212, 130, 106, 0.3);
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 24px;
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--warn);
    letter-spacing: 0.02em;
  }

  /* ── Module Check ── */
  .module-list {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
    margin-bottom: 28px;
  }
  .module-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
  }
  .module-item:last-child { border-bottom: none; }
  .module-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
  }
  .dot-ok   { background: var(--ok); }
  .dot-fail { background: var(--warn); }
  .module-name {
    font-family: var(--font-mono);
    font-size: 12px;
    flex: 1;
  }
  .module-status {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text3);
  }
  .status-ok   { color: var(--ok); }
  .status-fail { color: var(--warn); }
  .install-cmd {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--accent2);
    background: var(--bg3);
    padding: 2px 8px;
    border-radius: 3px;
    cursor: pointer;
    border: 1px solid var(--border2);
    transition: all 0.15s;
    white-space: nowrap;
  }
  .install-cmd:hover { border-color: var(--accent); color: var(--accent); }
  .install-cmd.copied { color: var(--ok); border-color: var(--ok); }

  /* ── Actions ── */
  .actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-bottom: 0;
  }
  .launch-btn {
    width: 100%;
    padding: 12px;
    background: var(--accent2);
    border: 1px solid var(--accent);
    color: var(--text);
    font-family: var(--font-serif);
    font-size: 13px;
    letter-spacing: 0.05em;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .launch-btn:hover { background: var(--accent); }
  .launch-btn.secondary {
    background: var(--bg3);
    border-color: var(--border2);
    color: var(--text2);
  }
  .launch-btn.secondary:hover {
    border-color: var(--accent2);
    color: var(--text);
  }
  .launch-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
    background: var(--bg3);
    border-color: var(--border2);
  }

  /* ── Status ── */
  .status-area {
    margin-top: 14px;
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text3);
    text-align: center;
    min-height: 18px;
  }
  .status-area.launching { color: var(--accent); }
  .status-area.error     { color: var(--warn); }

  /* ── Footer ── */
  .footer {
    margin-top: 28px;
    text-align: center;
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text3);
  }
  .footer a {
    color: var(--accent2);
    text-decoration: none;
  }
  .footer a:hover { color: var(--accent); }
</style>
</head>
<body>
<div class="container">

  <div class="logo">OCR <span>//</span> Project Manager</div>
  <h1>Launcher</h1>

  <div class="warn-banner" id="warnBanner"></div>

  <div class="section-label">モジュール状態</div>
  <div class="module-list" id="moduleList"></div>

  <div class="actions">
    <button class="launch-btn secondary" id="btnV1" onclick="doLaunch('v1')">v1で起動する</button>
    <button class="launch-btn" id="btnV2" onclick="doLaunch('v2')">インストール後にv2で起動する</button>
  </div>
  <div class="status-area" id="statusArea"></div>

  <div class="footer">
    <a href="https://github.com/StateToolsLab/ocr-project-manager#readme" target="_blank">README / ドキュメント</a>
  </div>
</div>

<script>
// ── 初期ロード ────────────────────────────────────────────────────────────────
async function loadModules() {
  const res = await fetch('/api/check');
  const data = await res.json();

  const missing = data.modules.filter(m => !m.ok);
  const banner = document.getElementById('warnBanner');
  if (missing.length > 0) {
    banner.textContent = `v2の必須モジュールが ${missing.length} 件不足しています。v1で起動するか、インストール後にv2で起動してください。`;
  } else {
    banner.textContent = '全モジュールが揃っています。v2で起動できます。';
    banner.style.color = 'var(--ok)';
    banner.style.borderColor = 'rgba(106,157,110,0.3)';
    banner.style.background = 'rgba(106,157,110,0.06)';
  }

  const list = document.getElementById('moduleList');
  list.innerHTML = data.modules.map(m => `
    <div class="module-item">
      <div class="module-dot ${m.ok ? 'dot-ok' : 'dot-fail'}"></div>
      <div class="module-name">${m.name}${m.note ? ` <span style="color:var(--text3);font-size:9px">(${m.note})</span>` : ''}</div>
      <div class="module-status ${m.ok ? 'status-ok' : 'status-fail'}">
        ${m.ok ? '✓ OK' : '未インストール'}
      </div>
      ${!m.ok && m.install ? `<button class="install-cmd" onclick="copyCmd(this, '${m.install}')">${m.install}</button>` : ''}
    </div>
  `).join('');
}

function copyCmd(btn, cmd) {
  navigator.clipboard.writeText(cmd).then(() => {
    const orig = btn.textContent;
    btn.textContent = '✓ コピー';
    btn.classList.add('copied');
    setTimeout(() => {
      btn.textContent = orig;
      btn.classList.remove('copied');
    }, 2000);
  });
}

// ── 起動 ──────────────────────────────────────────────────────────────────────
async function doLaunch(version) {
  const btnV1 = document.getElementById('btnV1');
  const btnV2 = document.getElementById('btnV2');
  const status = document.getElementById('statusArea');

  btnV1.disabled = true;
  btnV2.disabled = true;
  status.textContent = `${version === 'v2' ? 'v2 拡張版' : 'v1 安定版'} を起動中...`;
  status.className = 'status-area launching';

  const res = await fetch('/api/launch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ version }),
  });
  const data = await res.json();

  if (data.ok) {
    status.textContent = '起動しました — このタブは閉じてください';
    status.className = 'status-area';
    setTimeout(() => {
      window.location.href = 'http://localhost:5050';
    }, 1200);
  } else {
    status.textContent = `エラー: ${data.error}`;
    status.className = 'status-area error';
    btnV1.disabled = false;
    btnV2.disabled = false;
    // モジュール状態を再取得して表示を更新
    loadModules();
  }
}

loadModules();
</script>
</body>
</html>
"""


# ── Flask App ─────────────────────────────────────────────────────────────────
def create_flask_app():
    from flask import Flask, jsonify, render_template_string, request as freq

    flask_app = Flask(__name__)

    @flask_app.route("/")
    def index():
        return render_template_string(LAUNCHER_HTML)

    @flask_app.route("/api/check")
    def api_check():
        modules = check_modules()
        v2_available = all(m["ok"] for m in modules)
        return jsonify({"modules": modules, "v2_available": v2_available})

    @flask_app.route("/api/launch", methods=["POST"])
    def api_launch():
        data = freq.json
        version = data.get("version", "v1")

        # v2起動時はモジュールを再チェック
        if version == "v2":
            modules = check_modules()
            missing = [m["name"] for m in modules if not m["ok"]]
            if missing:
                return jsonify({"ok": False, "error": f"不足モジュール: {', '.join(missing)}"})

        try:
            launch_version(version)
            threading.Timer(2.0, lambda: server_should_stop.set()).start()
            return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)})

    return flask_app


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # 1. Windowsチェック
    if sys.platform == "win32":
        print("NDLOCRLiteはMac/Linux向けです。Windowsでの動作は保証されていません。")
        ans = input("続行しますか？ [y/N]: ").strip().lower()
        if ans != "y":
            sys.exit(0)

    # 2. Flaskチェック
    if not check_flask():
        print("エラー: flaskがインストールされていません。")
        print("インストールコマンド: pip3 install flask")
        sys.exit(1)

    # 3. v2ライブラリチェック
    modules = check_modules()
    v2_available = all(m["ok"] for m in modules)

    if v2_available:
        # 全部OK → v2を直接起動（ランチャーUIスキップ）
        print("OCR Project Manager v2 を起動します...")
        launch_version("v2")
        import time
        threading.Timer(1.5, lambda: webbrowser.open("http://localhost:5050")).start()
        print("ブラウザで http://localhost:5050 を開きます。")
        time.sleep(3)
        sys.exit(0)

    # 不足あり → ランチャーUIを起動
    missing_names = [m["name"] for m in modules if not m["ok"]]
    print(f"v2必須モジュールが不足しています: {', '.join(missing_names)}")
    print("OCR Project Manager ランチャー起動中...")

    flask_app = create_flask_app()
    threading.Timer(0.8, lambda: webbrowser.open("http://localhost:5051")).start()

    def run_server():
        flask_app.run(host="127.0.0.1", port=5051, debug=False)

    t = threading.Thread(target=run_server, daemon=True)
    t.start()

    server_should_stop.wait()
    print("ランチャーを終了します")
