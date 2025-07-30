import sys
import os
import platform
import subprocess
import signal
import time
import psutil
import gradio as gr
from datetime import datetime

def test_chromium_startup():
    """Phase 2: Chromium起動テスト"""
    results = []
    
    # コンテナログにも同時出力する関数
    def log_and_append(message):
        results.append(message)
        print(message)
        sys.stdout.flush()
    
    # 初期ログ出力
    print("=== Phase 2: Chromium起動テスト ===")
    print(f"実行時刻: {datetime.now()}")
    print("")
    sys.stdout.flush()
    
    log_and_append("=== Phase 2: Chromium起動テスト ===")
    log_and_append(f"実行時刻: {datetime.now()}")
    log_and_append("")
    
    # Phase 1で確認済みの情報を再確認
    log_and_append("📋 Phase 1結果の再確認:")
    chromium_path = "/usr/bin/chromium"
    if os.path.exists(chromium_path):
        log_and_append(f"  ✅ Chromiumバイナリ: {chromium_path}")
    else:
        log_and_append(f"  ❌ Chromiumバイナリが見つかりません: {chromium_path}")
        log_and_append("Phase 2 ステータス: FAILED - Phase 1を再実行してください")
        return "\n".join(results)
    
    log_and_append("")
    
    # テスト1: Chromiumバージョン確認
    log_and_append("🔍 テスト1: Chromiumバージョン確認")
    try:
        version_result = subprocess.run(
            [chromium_path, "--version"], 
            capture_output=True, text=True, timeout=10
        )
        if version_result.returncode == 0:
            version = version_result.stdout.strip()
            log_and_append(f"  ✅ バージョン取得成功: {version}")
        else:
            log_and_append(f"  ❌ バージョン取得失敗 (return code: {version_result.returncode})")
            log_and_append(f"    stderr: {version_result.stderr}")
    except subprocess.TimeoutExpired:
        log_and_append("  ❌ バージョン確認がタイムアウトしました")
    except Exception as e:
        log_and_append(f"  ❌ バージョン確認エラー: {e}")
    
    log_and_append("")
    
    # テスト2: 最小設定でのプロセス起動テスト
    log_and_append("🚀 テスト2: 最小設定での起動テスト")
    
    test_cases = [
        {
            "name": "基本ヘッドレス",
            "args": ["--headless", "--no-sandbox", "--disable-gpu"]
        },
        {
            "name": "フルセキュリティ無効",
            "args": ["--headless", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
        },
        {
            "name": "完全最小構成",
            "args": ["--headless", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", 
                    "--disable-extensions", "--disable-plugins", "--disable-images"]
        }
    ]
    
    successful_configs = []
    
    for i, test_case in enumerate(test_cases, 1):
        log_and_append(f"  テスト2-{i}: {test_case['name']}")
        log_and_append(f"    引数: {' '.join(test_case['args'])}")
        
        try:
            # プロセス起動
            process = subprocess.Popen(
                [chromium_path] + test_case['args'] + ["--remote-debugging-port=0"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # プロセスグループ作成
            )
            
            log_and_append(f"    プロセス起動: PID {process.pid}")
            
            # 短時間待機してプロセス状態確認
            time.sleep(3)
            
            # プロセスがまだ実行中か確認
            if process.poll() is None:
                log_and_append("    ✅ プロセス起動成功 (3秒後も実行中)")
                
                # psutilでプロセス情報取得
                try:
                    proc_info = psutil.Process(process.pid)
                    log_and_append(f"    プロセス情報: {proc_info.name()}, メモリ: {proc_info.memory_info().rss // 1024 // 1024}MB")
                except:
                    log_and_append("    プロセス情報取得に失敗")
                
                successful_configs.append(test_case['name'])
                
                # プロセス終了
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    process.wait(timeout=5)
                    log_and_append("    ✅ プロセス正常終了")
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    process.wait()
                    log_and_append("    ⚠️ プロセス強制終了")
                except Exception as e:
                    log_and_append(f"    ❌ プロセス終了エラー: {e}")
            else:
                return_code = process.returncode
                stderr_output = process.stderr.read().decode('utf-8', errors='ignore')
                log_and_append(f"    ❌ プロセス即座に終了 (return code: {return_code})")
                if stderr_output:
                    log_and_append(f"    エラー出力: {stderr_output[:200]}...")
        
        except Exception as e:
            log_and_append(f"    ❌ 起動テストエラー: {e}")
        
        log_and_append("")
    
    # テスト3: リモートデバッグポート確認
    log_and_append("🔗 テスト3: リモートデバッグポート機能確認")
    try:
        debug_process = subprocess.Popen(
            [chromium_path, "--headless", "--no-sandbox", "--disable-gpu", "--remote-debugging-port=9222"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        
        log_and_append(f"  デバッグモードプロセス起動: PID {debug_process.pid}")
        time.sleep(2)
        
        if debug_process.poll() is None:
            log_and_append("  ✅ リモートデバッグモード起動成功")
            
            # ポート9222の使用確認を試行
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', 9222))
                sock.close()
                if result == 0:
                    log_and_append("  ✅ デバッグポート9222にアクセス可能")
                else:
                    log_and_append("  ⚠️ デバッグポート9222にアクセス不可（通常動作）")
            except Exception as e:
                log_and_append(f"  ⚠️ ポート確認エラー: {e}")
            
            # プロセス終了
            try:
                os.killpg(os.getpgid(debug_process.pid), signal.SIGTERM)
                debug_process.wait(timeout=5)
                log_and_append("  ✅ デバッグプロセス正常終了")
            except:
                os.killpg(os.getpgid(debug_process.pid), signal.SIGKILL)
                debug_process.wait()
                log_and_append("  ⚠️ デバッグプロセス強制終了")
        else:
            log_and_append("  ❌ リモートデバッグモード起動失敗")
    
    except Exception as e:
        log_and_append(f"  ❌ デバッグポートテストエラー: {e}")
    
    log_and_append("")
    
    # 総合評価
    log_and_append("📊 Phase 2 総合評価:")
    
    if len(successful_configs) == 0:
        log_and_append("  ❌ 失敗: Chromiumプロセス起動に失敗")
        phase2_status = "FAILED"
    elif len(successful_configs) < len(test_cases):
        log_and_append(f"  ⚠️ 部分成功: {len(successful_configs)}/{len(test_cases)} 設定で起動成功")
        log_and_append(f"    成功設定: {', '.join(successful_configs)}")
        phase2_status = "PARTIAL"
    else:
        log_and_append("  ✅ 成功: 全てのChromium設定で起動成功")
        phase2_status = "PASSED"
    
    log_and_append("")
    log_and_append(f"Phase 2 ステータス: {phase2_status}")
    
    if phase2_status == "PASSED":
        log_and_append("")
        log_and_append("🎉 Phase 2合格！Phase 3に進む準備ができました。")
        log_and_append("ユーザーからの承認をお待ちしています。")
    elif phase2_status == "PARTIAL":
        log_and_append("")
        log_and_append("⚠️ Phase 2部分合格。問題を修正するか、現状でPhase 3に進むか判断が必要です。")
    
    return "\n".join(results)

# Gradioインターフェース
with gr.Blocks(title="Phase 2: Chromium起動テスト") as app:
    gr.Markdown("# 🌐 Phase 2: Chromium起動テスト")
    gr.Markdown("エルメス商品情報抽出ツールの段階的開発 - Phase 2")
    
    with gr.Row():
        test_btn = gr.Button("🚀 Chromium起動テストを実行", variant="primary")
    
    with gr.Row():
        output = gr.Textbox(
            label="テスト結果",
            lines=40,
            interactive=False,
            show_copy_button=True
        )
    
    test_btn.click(
        fn=test_chromium_startup,
        outputs=output
    )
    
    gr.Markdown("""
    ## Phase 2 の目標
    - Chromiumバイナリの実行可能性確認
    - 複数の設定でのプロセス起動テスト  
    - プロセス管理（起動・終了）の検証
    - リモートデバッグポート機能の確認
    
    ## 合格基準
    - 最低1つの設定でChromiumプロセス起動成功
    - プロセス管理が正常に動作
    - 全ての基本テストで ✅ が表示される
    
    ## 注意事項
    - Phase 1が合格していることが前提
    - Chromiumプロセスは自動的に適切に終了されます
    """)

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)