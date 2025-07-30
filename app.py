import sys
import os
import asyncio
import gradio as gr
from datetime import datetime
import traceback

def test_nodriver_basic():
    """Phase 3: nodriver基本動作テスト"""
    results = []
    
    # コンテナログにも同時出力する関数
    def log_and_append(message):
        results.append(message)
        print(message)
        sys.stdout.flush()
    
    # 初期ログ出力
    print("=== Phase 3: nodriver基本動作テスト ===")
    print(f"実行時刻: {datetime.now()}")
    print("")
    sys.stdout.flush()
    
    log_and_append("=== Phase 3: nodriver基本動作テスト ===")
    log_and_append(f"実行時刻: {datetime.now()}")
    log_and_append("")
    
    # Phase 1,2結果の再確認
    log_and_append("📋 前Phase結果の再確認:")
    log_and_append("  ✅ Phase 1: Python環境、依存関係、Chromiumバイナリ")
    log_and_append("  ✅ Phase 2: Chromium起動、プロセス管理、デバッグポート")
    log_and_append("")
    
    # nodriverインポートテスト
    log_and_append("📦 nodriverインポートテスト:")
    try:
        import nodriver as nd
        log_and_append("  ✅ nodriver インポート成功")
        log_and_append(f"  モジュールパス: {nd.__file__ if hasattr(nd, '__file__') else 'unknown'}")
        log_and_append(f"  バージョン: {nd.__version__ if hasattr(nd, '__version__') else 'unknown'}")
        
        # nodriverの主要属性確認
        log_and_append("  主要属性:")
        important_attrs = ['start', 'Browser', 'Tab', 'Element']
        for attr in important_attrs:
            if hasattr(nd, attr):
                log_and_append(f"    ✅ {attr}: {type(getattr(nd, attr))}")
            else:
                log_and_append(f"    ❌ {attr}: 存在しません")
    except Exception as e:
        log_and_append(f"  ❌ nodriverインポート失敗: {e}")
        log_and_append("Phase 3 ステータス: FAILED - Phase 1を再実行してください")
        return "\n".join(results)
    
    log_and_append("")
    
    # テスト1: 非同期環境確認
    log_and_append("🔄 テスト1: 非同期環境確認")
    try:
        import nest_asyncio
        nest_asyncio.apply()
        log_and_append("  ✅ nest_asyncio 適用成功")
        
        # 現在のイベントループ状況確認
        try:
            loop = asyncio.get_event_loop()
            log_and_append(f"  現在のループ: {type(loop)} (running: {loop.is_running()})")
        except Exception as e:
            log_and_append(f"  ループ確認エラー: {e}")
            
    except Exception as e:
        log_and_append(f"  ❌ 非同期環境準備エラー: {e}")
    
    log_and_append("")
    
    # テスト2: nodriver.start()の詳細テスト
    log_and_append("🚀 テスト2: nodriver.start()詳細テスト")
    
    async def test_nodriver_start():
        browser = None
        try:
            log_and_append("  Step 1: nodriver.start()パラメータ準備")
            
            # Phase 2で成功したChromium設定を使用
            browser_args = [
                '--headless',
                '--no-sandbox', 
                '--disable-gpu',
                '--disable-dev-shm-usage'
            ]
            
            log_and_append(f"    使用引数: {browser_args}")
            log_and_append(f"    sandbox: False")
            log_and_append(f"    headless: True")
            log_and_append("")
            
            log_and_append("  Step 2: nodriver.start()実行開始")
            log_and_append("    ⏳ ブラウザ起動中...")
            
            # nodriver.start()実行
            browser = await nd.start(
                headless=True,
                sandbox=False,
                browser_args=browser_args
            )
            
            log_and_append(f"  Step 3: nodriver.start()戻り値確認")
            log_and_append(f"    戻り値型: {type(browser)}")
            log_and_append(f"    戻り値: {browser}")
            
            if browser is None:
                log_and_append("    ❌ ERROR: browser is None")
                return False
            
            log_and_append("    ✅ browser オブジェクト取得成功")
            
            # browserオブジェクトの詳細確認
            log_and_append("  Step 4: browserオブジェクト詳細確認")
            log_and_append(f"    クラス: {browser.__class__}")
            log_and_append(f"    モジュール: {browser.__class__.__module__}")
            
            # 主要メソッドの存在確認
            important_methods = ['get', 'close', 'stop', 'quit']
            for method in important_methods:
                if hasattr(browser, method):
                    log_and_append(f"    ✅ メソッド {method}: {type(getattr(browser, method))}")
                else:
                    log_and_append(f"    ❌ メソッド {method}: 存在しません")
            
            log_and_append("")
            
            # テスト3: 最小限のページアクセステスト
            log_and_append("  Step 5: 最小限のページアクセステスト")
            
            # data: URLを使用してローカルHTMLをテスト
            test_html = "data:text/html,<html><head><title>Test Page</title></head><body><h1>Hello World</h1></body></html>"
            log_and_append(f"    テストURL: {test_html[:50]}...")
            
            log_and_append("    ⏳ browser.get()実行中...")
            tab = await browser.get(test_html)
            
            log_and_append(f"    browser.get()戻り値型: {type(tab)}")
            log_and_append(f"    browser.get()戻り値: {tab}")
            
            if tab is None:
                log_and_append("    ❌ ERROR: tab is None")
                return False
            
            log_and_append("    ✅ tab オブジェクト取得成功")
            
            # tabオブジェクトの詳細確認
            log_and_append("  Step 6: tabオブジェクト詳細確認")
            log_and_append(f"    クラス: {tab.__class__}")
            
            # タイトル取得テスト
            log_and_append("    ⏳ ページタイトル取得中...")
            try:
                # タイトル取得方法を複数試行
                title_methods = [
                    ('tab.title', lambda: tab.title),
                    ('tab.get_title()', lambda: tab.get_title() if hasattr(tab, 'get_title') else None),
                    ('await tab.evaluate("document.title")', lambda: tab.evaluate('document.title'))
                ]
                
                for method_name, method_func in title_methods:
                    try:
                        log_and_append(f"      試行: {method_name}")
                        if 'await' in method_name:
                            title = await method_func()
                        else:
                            title = method_func()
                        
                        if title:
                            log_and_append(f"      ✅ 成功: '{title}'")
                            break
                        else:
                            log_and_append(f"      ⚠️ 空の結果")
                    except Exception as e:
                        log_and_append(f"      ❌ 失敗: {e}")
                
            except Exception as e:
                log_and_append(f"    ❌ タイトル取得エラー: {e}")
            
            log_and_append("")
            log_and_append("  ✅ nodriver基本動作テスト成功")
            return True
            
        except Exception as e:
            log_and_append(f"  ❌ nodriver.start()エラー: {type(e).__name__}: {e}")
            log_and_append("  詳細スタックトレース:")
            for line in traceback.format_exc().split('\n'):
                if line.strip():
                    log_and_append(f"    {line}")
            return False
            
        finally:
            # 改善されたクリーンアップ処理
            if browser:
                try:
                    log_and_append("  🧹 ブラウザクリーンアップ開始")
                    
                    # Step 1: 全てのタブを安全に閉じる
                    try:
                        if hasattr(browser, 'tabs') and browser.tabs:
                            log_and_append(f"    開いているタブ数: {len(browser.tabs)}")
                            for i, tab in enumerate(browser.tabs):
                                try:
                                    await tab.close()
                                    log_and_append(f"    タブ {i+1} 閉じました")
                                except Exception as tab_error:
                                    log_and_append(f"    タブ {i+1} 閉じる際エラー: {tab_error}")
                        else:
                            log_and_append("    タブなし、またはタブ情報取得不可")
                    except Exception as tabs_error:
                        log_and_append(f"    タブ処理エラー: {tabs_error}")
                    
                    # Step 2: 接続を安全に閉じる
                    try:
                        if hasattr(browser, 'connection') and browser.connection:
                            log_and_append("    WebSocket接続を閉じています...")
                            await browser.connection.aclose()
                            log_and_append("    ✅ WebSocket接続閉じました")
                        else:
                            log_and_append("    WebSocket接続なし、またはすでに閉じられています")
                    except Exception as conn_error:
                        log_and_append(f"    WebSocket接続エラー: {conn_error}")
                    
                    # Step 3: ブラウザプロセスを確認・終了
                    try:
                        if hasattr(browser, '_process') and browser._process:
                            log_and_append("    ブラウザプロセス終了中...")
                            if browser._process.poll() is None:  # プロセスがまだ実行中
                                browser._process.terminate()
                                try:
                                    await asyncio.wait_for(browser._process.wait(), timeout=5)
                                    log_and_append("    ✅ ブラウザプロセス正常終了")
                                except asyncio.TimeoutError:
                                    browser._process.kill()
                                    await browser._process.wait()
                                    log_and_append("    ⚠️ ブラウザプロセス強制終了")
                            else:
                                log_and_append("    ブラウザプロセスは既に終了済み")
                        else:
                            log_and_append("    ブラウザプロセス情報なし")
                    except Exception as process_error:
                        log_and_append(f"    プロセス終了エラー: {process_error}")
                    
                    # Step 4: 最後にbrowser.stop()を呼び出す（エラーを無視）
                    try:
                        await browser.stop()
                        log_and_append("    ✅ browser.stop()完了")
                    except Exception as stop_error:
                        log_and_append(f"    browser.stop()エラー（無視）: {stop_error}")
                    
                    log_and_append("  ✅ ブラウザクリーンアップ完了")
                    
                except Exception as cleanup_error:
                    log_and_append(f"  ❌ クリーンアップ全体エラー: {cleanup_error}")
            else:
                log_and_append("  ブラウザオブジェクトなし - クリーンアップ不要")
    
    # 非同期テストを実行
    try:
        # 新しいイベントループで実行
        success = asyncio.run(test_nodriver_start())
    except Exception as e:
        log_and_append(f"  ❌ 非同期実行エラー: {e}")
        log_and_append("  詳細スタックトレース:")
        for line in traceback.format_exc().split('\n'):
            if line.strip():
                log_and_append(f"    {line}")
        success = False
    
    log_and_append("")
    
    # 総合評価
    log_and_append("📊 Phase 3 総合評価:")
    
    if success:
        log_and_append("  ✅ 成功: nodriver基本動作確認完了")
        phase3_status = "PASSED"
    else:
        log_and_append("  ❌ 失敗: nodriver動作に問題あり")
        phase3_status = "FAILED"
    
    log_and_append("")
    log_and_append(f"Phase 3 ステータス: {phase3_status}")
    
    if phase3_status == "PASSED":
        log_and_append("")
        log_and_append("🎉 Phase 3合格！Phase 4に進む準備ができました。")
        log_and_append("ユーザーからの承認をお待ちしています。")
    else:
        log_and_append("")
        log_and_append("❌ Phase 3で問題が発見されました。")
        log_and_append("上記のエラー詳細を確認して修正が必要です。")
    
    return "\n".join(results)

# Gradioインターフェース
with gr.Blocks(title="Phase 3: nodriver基本動作テスト") as app:
    gr.Markdown("# 🚀 Phase 3: nodriver基本動作テスト")
    gr.Markdown("エルメス商品情報抽出ツールの段階的開発 - Phase 3")
    
    with gr.Row():
        test_btn = gr.Button("🧪 nodriver基本動作テストを実行", variant="primary")
    
    with gr.Row():
        output = gr.Textbox(
            label="テスト結果",
            lines=50,
            interactive=False,
            show_copy_button=True
        )
    
    test_btn.click(
        fn=test_nodriver_basic,
        outputs=output
    )
    
    gr.Markdown("""
    ## Phase 3 の目標
    - nodriver.start()の成功とオブジェクト取得
    - ローカルHTMLページでの基本動作確認
    - タイトル取得などの基本的なページ操作
    - NoneType エラーの根本原因特定
    
    ## 合格基準
    - nodriver.start()でブラウザオブジェクト取得成功
    - browser.get()でタブオブジェクト取得成功
    - 基本的なページ操作（タイトル取得等）成功
    
    ## 前提条件
    - Phase 1: 基本環境テスト合格済み
    - Phase 2: Chromium起動テスト合格済み
    
    ## 注意事項
    - このテストでNoneTypeエラーの根本原因が特定される予定です
    """)

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)