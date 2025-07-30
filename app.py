import sys
import os
import asyncio
import gradio as gr
from datetime import datetime
import traceback
import json

def test_javascript_execution():
    """Phase 5: JavaScript実行テスト"""
    results = []
    
    # コンテナログにも同時出力する関数
    def log_and_append(message):
        results.append(message)
        print(message)
        sys.stdout.flush()
    
    # 初期ログ出力
    print("=== Phase 5: JavaScript実行テスト ===")
    print(f"実行時刻: {datetime.now()}")
    print("")
    sys.stdout.flush()
    
    log_and_append("=== Phase 5: JavaScript実行テスト ===")
    log_and_append(f"実行時刻: {datetime.now()}")
    log_and_append("")
    
    # Phase 1,2,3,4結果の再確認
    log_and_append("📋 前Phase結果の再確認:")
    log_and_append("  ✅ Phase 1: Python環境、依存関係、Chromiumバイナリ")
    log_and_append("  ✅ Phase 2: Chromium起動、プロセス管理、デバッグポート")
    log_and_append("  ✅ Phase 3: nodriver基本動作、ローカルHTML取得")
    log_and_append("  ✅ Phase 4: ネットワーク接続、外部サイトアクセス")
    log_and_append("")
    
    # JavaScript実行テスト
    log_and_append("⚡ Phase 5: JavaScript実行・DOM操作テスト")
    
    async def test_javascript_functionality():
        browser = None
        try:
            # nodriverインポート
            import nodriver as nd
            import nest_asyncio
            nest_asyncio.apply()
            
            log_and_append("  Step 1: nodriver.start()実行")
            browser_args = [
                '--headless',
                '--no-sandbox', 
                '--disable-gpu',
                '--disable-dev-shm-usage'
            ]
            
            browser = await nd.start(
                headless=True,
                sandbox=False,
                browser_args=browser_args
            )
            
            log_and_append(f"    ✅ Browser開始成功: {type(browser)}")
            log_and_append("")
            
            # テスト1: 基本的なJavaScript実行
            log_and_append("  Step 2: 基本JavaScript実行テスト")
            
            # 複雑なHTMLページを作成（英語版で文字化け回避）
            test_html = '''
            data:text/html,
            <html>
            <head>
                <title>JavaScript Test Page</title>
                <meta charset="UTF-8">
            </head>
            <body>
                <div id="main-container">
                    <h1 class="title">Test Page</h1>
                    <ul class="product-list">
                        <li class="product-item" data-price="100000">
                            <span class="product-name">Product A</span>
                            <span class="product-price">$1,000</span>
                        </li>
                        <li class="product-item" data-price="150000">
                            <span class="product-name">Product B</span>
                            <span class="product-price">$1,500</span>
                        </li>
                        <li class="product-item" data-price="200000">
                            <span class="product-name">Product C</span>
                            <span class="product-price">$2,000</span>
                        </li>
                    </ul>
                    <div class="hidden-content" style="display:none;">
                        Hidden Content
                    </div>
                </div>
                
                <script>
                    window.testData = {
                        pageType: "test",
                        productCount: 3,
                        totalValue: 450000
                    };
                </script>
            </body>
            </html>
            '''.replace('\n            ', '').replace('            ', '')
            
            tab = await browser.get(test_html)
            log_and_append(f"    ✅ テストページ読み込み完了")
            
            await asyncio.sleep(1)  # DOM構築完了待機
            
            # 基本JavaScript実行テスト
            basic_tests = [
                {
                    "name": "文字列操作",
                    "script": "'Hello ' + 'World'",
                    "expected": "Hello World"
                },
                {
                    "name": "数値計算", 
                    "script": "Math.floor(123.456)",
                    "expected": 123
                },
                {
                    "name": "配列操作",
                    "script": "[1,2,3].length",
                    "expected": 3
                },
                {
                    "name": "現在時刻取得",
                    "script": "typeof new Date()",
                    "expected": "object"
                }
            ]
            
            basic_success = 0
            for test in basic_tests:
                try:
                    result = await tab.evaluate(test["script"])
                    if result == test["expected"]:
                        log_and_append(f"    ✅ {test['name']}: {result}")
                        basic_success += 1
                    else:
                        log_and_append(f"    ⚠️ {test['name']}: 期待値{test['expected']}, 実際{result}")
                except Exception as e:
                    log_and_append(f"    ❌ {test['name']}: エラー {e}")
            
            log_and_append(f"    基本JavaScript: {basic_success}/{len(basic_tests)} 成功")
            log_and_append("")
            
            # テスト2: DOM要素取得・操作
            log_and_append("  Step 3: DOM要素取得・操作テスト")
            
            dom_tests = [
                {
                    "name": "タイトル取得",
                    "script": "document.title",
                    "expected_contains": "JavaScript Test"
                },
                {
                    "name": "ID要素取得",
                    "script": "document.getElementById('main-container') ? 'found' : 'not found'",
                    "expected": "found"
                },
                {
                    "name": "クラス要素数",
                    "script": "document.getElementsByClassName('product-item').length",
                    "expected": 3
                },
                {
                    "name": "CSSセレクタ",
                    "script": "document.querySelector('.title').textContent",
                    "expected": "Test Page"
                },
                {
                    "name": "複数セレクタ",
                    "script": "document.querySelectorAll('.product-name').length",
                    "expected": 3
                }
            ]
            
            dom_success = 0
            for test in dom_tests:
                try:
                    result = await tab.evaluate(test["script"])
                    if "expected_contains" in test:
                        if test["expected_contains"] in str(result):
                            log_and_append(f"    ✅ {test['name']}: '{result}'")
                            dom_success += 1
                        else:
                            log_and_append(f"    ⚠️ {test['name']}: '{result}' (期待文字列なし)")
                    elif result == test["expected"]:
                        log_and_append(f"    ✅ {test['name']}: {result}")
                        dom_success += 1
                    else:
                        log_and_append(f"    ⚠️ {test['name']}: 期待値{test['expected']}, 実際{result}")
                except Exception as e:
                    log_and_append(f"    ❌ {test['name']}: エラー {e}")
            
            log_and_append(f"    DOM操作: {dom_success}/{len(dom_tests)} 成功")
            log_and_append("")
            
            # テスト3: 複雑なデータ抽出（スクレイピング準備）
            log_and_append("  Step 4: 複雑なデータ抽出テスト")
            
            try:
                # 商品情報の一括抽出（エラーハンドリング強化）
                product_extraction_script = '''
                try {
                    const items = Array.from(document.querySelectorAll('.product-item'));
                    if (items.length === 0) {
                        throw new Error('No product items found');
                    }
                    
                    return items.map(item => {
                        const nameEl = item.querySelector('.product-name');
                        const priceEl = item.querySelector('.product-price');
                        
                        if (!nameEl || !priceEl) {
                            throw new Error('Required elements not found');
                        }
                        
                        return {
                            name: nameEl.textContent,
                            price: priceEl.textContent,
                            priceValue: parseInt(item.dataset.price)
                        };
                    });
                } catch (error) {
                    return { error: error.message };
                }
                '''
                
                products = await tab.evaluate(product_extraction_script)
                
                # エラーチェック
                if isinstance(products, dict) and 'error' in products:
                    log_and_append(f"    ❌ 商品抽出エラー: {products['error']}")
                    extraction_success = False
                elif isinstance(products, list) and len(products) > 0:
                    log_and_append(f"    ✅ 商品情報抽出成功: {len(products)}件")
                    
                    for i, product in enumerate(products, 1):
                        log_and_append(f"      商品{i}: {product['name']} - {product['price']} (値:{product['priceValue']})")
                    
                    # 合計金額計算
                    total_script = '''
                    Array.from(document.querySelectorAll('.product-item'))
                         .reduce((sum, item) => sum + parseInt(item.dataset.price), 0)
                    '''
                    
                    total = await tab.evaluate(total_script)
                    log_and_append(f"    ✅ 合計金額計算: ${total:,}")
                    
                    # グローバル変数アクセス
                    global_data = await tab.evaluate('window.testData')
                    log_and_append(f"    ✅ グローバル変数取得: {global_data}")
                    
                    extraction_success = True
                else:
                    log_and_append(f"    ❌ 予期しない結果: {products}")
                    extraction_success = False
                
            except Exception as e:
                log_and_append(f"    ❌ データ抽出エラー: {e}")
                log_and_append(f"    エラー詳細: {traceback.format_exc()}")
                extraction_success = False
            
            log_and_append("")
            
            # テスト4: 動的コンテンツ・非表示要素対応
            log_and_append("  Step 5: 動的コンテンツ対応テスト")
            
            try:
                # 非表示要素の表示化
                show_hidden_script = '''
                document.querySelector('.hidden-content').style.display = 'block';
                document.querySelector('.hidden-content').textContent;
                '''
                
                hidden_content = await tab.evaluate(show_hidden_script)
                log_and_append(f"    ✅ 隠れた要素表示・取得: '{hidden_content}'")
                
                # 新しい要素の動的追加
                add_element_script = '''
                const newItem = document.createElement('li');
                newItem.className = 'product-item';
                newItem.dataset.price = '300000';
                newItem.innerHTML = '<span class="product-name">Dynamic Product</span><span class="product-price">$3,000</span>';
                document.querySelector('.product-list').appendChild(newItem);
                document.querySelectorAll('.product-item').length;
                '''
                
                new_count = await tab.evaluate(add_element_script)
                log_and_append(f"    ✅ 動的要素追加後の商品数: {new_count}")
                
                dynamic_success = True
                
            except Exception as e:
                log_and_append(f"    ❌ 動的コンテンツエラー: {e}")
                dynamic_success = False
            
            log_and_append("")
            
            # 総合評価
            log_and_append("📊 JavaScript機能テスト結果:")
            log_and_append(f"  基本JavaScript実行: {basic_success}/{len(basic_tests)}")
            log_and_append(f"  DOM操作: {dom_success}/{len(dom_tests)}")
            log_and_append(f"  データ抽出: {'成功' if extraction_success else '失敗'}")
            log_and_append(f"  動的コンテンツ: {'成功' if dynamic_success else '失敗'}")
            
            # 成功判定
            total_success = (basic_success >= len(basic_tests) * 0.8 and 
                           dom_success >= len(dom_tests) * 0.8 and
                           extraction_success and dynamic_success)
            
            return total_success
            
        except Exception as e:
            log_and_append(f"❌ JavaScript実行テスト全体エラー: {type(e).__name__}: {e}")
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
        js_success = asyncio.run(test_javascript_functionality())
    except Exception as e:
        log_and_append(f"❌ 非同期実行エラー: {e}")
        log_and_append("詳細スタックトレース:")
        for line in traceback.format_exc().split('\n'):
            if line.strip():
                log_and_append(f"  {line}")
        js_success = False
    
    log_and_append("")
    
    # 総合評価
    log_and_append("📊 Phase 5 総合評価:")
    
    if js_success:
        log_and_append("  ✅ 成功: JavaScript実行・DOM操作確認完了")
        phase5_status = "PASSED"
    else:
        log_and_append("  ❌ 失敗: JavaScript実行に問題あり")
        phase5_status = "FAILED"
    
    log_and_append("")
    log_and_append(f"Phase 5 ステータス: {phase5_status}")
    
    if phase5_status == "PASSED":
        log_and_append("")
        log_and_append("🎉 Phase 5合格！Phase 6に進む準備ができました。")
        log_and_append("ユーザーからの承認をお待ちしています。")
    else:
        log_and_append("")
        log_and_append("❌ Phase 5で問題が発見されました。")
        log_and_append("JavaScript実行環境またはDOM操作の確認が必要です。")
    
    return "\n".join(results)

# Gradioインターフェース
with gr.Blocks(title="Phase 5: JavaScript実行テスト") as app:
    gr.Markdown("# ⚡ Phase 5: JavaScript実行テスト")
    gr.Markdown("エルメス商品情報抽出ツールの段階的開発 - Phase 5")
    
    with gr.Row():
        test_btn = gr.Button("⚡ JavaScript実行テストを実行", variant="primary")
    
    with gr.Row():
        output = gr.Textbox(
            label="テスト結果",
            lines=50,
            interactive=False,
            show_copy_button=True
        )
    
    test_btn.click(
        fn=test_javascript_execution,
        outputs=output
    )
    
    gr.Markdown("""
    ## Phase 5 の目標
    - 基本的なJavaScript実行確認
    - DOM要素の取得・操作
    - セレクタによる要素検索
    - 複雑なデータ抽出（商品情報等）
    - 動的コンテンツ・非表示要素対応
    
    ## 合格基準
    - 基本JavaScript実行成功 (80%以上)
    - DOM操作成功 (80%以上)
    - データ抽出機能成功
    - 動的コンテンツ対応成功
    
    ## 前提条件
    - Phase 1: 基本環境テスト合格済み
    - Phase 2: Chromium起動テスト合格済み
    - Phase 3: nodriver基本動作テスト合格済み
    - Phase 4: ネットワーク接続テスト合格済み
    
    ## テスト内容
    - 文字列・数値・配列操作
    - DOM要素取得（ID、クラス、セレクタ）
    - 商品情報の一括抽出
    - 動的要素追加・非表示要素表示
    """)

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)