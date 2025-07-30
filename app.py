import sys
import os
import platform
import subprocess
import gradio as gr
from datetime import datetime

def test_basic_environment():
    """Phase 1: 基本環境テスト"""
    results = []
    results.append("=== Phase 1: 基本環境テスト ===")
    results.append(f"実行時刻: {datetime.now()}")
    results.append("")
    
    # コンテナログにも同時出力する関数
    def log_and_append(message):
        results.append(message)
        print(message)  # コンテナログに出力
        sys.stdout.flush()  # 即座にフラッシュ
    
    # 初期ログ出力
    print("=== Phase 1: 基本環境テスト ===")
    print(f"実行時刻: {datetime.now()}")
    print("")
    sys.stdout.flush()
    
    # Python環境確認
    log_and_append("📋 Python環境情報:")
    log_and_append(f"  Python version: {sys.version}")
    log_and_append(f"  Python executable: {sys.executable}")
    log_and_append(f"  Platform: {platform.platform()}")  
    log_and_append(f"  Architecture: {platform.architecture()}")
    log_and_append("")
    
    # 作業環境確認
    log_and_append("📁 作業環境情報:")
    log_and_append(f"  Current directory: {os.getcwd()}")
    log_and_append(f"  User: {os.getenv('USER', 'unknown')}")
    log_and_append(f"  Home: {os.getenv('HOME', 'unknown')}")
    log_and_append("")
    
    # 環境変数確認
    log_and_append("🔧 重要な環境変数:")
    env_vars = ['DISPLAY', 'CHROME_BIN', 'CHROME_PATH', 'CHROMIUM_PATH', 'PATH']
    for var in env_vars:
        value = os.getenv(var, 'not set')
        log_and_append(f"  {var}: {value}")
    log_and_append("")
    
    # 依存関係テスト
    log_and_append("📦 依存関係テスト:")
    dependencies = [
        ('gradio', 'gr'),
        ('nodriver', 'nd'), 
        ('asyncio', 'asyncio'),
        ('nest_asyncio', 'nest_asyncio'),
        ('aiohttp', 'aiohttp')
    ]
    
    failed_imports = []
    for dep_name, import_name in dependencies:
        try:
            if import_name == 'gr':
                import gradio as gr
                log_and_append(f"  ✅ {dep_name}: {gr.__version__ if hasattr(gr, '__version__') else 'imported'}")
            elif import_name == 'nd':
                import nodriver as nd
                log_and_append(f"  ✅ {dep_name}: {nd.__version__ if hasattr(nd, '__version__') else 'imported'}")
            else:
                __import__(import_name)
                log_and_append(f"  ✅ {dep_name}: imported successfully")
        except Exception as e:
            log_and_append(f"  ❌ {dep_name}: {str(e)}")
            failed_imports.append(dep_name)
    
    log_and_append("")
    
    # Chromiumバイナリ確認
    log_and_append("🌐 Chromiumバイナリ確認:")
    chromium_paths = [
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser', 
        '/usr/bin/google-chrome',
        '/opt/google/chrome/chrome'
    ]
    
    chromium_found = False
    for path in chromium_paths:
        if os.path.exists(path):
            log_and_append(f"  ✅ Found: {path}")
            chromium_found = True
            # バージョン確認を試行
            try:
                version_output = subprocess.run([path, '--version'], 
                                              capture_output=True, text=True, timeout=5)
                if version_output.returncode == 0:
                    log_and_append(f"    Version: {version_output.stdout.strip()}")
            except Exception as e:
                log_and_append(f"    Version check failed: {e}")
        else:
            log_and_append(f"  ❌ Not found: {path}")
    
    log_and_append("")
    
    # ファイルシステム権限テスト
    log_and_append("🔒 ファイルシステム権限テスト:")
    test_file = "/tmp/hermes_test.txt"
    try:
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        log_and_append("  ✅ Write/delete permissions: OK")
    except Exception as e:
        log_and_append(f"  ❌ Write/delete permissions: {e}")
    
    # 総合評価
    log_and_append("")
    log_and_append("📊 Phase 1 総合評価:")
    
    if failed_imports:
        log_and_append(f"  ❌ 失敗: 依存関係エラー ({', '.join(failed_imports)})")
        phase1_status = "FAILED"
    elif not chromium_found:
        log_and_append("  ❌ 失敗: Chromiumバイナリが見つかりません")
        phase1_status = "FAILED"
    else:
        log_and_append("  ✅ 成功: 基本環境は正常です")
        phase1_status = "PASSED"
    
    log_and_append("")
    log_and_append(f"Phase 1 ステータス: {phase1_status}")
    
    if phase1_status == "PASSED":
        log_and_append("")
        log_and_append("🎉 Phase 1合格！Phase 2に進む準備ができました。")
        log_and_append("ユーザーからの承認をお待ちしています。")

    return "\n".join(results)

# Gradioインターフェース
with gr.Blocks(title="Phase 1: 基本環境テスト") as app:
    gr.Markdown("# 🔧 Phase 1: 基本環境テスト")
    gr.Markdown("エルメス商品情報抽出ツールの段階的開発 - Phase 1")
    
    with gr.Row():
        test_btn = gr.Button("🧪 基本環境テストを実行", variant="primary")
    
    with gr.Row():
        output = gr.Textbox(
            label="テスト結果",
            lines=30,
            interactive=False,
            show_copy_button=True
        )
    
    test_btn.click(
        fn=test_basic_environment,
        outputs=output
    )
    
    gr.Markdown("""
    ## Phase 1 の目標
    - Python 3.10環境の確認
    - 全依存関係のインポート成功
    - Chromiumバイナリの存在確認
    - ファイルシステム権限の確認
    
    ## 合格基準
    全ての項目で ✅ が表示されることが必要です。
    ❌ が表示された場合は、その問題を解決してから次のPhaseに進みます。
    """)

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)