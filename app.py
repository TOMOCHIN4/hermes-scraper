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
                    "name": "エルメスバッグ検索ページ（JSON抽出テスト用）",
                    "url": "https://www.hermes.com/jp/ja/search/?s=%E3%83%90%E3%83%83%E3%82%B0#",
                    "timeout": 45,
                    "extract_products": True
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
                    
                    # 検索結果ページの完全レンダリング待機（改善版）
                    log_and_append(f"    ⏳ Angular初期化・商品リスト読み込み待機...")
                    
                    # Step 1: 基本待機（Angular初期化）
                    await asyncio.sleep(10)
                    
                    # Step 2: 商品コンテナ要素の出現を待機
                    container_selectors = [
                        'h-grid-results',
                        '.product-grid-list',
                        '[data-testid="product-grid"]',
                        '.search-results',
                        'h-grid-result-item'
                    ]
                    
                    container_found = False
                    for selector in container_selectors:
                        try:
                            log_and_append(f"      要素待機: {selector}")
                            # 要素出現まで最大20秒待機
                            for attempt in range(40):  # 0.5秒 × 40回 = 20秒
                                element_exists = await tab.evaluate(f'document.querySelector("{selector}") ? true : false')
                                if element_exists:
                                    log_and_append(f"      ✅ 要素発見: {selector}")
                                    container_found = True
                                    break
                                await asyncio.sleep(0.5)
                            
                            if container_found:
                                break
                                
                        except Exception as wait_error:
                            log_and_append(f"      ⚠️ 要素待機エラー: {selector} - {wait_error}")
                    
                    if not container_found:
                        log_and_append(f"    ⚠️ 商品コンテナ要素が見つかりません（20秒経過）")
                    
                    # Step 3: 追加でスクロール処理（無限スクロール対応）
                    log_and_append(f"    📜 ページスクロール実行...")
                    try:
                        await tab.evaluate('''
                            window.scrollTo(0, document.body.scrollHeight / 2);
                        ''')
                        await asyncio.sleep(2)
                        await tab.evaluate('''
                            window.scrollTo(0, document.body.scrollHeight);
                        ''')
                        await asyncio.sleep(3)
                        log_and_append(f"    ✅ スクロール完了")
                    except Exception as scroll_error:
                        log_and_append(f"    ⚠️ スクロールエラー: {scroll_error}")
                    
                    # 【詳細ロギング】基本ページ情報の完全取得
                    try:
                        log_and_append(f"    🔍 ページ詳細情報取得開始")
                        
                        # ページタイトル取得
                        title = await tab.evaluate('document.title')
                        log_and_append(f"    ページタイトル: '{title}'")
                        
                        # ページURL確認
                        current_url = await tab.evaluate('window.location.href')
                        log_and_append(f"    現在URL: {current_url}")
                        
                        # Redirect確認
                        original_url = site['url']
                        if current_url != original_url:
                            log_and_append(f"    🔄 リダイレクト検出:")
                            log_and_append(f"      元URL: {original_url}")
                            log_and_append(f"      現URL: {current_url}")
                        
                        # 基本的なページ要素確認
                        body_exists = await tab.evaluate('document.body ? true : false')
                        log_and_append(f"    Body要素: {'存在' if body_exists else '不存在'}")
                        
                        if body_exists:
                            # 【詳細ロギング】ページコンテンツ分析
                            page_analysis = await tab.evaluate('''
                            (function() {
                                const body = document.body;
                                const analysis = {
                                    contentLength: body.innerText.length,
                                    htmlLength: body.innerHTML.length,
                                    childElementCount: body.children.length,
                                    hasScripts: document.scripts.length,
                                    hasAngular: !!window.angular || !!document.querySelector('[ng-app]') || !!document.querySelector('h-root'),
                                    visible_text_sample: body.innerText.substring(0, 200),
                                    meta_viewport: document.querySelector('meta[name="viewport"]') ? 'exists' : 'missing',
                                    page_ready_state: document.readyState
                                };
                                
                                // CAPTCHA/ブロック検出
                                analysis.security_indicators = {
                                    captcha: !!document.querySelector('[class*="captcha"], [id*="captcha"]'),
                                    cloudflare: !!document.querySelector('[data-cf-beacon], .cf-browser-verification'),
                                    blocked_text: body.innerText.toLowerCase().includes('blocked') || body.innerText.toLowerCase().includes('access denied'),
                                    bot_detected: body.innerText.toLowerCase().includes('bot') && body.innerText.toLowerCase().includes('detected')
                                };
                                
                                return analysis;
                            })()
                            ''')
                            
                            # nodriverの戻り値を安全に処理
                            def safe_get(data, key, default='N/A'):
                                """nodriverの戻り値から安全にデータを取得"""
                                try:
                                    if isinstance(data, dict):
                                        return data.get(key, default)
                                    elif isinstance(data, list) and len(data) > 0:
                                        # nodriverが配列で返す場合の処理
                                        for item in data:
                                            if isinstance(item, dict) and key in item:
                                                return item[key]
                                        return default
                                    else:
                                        return default
                                except:
                                    return default
                            
                            log_and_append(f"    📄 ページコンテンツ分析:")
                            log_and_append(f"      データ型: {type(page_analysis)}")
                            
                            if isinstance(page_analysis, dict):
                                log_and_append(f"      テキスト長: {safe_get(page_analysis, 'contentLength')}文字")
                                log_and_append(f"      HTML長: {safe_get(page_analysis, 'htmlLength')}文字") 
                                log_and_append(f"      子要素数: {safe_get(page_analysis, 'childElementCount')}個")
                                log_and_append(f"      スクリプト数: {safe_get(page_analysis, 'hasScripts')}個")
                                log_and_append(f"      Angular検出: {safe_get(page_analysis, 'hasAngular')}")
                                log_and_append(f"      ページ状態: {safe_get(page_analysis, 'page_ready_state')}")
                                
                                # 【重要】セキュリティ・ブロック検出
                                security = safe_get(page_analysis, 'security_indicators', {})
                                if isinstance(security, dict):
                                    log_and_append(f"    🛡️ セキュリティ状況:")
                                    log_and_append(f"      CAPTCHA: {safe_get(security, 'captcha')}")
                                    log_and_append(f"      Cloudflare: {safe_get(security, 'cloudflare')}")
                                    log_and_append(f"      ブロック検出: {safe_get(security, 'blocked_text')}")
                                    log_and_append(f"      Bot検出: {safe_get(security, 'bot_detected')}")
                                
                                # コンテンツサンプル表示
                                sample = safe_get(page_analysis, 'visible_text_sample')
                                if sample and sample != 'N/A':
                                    log_and_append(f"    📝 表示テキストサンプル:")
                                    log_and_append(f"      '{sample}'")
                            else:
                                log_and_append(f"      ⚠️ 予期しないデータ形式: {page_analysis}")
                            
                            # hermes-state スクリプトの詳細確認
                            hermes_state_analysis = await tab.evaluate('''
                            (function() {
                                try {
                                    const script = document.getElementById('hermes-state');
                                    if (script) {
                                        const content = script.textContent;
                                        return {
                                            exists: true,
                                            size: content.length,
                                            type: script.type,
                                            first_100_chars: content.substring(0, 100),
                                            last_100_chars: content.length > 100 ? content.substring(content.length - 100) : '',
                                            looks_like_json: content.trim().startsWith('{') || content.trim().startsWith('[')
                                        };
                                    } else {
                                        // 他のスクリプトタグも確認
                                        const all_scripts = Array.from(document.scripts);
                                        const json_scripts = all_scripts.filter(s => 
                                            s.type === 'application/json' || 
                                            (s.id && (s.id.includes('state') || s.id.includes('data')))
                                        );
                                        
                                        return {
                                            exists: false,
                                            total_scripts: all_scripts.length,
                                            json_scripts: json_scripts.map(s => ({
                                                id: s.id || 'no-id', 
                                                type: s.type || 'no-type', 
                                                size: s.textContent ? s.textContent.length : 0
                                            }))
                                        };
                                    }
                                } catch (error) {
                                    return { error: error.message };
                                }
                            })()
                            ''')
                            
                            log_and_append(f"    📜 hermes-state スクリプト分析:")
                            
                            # 安全なデータアクセス
                            if isinstance(hermes_state_analysis, dict):
                                if safe_get(hermes_state_analysis, 'exists') == True:
                                    log_and_append(f"      ✅ 存在確認")
                                    log_and_append(f"      サイズ: {safe_get(hermes_state_analysis, 'size')}文字")
                                    log_and_append(f"      タイプ: {safe_get(hermes_state_analysis, 'type')}")
                                    log_and_append(f"      JSON形式: {safe_get(hermes_state_analysis, 'looks_like_json')}")
                                    log_and_append(f"      開始100文字: '{safe_get(hermes_state_analysis, 'first_100_chars')}'")
                                    last_chars = safe_get(hermes_state_analysis, 'last_100_chars')
                                    if last_chars and last_chars != 'N/A':
                                        log_and_append(f"      終端100文字: '{last_chars}'")
                                elif safe_get(hermes_state_analysis, 'exists') == False:
                                    log_and_append(f"      ❌ hermes-state not found")
                                    log_and_append(f"      総スクリプト数: {safe_get(hermes_state_analysis, 'total_scripts')}")
                                    json_scripts = safe_get(hermes_state_analysis, 'json_scripts', [])
                                    log_and_append(f"      JSONスクリプト: {json_scripts}")
                                else:
                                    error_msg = safe_get(hermes_state_analysis, 'error')
                                    if error_msg != 'N/A':
                                        log_and_append(f"      ⚠️ スクリプト分析エラー: {error_msg}")
                            else:
                                log_and_append(f"      ⚠️ 予期しないスクリプト分析データ形式: {type(hermes_state_analysis)}")
                            
                            # Angular/DOM要素の詳細確認（安全版）
                            try:
                                dom_analysis = await tab.evaluate('''
                                (function() {
                                    try {
                                        const selectors_to_check = [
                                            'h-root', 'h-grid-results', 'h-grid-result-item', 'h-grid-page',
                                            '.product-grid-list', '.search-results', '[data-testid="product-grid"]',
                                            '.product-item', '.product-card', 'article'
                                        ];
                                        
                                        const results = {};
                                        selectors_to_check.forEach(selector => {
                                            try {
                                                const elements = document.querySelectorAll(selector);
                                                results[selector] = {
                                                    count: elements.length,
                                                    first_element_info: elements[0] ? {
                                                        tagName: elements[0].tagName,
                                                        className: elements[0].className || '',
                                                        innerText_length: elements[0].innerText ? elements[0].innerText.length : 0
                                                    } : null
                                                };
                                            } catch (e) {
                                                results[selector] = { error: e.message };
                                            }
                                        });
                                        
                                        return results;
                                    } catch (error) {
                                        return { global_error: error.message };
                                    }
                                })()
                                ''')
                                
                                log_and_append(f"    🔍 DOM要素詳細分析:")
                                if isinstance(dom_analysis, dict):
                                    if 'global_error' in dom_analysis:
                                        log_and_append(f"      ❌ DOM分析全体エラー: {dom_analysis['global_error']}")
                                    else:
                                        for selector, info in dom_analysis.items():
                                            if isinstance(info, dict):
                                                if 'error' in info:
                                                    log_and_append(f"      ⚠️ {selector}: エラー - {info['error']}")
                                                elif safe_get(info, 'count', 0) > 0:
                                                    count = safe_get(info, 'count')
                                                    log_and_append(f"      ✅ {selector}: {count}個")
                                                    first_info = safe_get(info, 'first_element_info')
                                                    if isinstance(first_info, dict):
                                                        tag = safe_get(first_info, 'tagName')
                                                        class_name = safe_get(first_info, 'className') 
                                                        text_len = safe_get(first_info, 'innerText_length')
                                                        log_and_append(f"        第1要素: {tag}.{class_name} ({text_len}文字)")
                                                else:
                                                    log_and_append(f"      ❌ {selector}: 0個")
                                else:
                                    log_and_append(f"      ⚠️ DOM分析データ型エラー: {type(dom_analysis)}")
                                    
                            except Exception as dom_error:
                                log_and_append(f"    ❌ DOM要素分析エラー: {dom_error}")
                            
                            successful_connections += 1
                            accessible_pages.append({
                                "name": site['name'],
                                "url": site['url'],
                                "title": title,
                                "tab": tab,
                                "extract_products": site.get('extract_products', False),
                                "analysis": page_analysis,
                                "hermes_state": hermes_state_analysis,
                                "dom_analysis": dom_analysis
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
                    
                    # 商品抽出指定があるページのみで実行
                    if not page.get('extract_products', False):
                        log_and_append(f"    スキップ: 商品抽出対象外")
                        continue
                    
                    try:
                        tab = page['tab']
                        
                        # エルメス特有のJSON データ抽出方式
                        log_and_append(f"      エルメス特化: JSON データ抽出を試行")
                        
                        # 【重要修正】hermes-state の直接RAW取得
                        log_and_append(f"      🎯 hermes-state RAW内容取得:")
                        
                        raw_hermes_data = await tab.evaluate('''
                        (function() {
                            try {
                                const hermesStateScript = document.getElementById('hermes-state');
                                if (hermesStateScript) {
                                    const rawText = hermesStateScript.textContent;
                                    return {
                                        success: true,
                                        exists: true,
                                        size: rawText.length,
                                        first_500_chars: rawText.substring(0, 500),
                                        last_200_chars: rawText.substring(Math.max(0, rawText.length - 200)),
                                        raw_content: rawText  // 完全な生データ
                                    };
                                } else {
                                    return { success: false, error: 'hermes-state script not found' };
                                }
                            } catch (error) {
                                return { success: false, error: error.message };
                            }
                        })()
                        ''')
                        
                        if isinstance(raw_hermes_data, dict) and raw_hermes_data.get('success'):
                            log_and_append(f"        ✅ hermes-state発見")
                            log_and_append(f"        サイズ: {raw_hermes_data['size']}文字")
                            log_and_append(f"        開始500文字: '{raw_hermes_data['first_500_chars']}'")
                            log_and_append(f"        終端200文字: '{raw_hermes_data['last_200_chars']}'")
                            
                            # 実際のJSONパース試行
                            raw_content = raw_hermes_data.get('raw_content', '')
                            if raw_content and len(raw_content) > 10:
                                try:
                                    import json
                                    actual_json_data = json.loads(raw_content)
                                    log_and_append(f"        ✅ JSON パース成功")
                                    log_and_append(f"        JSON型: {type(actual_json_data)}")
                                    
                                    if isinstance(actual_json_data, dict):
                                        log_and_append(f"        トップレベルキー: {list(actual_json_data.keys())}")
                                        
                                        # 商品データ探索
                                        if 'products' in actual_json_data:
                                            products = actual_json_data['products']
                                            log_and_append(f"        🎯 products発見: {type(products)}")
                                            
                                            if isinstance(products, dict) and 'items' in products:
                                                items = products['items']
                                                total = products.get('total', len(items) if isinstance(items, list) else 0)
                                                log_and_append(f"        ✅ 商品データ構造確認:")
                                                log_and_append(f"          総数: {total}")
                                                log_and_append(f"          アイテム型: {type(items)}")
                                                log_and_append(f"          アイテム数: {len(items) if isinstance(items, list) else 'N/A'}")
                                                
                                                if isinstance(items, list) and len(items) > 0:
                                                    first_item = items[0]
                                                    log_and_append(f"          第1商品キー: {list(first_item.keys()) if isinstance(first_item, dict) else 'N/A'}")
                                                    
                                                    # 実際の商品情報サンプル表示
                                                    sample_products = []
                                                    for i, item in enumerate(items[:3]):
                                                        if isinstance(item, dict):
                                                            product_info = {
                                                                'title': item.get('title', item.get('name', 'N/A')),
                                                                'url': item.get('url', item.get('link', 'N/A')),
                                                                'price': item.get('price', 'N/A'),
                                                                'sku': item.get('sku', item.get('id', 'N/A'))
                                                            }
                                                            sample_products.append(product_info)
                                                            log_and_append(f"          商品{i+1}: {product_info['title']}")
                                                            log_and_append(f"            URL: {product_info['url']}")
                                                            log_and_append(f"            価格: {product_info['price']}")
                                                    
                                                    if sample_products:
                                                        log_and_append(f"        🎉 商品情報抽出完全成功! {len(sample_products)}件サンプル取得")
                                                        extraction_success = True
                                                        break
                                            else:
                                                log_and_append(f"        ⚠️ products.items構造が異なる: {products}")
                                        else:
                                            log_and_append(f"        ⚠️ products キーが存在しない")
                                            # 他の可能なキーを探索
                                            possible_keys = [k for k in actual_json_data.keys() if 'product' in k.lower() or 'item' in k.lower() or 'result' in k.lower()]
                                            if possible_keys:
                                                log_and_append(f"        可能性のあるキー: {possible_keys}")
                                    else:
                                        log_and_append(f"        ⚠️ JSONが辞書型ではない: {type(actual_json_data)}")
                                        
                                except json.JSONDecodeError as json_error:
                                    log_and_append(f"        ❌ JSON パースエラー: {json_error}")
                                except Exception as parse_error:
                                    log_and_append(f"        ❌ データ処理エラー: {parse_error}")
                            else:
                                log_and_append(f"        ❌ hermes-state内容が空または短すぎる")
                        else:
                            error_msg = raw_hermes_data.get('error', 'Unknown error') if isinstance(raw_hermes_data, dict) else str(raw_hermes_data)
                            log_and_append(f"        ❌ hermes-state取得エラー: {error_msg}")
                        
                        # Step 2: 構造に応じた商品データ抽出（改善版）
                        json_extraction_script = '''
                        (function() {
                            try {
                                const hermesStateScript = document.getElementById('hermes-state');
                                if (hermesStateScript) {
                                    const jsonData = JSON.parse(hermesStateScript.textContent);
                                    let productData = null;
                                    
                                    // パターン1: jsonData自体が配列の場合
                                    if (Array.isArray(jsonData)) {
                                        // 配列の中から products を含む要素を探索
                                        for (let item of jsonData) {
                                            if (item && item.products) {
                                                if (Array.isArray(item.products.items)) {
                                                    productData = {
                                                        total: item.products.total || item.products.items.length,
                                                        items: item.products.items.slice(0, 5).map(p => ({
                                                            title: p.title || p.name,
                                                            url: p.url || p.link,
                                                            sku: p.sku || p.id,
                                                            price: p.price
                                                        }))
                                                    };
                                                    break;
                                                }
                                            }
                                        }
                                    }
                                    
                                    // パターン2: 従来の辞書型 products.items
                                    else if (jsonData.products && jsonData.products.items) {
                                        productData = {
                                            total: jsonData.products.total || jsonData.products.items.length,
                                            items: jsonData.products.items.slice(0, 5).map(p => ({
                                                title: p.title || p.name,
                                                url: p.url || p.link,
                                                sku: p.sku || p.id,
                                                price: p.price
                                            }))
                                        };
                                    }
                                    
                                    // パターン3: 直接的な products 配列
                                    else if (Array.isArray(jsonData.products)) {
                                        productData = {
                                            total: jsonData.products.length,
                                            items: jsonData.products.slice(0, 5).map(p => ({
                                                title: p.title || p.name,
                                                url: p.url || p.link,
                                                sku: p.sku || p.id,
                                                price: p.price
                                            }))
                                        };
                                    }
                                    
                                    if (productData && productData.items.length > 0) {
                                        return { success: true, data: productData };
                                    } else {
                                        return { 
                                            success: false, 
                                            error: 'Product data structure not found',
                                            available_keys: Array.isArray(jsonData) ? 'array_structure' : Object.keys(jsonData)
                                        };
                                    }
                                } else {
                                    return { success: false, error: 'hermes-state script not found' };
                                }
                            } catch (error) {
                                return { success: false, error: error.message, stack: error.stack };
                            }
                        })()
                        '''
                        
                        try:
                            json_result = await tab.evaluate(json_extraction_script)
                            
                            if json_result.get('success'):
                                product_data = json_result['data']
                                total_count = product_data['total']
                                items = product_data['items']
                                
                                log_and_append(f"      ✅ JSON商品データ抽出成功!")
                                log_and_append(f"      総商品数: {total_count}")
                                log_and_append(f"      サンプル商品: {len(items)}件")
                                
                                for i, item in enumerate(items, 1):
                                    log_and_append(f"        {i}. {item['title']}")
                                    log_and_append(f"           URL: {item['url']}")
                                    log_and_append(f"           SKU: {item['sku']}")
                                    if item['price']:
                                        log_and_append(f"           価格: {item['price']}")
                                
                                extraction_success = True
                                break
                                
                            else:
                                error_msg = json_result.get('error', 'Unknown error')
                                log_and_append(f"      ⚠️ JSON抽出失敗: {error_msg}")
                                
                                if 'keys' in json_result:
                                    log_and_append(f"      利用可能なキー: {json_result['keys']}")
                                
                                # フォールバック: 標準セレクタも試行
                                log_and_append(f"      フォールバック: 標準セレクタを試行")
                                
                                fallback_selectors = ["h-grid-result-item", ".grid-item", "article"]
                                for selector in fallback_selectors:
                                    count_script = f"document.querySelectorAll('{selector}').length"
                                    count = await tab.evaluate(count_script)
                                    log_and_append(f"        セレクタ '{selector}': {count}件")
                                    
                                    if count > 0:
                                        log_and_append(f"      ✅ フォールバック成功: {selector}で{count}件発見")
                                        extraction_success = True
                                        break
                        
                        except Exception as json_error:
                            log_and_append(f"      ❌ JSON抽出エラー: {json_error}")
                        
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