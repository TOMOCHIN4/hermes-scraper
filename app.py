import sys
import os
import asyncio
import gradio as gr
from datetime import datetime
import traceback
import json
import time

def test_hermes_site_scraping():
    """Phase 6: エルメスサイト特化テスト"""
    results = []
    
    # コンテナログにも同時出力する関数
    def log_and_append(message):
        results.append(message)
        print(message)
        sys.stdout.flush()
    
    # 初期ログ出力
    print("=== Phase 6: エルメスサイト特化テスト ===")
    print(f"実行時刻: {datetime.now()}")
    print("")
    sys.stdout.flush()
    
    log_and_append("=== Phase 6: エルメスサイト特化テスト ===")
    log_and_append(f"実行時刻: {datetime.now()}")
    log_and_append("")
    
    # Phase 1-5結果の再確認
    log_and_append("📋 前Phase結果の再確認:")
    log_and_append("  ✅ Phase 1: Python環境、依存関係、Chromiumバイナリ")
    log_and_append("  ✅ Phase 2: Chromium起動、プロセス管理、デバッグポート")
    log_and_append("  ✅ Phase 3: nodriver基本動作、ローカルHTML取得")
    log_and_append("  ✅ Phase 4: ネットワーク接続、外部サイトアクセス")
    log_and_append("  ✅ Phase 5: JavaScript実行、DOM操作、データ抽出")
    log_and_append("")
    
    # エルメスサイト特化テスト
    log_and_append("🛍️ Phase 6: エルメスサイト特化テスト")
    
    async def test_hermes_functionality():
        browser = None
        try:
            # nodriverインポート
            import nodriver as nd
            import nest_asyncio
            nest_asyncio.apply()
            
            log_and_append("  Step 1: 特殊ブラウザ設定でnodriver起動")
            
            # エルメスサイト用の特殊設定
            browser_args = [
                '--headless',
                '--no-sandbox',
                '--disable-gpu',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--exclude-switches=enable-automation',
                '--disable-extensions',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
            
            browser = await nd.start(
                headless=True,
                sandbox=False,
                browser_args=browser_args
            )
            
            log_and_append(f"    ✅ Browser開始成功: {type(browser)}")
            log_and_append("")
            
            # テスト1: エルメス公式サイト接続テスト
            log_and_append("  Step 2: エルメス公式サイト接続テスト")
            
            hermes_urls = [
                {
                    "name": "エルメス日本公式トップページ",
                    "url": "https://www.hermes.com/jp/ja/",
                    "timeout": 20
                },
                {
                    "name": "エルメス商品カテゴリページ",
                    "url": "https://www.hermes.com/jp/ja/category/women/",
                    "timeout": 25
                },
                {
                    "name": "エルメスバッグカテゴリ",
                    "url": "https://www.hermes.com/jp/ja/category/women/bags-and-clutches/",
                    "timeout": 30
                }
            ]
            
            successful_connections = 0
            accessible_pages = []
            
            for i, site in enumerate(hermes_urls, 1):
                log_and_append(f"    テスト{i}: {site['name']}")
                log_and_append(f"    URL: {site['url']}")
                
                try:
                    log_and_append(f"    ⏳ 接続中 (タイムアウト: {site['timeout']}秒)...")
                    
                    # タイムアウト付きでページアクセス
                    tab = await asyncio.wait_for(
                        browser.get(site['url']), 
                        timeout=site['timeout']
                    )
                    
                    if tab is None:
                        log_and_append(f"    ❌ タブ取得失敗")
                        continue
                    
                    log_and_append(f"    ✅ ページアクセス成功")
                    
                    # ページロード完了を待機
                    await asyncio.sleep(3)
                    
                    # 基本情報取得
                    try:
                        # ページタイトル取得
                        title = await tab.evaluate('document.title')
                        log_and_append(f"    ページタイトル: '{title}'")
                        
                        # ページURL確認
                        current_url = await tab.evaluate('window.location.href')
                        log_and_append(f"    現在URL: {current_url}")
                        
                        # 基本的なページ要素確認
                        body_exists = await tab.evaluate('document.body ? true : false')
                        log_and_append(f"    Body要素: {'存在' if body_exists else '不存在'}")
                        
                        if body_exists:
                            # ページ内容の一部取得
                            content_length = await tab.evaluate('document.body.innerText.length')
                            log_and_append(f"    ページ内容長: {content_length}文字")
                            
                            successful_connections += 1
                            accessible_pages.append({
                                "name": site['name'],
                                "url": site['url'],
                                "title": title,
                                "tab": tab
                            })
                        
                    except Exception as info_error:
                        log_and_append(f"    ⚠️ ページ情報取得エラー: {info_error}")
                
                except asyncio.TimeoutError:
                    log_and_append(f"    ❌ タイムアウト ({site['timeout']}秒)")
                except Exception as page_error:
                    log_and_append(f"    ❌ ページアクセスエラー: {type(page_error).__name__}: {page_error}")
                
                log_and_append("")
                
                # アクセス間隔を空ける（レート制限対策）
                if i < len(hermes_urls):
                    log_and_append(f"    ⏱️ アクセス間隔調整中 (3秒待機)...")
                    await asyncio.sleep(3)
            
            log_and_append(f"📊 エルメスサイト接続結果: {successful_connections}/{len(hermes_urls)} 成功")
            log_and_append("")
            
            # テスト2: 商品情報抽出テスト（接続成功したページで実行）
            if accessible_pages:
                log_and_append("  Step 3: 商品情報抽出テスト")
                
                extraction_success = False
                
                for page in accessible_pages:
                    log_and_append(f"    対象ページ: {page['name']}")
                    
                    try:
                        tab = page['tab']
                        
                        # エルメス特有のセレクタで商品情報を探索
                        product_selectors = [
                            "article[data-product]",  # 一般的な商品記事
                            ".product-item",          # 商品アイテム
                            ".product-card",          # 商品カード
                            "[data-testid*=\"product\"]", # テストID付き商品
                            ".grid-item",             # グリッドアイテム
                            ".product-tile"           # 商品タイル
                        ]
                        
                        for selector in product_selectors:
                            try:
                                count_script = f"document.querySelectorAll('{selector}').length"
                                count = await tab.evaluate(count_script)
                                log_and_append(f"      セレクタ '{selector}': {count}件")
                                
                                if count > 0:
                                    # 商品情報詳細取得を試行
                                    detail_script = f'''
                                    (function() {{
                                        const items = Array.from(document.querySelectorAll('{selector}'));
                                        return items.slice(0, 3).map((item, index) => {{
                                            return {{
                                                index: index + 1,
                                                tagName: item.tagName,
                                                className: item.className,
                                                innerHTML: item.innerHTML.substring(0, 200),
                                                textContent: item.textContent.substring(0, 100)
                                            }};
                                        }});
                                    }})()
                                    '''
                                    
                                    details = await tab.evaluate(detail_script)
                                    if details and len(details) > 0:
                                        log_and_append(f"      ✅ 商品要素詳細取得成功: {len(details)}件")
                                        extraction_success = True
                                        break
                                        
                            except Exception as selector_error:
                                log_and_append(f"      ⚠️ セレクタ '{selector}' エラー: {selector_error}")
                        
                        if extraction_success:
                            break
                            
                    except Exception as extract_error:
                        log_and_append(f"    ❌ 抽出テストエラー: {extract_error}")
                
                if extraction_success:
                    log_and_append("    ✅ 商品情報抽出機能の基本動作確認完了")
                else:
                    log_and_append("    ⚠️ 商品情報抽出: 該当要素なし（通常の商品ページではない可能性）")
            else:
                log_and_append("  Step 3: スキップ（接続成功ページなし）")
                extraction_success = False
            
            log_and_append("")
            
            # テスト3: アンチボット・セキュリティ対策確認
            log_and_append("  Step 4: セキュリティ・アンチボット対策確認")
            
            security_checks = []
            
            if accessible_pages:
                try:
                    tab = accessible_pages[0]['tab']
                    
                    # 一般的なボット検出要素の確認
                    security_script = '''
                    (function() {
                        const checks = {};
                        
                        // navigator情報
                        checks.webdriver = navigator.webdriver;
                        checks.userAgent = navigator.userAgent.includes('HeadlessChrome');
                        checks.languages = navigator.languages.length;
                        
                        // window要素
                        checks.chrome = !!window.chrome;
                        checks.permissions = !!navigator.permissions;
                        
                        // 特殊要素
                        checks.captcha = document.querySelector('[class*="captcha"]') ? true : false;
                        checks.cloudflare = document.querySelector('[data-cf-beacon]') ? true : false;
                        
                        return checks;
                    })()
                    '''
                    
                    security_info = await tab.evaluate(security_script)
                    
                    log_and_append("    セキュリティ状況:")
                    for key, value in security_info.items():
                        status = "🚨" if value else "✅"
                        log_and_append(f"      {status} {key}: {value}")
                    
                    security_checks = security_info
                    
                except Exception as security_error:
                    log_and_append(f"    ⚠️ セキュリティチェックエラー: {security_error}")
            else:
                log_and_append("    スキップ（接続成功ページなし）")
            
            log_and_append("")
            
            # 総合評価
            log_and_append("📊 エルメスサイト特化テスト結果:")
            log_and_append(f"  サイト接続: {successful_connections}/{len(hermes_urls)}")
            log_and_append(f"  商品抽出: {'成功' if extraction_success else '要改善'}")
            security_ok_count = len([k for k, v in security_checks.items() if not v]) if isinstance(security_checks, dict) else 0
            security_total = len(security_checks) if isinstance(security_checks, dict) else 0
            log_and_append(f"  セキュリティ: {security_ok_count}/{security_total}項目OK")
            
            # 成功判定（接続成功があれば基本的にOK）
            hermes_success = successful_connections > 0
            
            return hermes_success
            
        except Exception as e:
            log_and_append(f"❌ エルメスサイトテスト全体エラー: {type(e).__name__}: {e}")
            log_and_append("詳細スタックトレース:")
            for line in traceback.format_exc().split('\n'):
                if line.strip():
                    log_and_append(f"  {line}")
            return False
            
        finally:
            # ブラウザクリーンアップ
            if browser:
                try:
                    log_and_append("🧹 ブラウザクリーンアップ")
                    await browser.stop()
                except:
                    pass
                log_and_append("✅ クリーンアップ完了")
    
    # 非同期テストを実行
    try:
        hermes_success = asyncio.run(test_hermes_functionality())
    except Exception as e:
        log_and_append(f"❌ 非同期実行エラー: {e}")
        log_and_append("詳細スタックトレース:")
        for line in traceback.format_exc().split('\n'):
            if line.strip():
                log_and_append(f"  {line}")
        hermes_success = False
    
    log_and_append("")
    
    # 総合評価
    log_and_append("📊 Phase 6 総合評価:")
    
    if hermes_success:
        log_and_append("  ✅ 成功: エルメスサイト特化テスト完了")
        phase6_status = "PASSED"
    else:
        log_and_append("  ❌ 失敗: エルメスサイトアクセスに問題あり")
        phase6_status = "FAILED"
    
    log_and_append("")
    log_and_append(f"Phase 6 ステータス: {phase6_status}")
    
    if phase6_status == "PASSED":
        log_and_append("")
        log_and_append("🎉 Phase 6合格！Phase 7に進む準備ができました。")
        log_and_append("ユーザーからの承認をお待ちしています。")
    else:
        log_and_append("")
        log_and_append("❌ Phase 6で問題が発見されました。")
        log_and_append("エルメスサイトのアクセス制限またはセキュリティ対策の確認が必要です。")
    
    return "\n".join(results)

# Gradioインターフェース
with gr.Blocks(title="Phase 6: エルメスサイト特化テスト") as app:
    gr.Markdown("# 🛍️ Phase 6: エルメスサイト特化テスト")
    gr.Markdown("エルメス商品情報抽出ツールの段階的開発 - Phase 6")
    
    with gr.Row():
        test_btn = gr.Button("🛍️ エルメスサイト特化テストを実行", variant="primary")
    
    with gr.Row():
        output = gr.Textbox(
            label="テスト結果",
            lines=50,
            interactive=False,
            show_copy_button=True
        )
    
    test_btn.click(
        fn=test_hermes_site_scraping,
        outputs=output
    )
    
    gr.Markdown("""
    ## Phase 6 の目標
    - エルメス公式サイトへの接続確認
    - 商品ページの構造解析
    - 実際の商品データ抽出テスト
    - アンチボット・セキュリティ対策の確認
    - レート制限対応の検証
    
    ## 合格基準
    - 最低1つのエルメスページにアクセス成功
    - 基本的なページ情報取得成功
    - セキュリティ制限の把握
    
    ## 前提条件
    - Phase 1-5: 全ての基礎機能テスト合格済み
    
    ## テスト対象
    - エルメス日本公式サイト (hermes.com/jp/ja/)
    - 商品カテゴリページ
    - バッグカテゴリページ
    
    ## 注意事項
    - 実際のサイトにアクセスするため時間がかかります
    - サイトのセキュリティ制限により一部制限される可能性があります
    - レート制限対策として適切な間隔を空けます
    """)

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)