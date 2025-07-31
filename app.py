import sys
import os
import asyncio
import gradio as gr
from datetime import datetime
import traceback
import json
import time

def normalize_nodriver_result(result):
    """nodriverが返す特殊なリスト形式を辞書形式に変換"""
    if isinstance(result, list):
        try:
            normalized = {}
            for item in result:
                if isinstance(item, list) and len(item) == 2:
                    key = item[0]
                    value_info = item[1]
                    if isinstance(value_info, dict) and 'value' in value_info:
                        normalized[key] = value_info['value']
                    else:
                        normalized[key] = value_info
            return normalized if normalized else result
        except Exception:
            return result
    return result

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
    
    log_and_append("=== Phase 6: エルメスサイト特化テスト (v2025.01.31) ===")
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
                    "name": "エルメスバッグ検索ページ（HTML直接解析テスト）",
                    "url": "https://www.hermes.com/jp/ja/search/?s=%E3%83%90%E3%83%83%E3%82%B0#",
                    "timeout": 45,
                    "extract_products": True
                }
            ]
            
            nonlocal successful_connections  # 外側スコープの変数を使用
            nonlocal extraction_success  # 外側スコープの変数を使用
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
                                element_exists_raw = await tab.evaluate(f'document.querySelector("{selector}") ? true : false')
                                element_exists = normalize_nodriver_result(element_exists_raw)
                                if isinstance(element_exists, dict):
                                    element_exists = element_exists.get('exists', element_exists.get('value', False))
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
                        title_raw = await tab.evaluate('document.title')
                        title = normalize_nodriver_result(title_raw)
                        if isinstance(title, dict):
                            title = title.get('title', title.get('value', str(title_raw)))
                        log_and_append(f"    ページタイトル: '{title}'")
                        
                        # ページURL確認
                        current_url_raw = await tab.evaluate('window.location.href')
                        current_url = normalize_nodriver_result(current_url_raw)
                        if isinstance(current_url, dict):
                            current_url = current_url.get('href', current_url.get('value', str(current_url_raw)))
                        log_and_append(f"    現在URL: {current_url}")
                        
                        # Redirect確認
                        original_url = site['url']
                        if current_url != original_url:
                            log_and_append(f"    🔄 リダイレクト検出:")
                            log_and_append(f"      元URL: {original_url}")
                            log_and_append(f"      現URL: {current_url}")
                        
                        # 基本的なページ要素確認
                        body_exists_raw = await tab.evaluate('document.body ? true : false')
                        body_exists = normalize_nodriver_result(body_exists_raw)
                        if isinstance(body_exists, dict):
                            body_exists = body_exists.get('value', body_exists_raw)
                        log_and_append(f"    Body要素: {'存在' if body_exists else '不存在'}")
                        
                        if body_exists:
                            # 【詳細ロギング】ページコンテンツ分析
                            page_analysis_raw = await tab.evaluate('''
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
                            
                            # nodriverの戻り値を正規化
                            page_analysis = normalize_nodriver_result(page_analysis_raw)
                            
                            # nodriverの戻り値を安全に処理
                            def safe_get(data, key, default='N/A'):
                                """nodriverの戻り値から安全にデータを取得"""
                                try:
                                    if isinstance(data, dict):
                                        return data.get(key, default)
                                    elif isinstance(data, list) and len(data) > 0:
                                        # nodriverが配列で返す場合の処理
                                        for item in data:
                                            if isinstance(item, list) and len(item) == 2:
                                                # ['key', {'value': xxx}] 形式
                                                if item[0] == key:
                                                    value_info = item[1]
                                                    if isinstance(value_info, dict) and 'value' in value_info:
                                                        return value_info['value']
                                                    else:
                                                        return value_info
                                            elif isinstance(item, dict) and key in item:
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
                            hermes_state_analysis_raw = await tab.evaluate('''
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
                            
                            # nodriverの戻り値を正規化
                            hermes_state_analysis = normalize_nodriver_result(hermes_state_analysis_raw)
                            
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
                                dom_analysis_raw = await tab.evaluate('''
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
                                
                                # nodriverの戻り値を正規化
                                dom_analysis = normalize_nodriver_result(dom_analysis_raw)
                                
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
                
                # extraction_success は外側スコープから参照
                
                for page in accessible_pages:
                    log_and_append(f"    対象ページ: {page['name']}")
                    
                    # 商品抽出指定があるページのみで実行
                    if not page.get('extract_products', False):
                        log_and_append(f"    スキップ: 商品抽出対象外")
                        continue
                    
                    try:
                        tab = page['tab']
                        
                        # 完全なHTMLをダウンロード
                        log_and_append(f"      📥 完全なHTMLダウンロード開始")
                        
                        # ページの完全なHTMLを取得（SaveAs相当）
                        # まずページが完全に読み込まれるまで待機
                        log_and_append("      ⏳ ページ完全読み込み待機中...")
                        await asyncio.sleep(5)  # 追加待機
                        
                        # JavaScriptを使用してレンダリング後のHTMLを取得
                        try:
                            # 方法1: XMLSerializerを使用
                            full_html_raw = await tab.evaluate('''
                                (() => {
                                    const serializer = new XMLSerializer();
                                    return serializer.serializeToString(document);
                                })()
                            ''')
                            full_html = normalize_nodriver_result(full_html_raw)
                            
                            # HTMLが辞書形式の場合、値を取得
                            if isinstance(full_html, dict):
                                full_html = full_html.get('html', full_html.get('value', str(full_html)))
                            
                            # まだ空の場合、方法2を試す
                            if not full_html or len(str(full_html)) < 1000:
                                log_and_append("      ⏳ 別方式でHTML取得中...")
                                full_html_raw2 = await tab.evaluate('''
                                    document.documentElement.outerHTML
                                ''')
                                full_html2 = normalize_nodriver_result(full_html_raw2)
                                if isinstance(full_html2, dict):
                                    full_html2 = full_html2.get('value', str(full_html2))
                                if full_html2 and len(str(full_html2)) > len(str(full_html)):
                                    full_html = full_html2
                            
                            # 確実に文字列にする
                            if not isinstance(full_html, str):
                                full_html = str(full_html) if full_html else ""
                                
                        except Exception as html_error:
                            log_and_append(f"      ⚠️ HTML取得エラー: {html_error}")
                            full_html = ""
                        
                        # HTMLをファイルに保存
                        import os
                        html_filename = 'hermes_page.html'
                        with open(html_filename, 'w', encoding='utf-8') as f:
                            f.write(full_html)
                        log_and_append(f"      ✅ HTMLを {html_filename} に保存 ({len(full_html):,} bytes)")
                        
                        # まずHTMLからhermes-state JSONを抽出して解析
                        log_and_append("      🔍 hermes-state JSONを解析中...")
                        
                        try:
                            # 保存したHTMLからhermes-stateを抽出
                            import re
                            hermes_state_match = re.search(r'<script id="hermes-state" type="application/json">(.*?)</script>', full_html, re.DOTALL)
                            
                            if hermes_state_match:
                                hermes_state_json = hermes_state_match.group(1)
                                log_and_append(f"      ✅ hermes-state JSONを発見 ({len(hermes_state_json):,} bytes)")
                                
                                # JSONをパース
                                import json
                                hermes_data = json.loads(hermes_state_json)
                                
                                # 商品データを探索
                                products_found = False
                                total_count = 0
                                product_items = []
                                
                                # データ構造を探索
                                for key, value in hermes_data.items():
                                    if isinstance(value, dict):
                                        # b.totalとb.productsを探す
                                        if 'b' in value and isinstance(value['b'], dict):
                                            b_data = value['b']
                                            if 'total' in b_data:
                                                total_count = b_data['total']
                                                log_and_append(f"      ✅ 総商品数を発見: {total_count}件")
                                            
                                            if 'products' in b_data and isinstance(b_data['products'], dict):
                                                if 'items' in b_data['products'] and isinstance(b_data['products']['items'], list):
                                                    product_items = b_data['products']['items']
                                                    log_and_append(f"      ✅ 商品リストを発見: {len(product_items)}件")
                                                    products_found = True
                                                    break
                                
                                if products_found and len(product_items) > 0:
                                    # 商品データを整形
                                    items = []
                                    for idx, product in enumerate(product_items[:100], 1):  # 最大100件
                                        item = {
                                            'index': idx,
                                            'title': product.get('title', 'N/A'),
                                            'url': product.get('url', 'N/A'),
                                            'sku': product.get('sku', 'N/A'),
                                            'price': product.get('price', 'N/A'),
                                            'color': product.get('mainColor', {}).get('name', '') if isinstance(product.get('mainColor'), dict) else ''
                                        }
                                        items.append(item)
                                    
                                    # 成功データを返す
                                    html_result = {
                                        'success': True,
                                        'data': {
                                            'total': total_count,
                                            'extracted': len(items),
                                            'items': items
                                        }
                                    }
                                else:
                                    html_result = {
                                        'success': False,
                                        'error': 'No products found in hermes-state JSON',
                                        'debug': {
                                            'totalElement': total_count > 0,
                                            'productElements': len(product_items)
                                        }
                                    }
                            else:
                                log_and_append("      ⚠️ hermes-state JSONが見つかりません")
                                # フォールバック: JavaScriptでDOMから抽出
                                html_extraction_script = '''
                        (function() {
                            try {
                                // 総商品数を取得
                                const totalElement = document.querySelector('[data-testid="number-current-result"]');
                                const totalMatch = totalElement ? totalElement.textContent.match(/\\((\\d+)\\)/) : null;
                                const total = totalMatch ? parseInt(totalMatch[1]) : 0;
                                
                                // 商品要素を取得
                                const productElements = document.querySelectorAll('h-grid-result-item, .product-grid-list-item');
                                const products = [];
                                
                                productElements.forEach((element, index) => {
                                    // 全件処理（制限なし）
                                    
                                    // 商品リンク要素を探す（複数のセレクタを試す）
                                    const linkElement = element.querySelector('a.product-item-name, a[class*="product"], a[href*="/product/"]');
                                    if (!linkElement) return;
                                    
                                    // 商品名
                                    const titleElement = linkElement.querySelector('.product-title');
                                    const title = titleElement ? titleElement.textContent.trim() : 'N/A';
                                    
                                    // URL
                                    const url = linkElement.href || linkElement.getAttribute('href') || 'N/A';
                                    
                                    // SKU（商品ID）
                                    const sku = linkElement.id ? linkElement.id.replace('product-item-meta-link-', '') : 'N/A';
                                    
                                    // 価格を探す
                                    const priceElement = element.querySelector('.price, [class*="price"]');
                                    const price = priceElement ? priceElement.textContent.trim() : 'N/A';
                                    
                                    // カラー情報（オプション）
                                    const colorElement = element.querySelector('.product-item-color');
                                    const color = colorElement ? colorElement.textContent.trim() : '';
                                    
                                    products.push({
                                        title: title,
                                        url: url,
                                        sku: sku,
                                        price: price,
                                        color: color,
                                        index: index + 1
                                    });
                                });
                                
                                if (products.length > 0) {
                                    return {
                                        success: true,
                                        data: {
                                            total: total,
                                            extracted: products.length,
                                            items: products
                                        }
                                    };
                                } else {
                                    // デバッグ用: 要素の検索状況
                                    const debugInfo = {
                                        totalElement: !!totalElement,
                                        productElements: productElements.length,
                                        firstElementHTML: productElements[0] ? productElements[0].outerHTML.substring(0, 200) : 'N/A'
                                    };
                                    
                                    return {
                                        success: false,
                                        error: 'No products found in HTML',
                                        debug: debugInfo
                                    };
                                }
                            } catch (error) {
                                return { success: false, error: error.message };
                            }
                        })()
                        '''
                        
                                html_result_raw = await tab.evaluate(html_extraction_script)
                                html_result = normalize_nodriver_result(html_result_raw)
                            
                        except json.JSONDecodeError as json_error:
                            log_and_append(f"      ❌ JSONパースエラー: {json_error}")
                            html_result = {'success': False, 'error': f'JSON parse error: {json_error}'}
                        except Exception as extract_error:
                            log_and_append(f"      ❌ hermes-state抽出エラー: {extract_error}")
                            html_result = {'success': False, 'error': f'Extraction error: {extract_error}'}
                            
                        # normalize_nodriver_result関数で既に正規化済み
                        normalized_html_result = html_result
                        
                        if isinstance(normalized_html_result, dict) and normalized_html_result.get('success'):
                            product_data = normalized_html_result.get('data', {})
                            
                            # product_dataがリストの場合の処理
                            if isinstance(product_data, list):
                                log_and_append(f"      ⚠️ product_dataがリスト形式で返されました: {type(product_data)}")
                                # リストから辞書形式のデータを探す
                                for item in product_data:
                                    if isinstance(item, dict) and ('total' in item or 'items' in item):
                                        product_data = item
                                        break
                                else:
                                    # 適切なデータが見つからない場合
                                    product_data = {}
                            
                            # 辞書として安全にアクセス
                            if isinstance(product_data, dict):
                                total_count = product_data.get('total', 0)
                                extracted_count = product_data.get('extracted', 0)
                                items = product_data.get('items', [])
                            else:
                                log_and_append(f"      ⚠️ product_dataの形式が不正: {type(product_data)}")
                                total_count = 0
                                extracted_count = 0
                                items = []
                            
                            # 商品数の検証
                            if extracted_count > 0 and len(items) > 0:
                                log_and_append(f"      ✅ 商品データ抽出成功!")
                                log_and_append(f"      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                                log_and_append(f"      総商品数: {total_count}件")
                                log_and_append(f"      抽出成功: {extracted_count}件")
                                log_and_append(f"      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                                log_and_append("")
                            else:
                                log_and_append(f"      ⚠️ 商品データ抽出失敗: 商品数が0件")
                                log_and_append(f"      総商品数: {total_count}件")
                                log_and_append(f"      抽出成功: {extracted_count}件")
                                log_and_append(f"      アイテム数: {len(items)}件")
                                log_and_append("")
                            
                            # 商品がある場合のみ表示と成功判定
                            if len(items) > 0:
                                # 商品情報を整形して表示
                                for item in items:
                                    title_line = f"      {item['index']:>3}. {item['title']}"
                                    if item.get('color'):
                                        title_line += f" ({item['color']})"
                                    log_and_append(title_line)
                                    
                                    if item.get('price') and item['price'] != 'N/A':
                                        log_and_append(f"          価格: {item['price']}")
                                    log_and_append(f"          URL: {item['url']}")
                                    log_and_append("")  # 商品間の空行
                                
                                extraction_success = True
                            else:
                                extraction_success = False
                            
                            # 商品データを保存（JSON & CSV & TXT）
                            try:
                                # 固定ファイル名（上書き保存）
                                json_filename = "hermes_products.json"
                                csv_filename = "hermes_products.csv"
                                txt_filename = "hermes_products.txt"
                                
                                # JSON形式で保存
                                products_data = {
                                    "total": total_count,
                                    "extracted": extracted_count,
                                    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                                    "products": items
                                }
                                with open(json_filename, 'w', encoding='utf-8') as f:
                                    json.dump(products_data, f, ensure_ascii=False, indent=2)
                                
                                # CSV形式で保存（不要なフィールドを除外）
                                import csv
                                with open(csv_filename, 'w', encoding='utf-8-sig', newline='') as f:
                                    fieldnames = ['index', 'title', 'color', 'price', 'sku', 'url']
                                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                                    writer.writeheader()
                                    
                                    # 各商品データから必要なフィールドのみ抽出
                                    cleaned_items = []
                                    for item in items:
                                        cleaned_item = {
                                            'index': item.get('index', ''),
                                            'title': item.get('title', ''),
                                            'color': item.get('color', ''),
                                            'price': item.get('price', ''),
                                            'sku': item.get('sku', ''),
                                            'url': item.get('url', '')
                                        }
                                        cleaned_items.append(cleaned_item)
                                    
                                    writer.writerows(cleaned_items)
                                
                                # テキスト形式で保存（商品名、URL、総数）
                                with open(txt_filename, 'w', encoding='utf-8') as f:
                                    f.write(f"エルメス商品情報\n")
                                    f.write(f"抽出日時: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                                    f.write(f"総商品数: {total_count}件\n")
                                    f.write(f"抽出成功: {extracted_count}件\n")
                                    f.write("=" * 80 + "\n\n")
                                    
                                    for item in items:
                                        f.write(f"商品 {item.get('index', 'N/A')}/{extracted_count}\n")
                                        f.write(f"商品名: {item.get('title', 'N/A')}\n")
                                        if item.get('color'):
                                            f.write(f"カラー: {item.get('color')}\n")
                                        f.write(f"価格: {item.get('price', 'N/A')}\n")
                                        f.write(f"URL: {item.get('url', 'N/A')}\n")
                                        f.write(f"SKU: {item.get('sku', 'N/A')}\n")
                                        f.write("-" * 40 + "\n\n")
                                
                                log_and_append(f"      💾 データ保存完了:")
                                log_and_append(f"         - HTML: hermes_page.html ({len(full_html):,} bytes)")
                                log_and_append(f"         - JSON: {json_filename}")
                                log_and_append(f"         - CSV: {csv_filename}")
                                log_and_append(f"         - TXT: {txt_filename}")
                            except Exception as save_error:
                                log_and_append(f"      ⚠️ データ保存エラー: {save_error}")
                            
                            break
                            
                        else:
                            if isinstance(normalized_html_result, dict):
                                error_msg = normalized_html_result.get('error', 'Unknown error')
                            else:
                                error_msg = str(normalized_html_result)
                            log_and_append(f"      ⚠️ HTML抽出失敗: {error_msg}")
                            
                            if isinstance(normalized_html_result, dict) and 'debug' in normalized_html_result:
                                debug_info = normalized_html_result['debug']
                                log_and_append(f"      デバッグ情報:")
                                log_and_append(f"        総数要素: {debug_info.get('totalElement', False)}")
                                log_and_append(f"        商品要素数: {debug_info.get('productElements', 0)}")
                                if 'firstElementHTML' in debug_info:
                                    log_and_append(f"        最初の要素: {debug_info['firstElementHTML'][:100]}...")
                                
                                # フォールバック: 標準セレクタも試行
                                log_and_append(f"      フォールバック: 標準セレクタを試行")
                                
                                fallback_selectors = ["h-grid-result-item", ".grid-item", "article"]
                                for selector in fallback_selectors:
                                    count_script = f"document.querySelectorAll('{selector}').length"
                                    count_raw = await tab.evaluate(count_script)
                                    count = normalize_nodriver_result(count_raw)
                                    if isinstance(count, dict):
                                        count = count.get('count', count.get('value', 0))
                                    log_and_append(f"        セレクタ '{selector}': {count}件")
                                    
                                    if count > 0:
                                        log_and_append(f"      ✅ フォールバック成功: {selector}で{count}件発見")
                                        
                                        # フォールバックで商品を発見したら、実際にデータを抽出
                                        log_and_append(f"      📥 フォールバック商品データ抽出開始...")
                                        fallback_script = f'''
                                        (function() {{
                                            const elements = document.querySelectorAll('{selector}');
                                            const products = [];
                                            
                                            elements.forEach((element, index) => {{
                                                // 商品リンクを探す
                                                const linkElement = element.querySelector('a.product-item-name, a[class*="product"], a[href*="/product/"]');
                                                if (!linkElement) return;
                                                
                                                // 商品名
                                                const titleElement = linkElement.querySelector('.product-title');
                                                const title = titleElement ? titleElement.textContent.trim() : 'N/A';
                                                
                                                // URL
                                                const url = linkElement.href || linkElement.getAttribute('href') || 'N/A';
                                                
                                                // SKU
                                                const sku = linkElement.id ? linkElement.id.replace('product-item-meta-link-', '') : 'N/A';
                                                
                                                // 価格
                                                const priceElement = element.querySelector('.price, [class*="price"]');
                                                const price = priceElement ? priceElement.textContent.trim() : 'N/A';
                                                
                                                // カラー
                                                const colorElement = element.querySelector('.product-item-color');
                                                const color = colorElement ? colorElement.textContent.trim() : '';
                                                
                                                products.push({{
                                                    title: title,
                                                    url: url,
                                                    sku: sku,
                                                    price: price,
                                                    color: color,
                                                    index: index + 1
                                                }});
                                            }});
                                            
                                            return {{
                                                total: elements.length,
                                                extracted: products.length,
                                                items: products
                                            }};
                                        }})()
                                        '''
                                        
                                        fallback_result_raw = await tab.evaluate(fallback_script)
                                        fallback_result = normalize_nodriver_result(fallback_result_raw)
                                        
                                        if isinstance(fallback_result, dict) and fallback_result.get('extracted', 0) > 0:
                                            total_count = fallback_result.get('total', 0)
                                            extracted_count = fallback_result.get('extracted', 0)
                                            items = fallback_result.get('items', [])
                                            
                                            log_and_append(f"      ✅ フォールバック抽出成功: {extracted_count}/{total_count}件")
                                            
                                            # 商品データを保存（JSON & CSV & TXT）
                                            try:
                                                # 固定ファイル名（上書き保存）
                                                json_filename = "hermes_products.json"
                                                csv_filename = "hermes_products.csv"
                                                txt_filename = "hermes_products.txt"
                                                
                                                # JSON形式で保存
                                                products_data = {
                                                    "total": total_count,
                                                    "extracted": extracted_count,
                                                    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                                                    "products": items
                                                }
                                                with open(json_filename, 'w', encoding='utf-8') as f:
                                                    json.dump(products_data, f, ensure_ascii=False, indent=2)
                                                
                                                # CSV形式で保存（不要なフィールドを除外）
                                                import csv
                                                with open(csv_filename, 'w', encoding='utf-8-sig', newline='') as f:
                                                    fieldnames = ['index', 'title', 'color', 'price', 'sku', 'url']
                                                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                                                    writer.writeheader()
                                                    
                                                    # 各商品データから必要なフィールドのみ抽出
                                                    cleaned_items = []
                                                    for item in items:
                                                        cleaned_item = {
                                                            'index': item.get('index', ''),
                                                            'title': item.get('title', ''),
                                                            'color': item.get('color', ''),
                                                            'price': item.get('price', ''),
                                                            'sku': item.get('sku', ''),
                                                            'url': item.get('url', '')
                                                        }
                                                        cleaned_items.append(cleaned_item)
                                                    
                                                    writer.writerows(cleaned_items)
                                                
                                                # テキスト形式で保存（商品名、URL、総数）
                                                with open(txt_filename, 'w', encoding='utf-8') as f:
                                                    f.write(f"エルメス商品情報\n")
                                                    f.write(f"抽出日時: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                                                    f.write(f"総商品数: {total_count}件\n")
                                                    f.write(f"抽出成功: {extracted_count}件\n")
                                                    f.write("=" * 80 + "\n\n")
                                                    
                                                    for item in items:
                                                        f.write(f"商品 {item.get('index', 'N/A')}/{extracted_count}\n")
                                                        f.write(f"商品名: {item.get('title', 'N/A')}\n")
                                                        if item.get('color'):
                                                            f.write(f"カラー: {item.get('color')}\n")
                                                        f.write(f"価格: {item.get('price', 'N/A')}\n")
                                                        f.write(f"URL: {item.get('url', 'N/A')}\n")
                                                        f.write(f"SKU: {item.get('sku', 'N/A')}\n")
                                                        f.write("-" * 40 + "\n\n")
                                                
                                                log_and_append(f"      💾 フォールバックデータ保存完了:")
                                                log_and_append(f"         - JSON: {json_filename}")
                                                log_and_append(f"         - CSV: {csv_filename}")
                                                log_and_append(f"         - TXT: {txt_filename}")
                                                
                                                extraction_success = True
                                            except Exception as save_error:
                                                log_and_append(f"      ⚠️ フォールバックデータ保存エラー: {save_error}")
                                                extraction_success = False
                                        else:
                                            log_and_append(f"      ❌ フォールバック抽出失敗")
                                            extraction_success = False
                                        
                                        break
                        
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
                # extraction_success は既に False
            
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
                    
                    security_info_raw = await tab.evaluate(security_script)
                    security_info = normalize_nodriver_result(security_info_raw)
                    
                    # nodriverのデータ形式対応
                    normalized_security = security_info
                    
                    log_and_append("    セキュリティ状況:")
                    if isinstance(normalized_security, dict):
                        for key, value in normalized_security.items():
                            status = "🚨" if value else "✅"
                            log_and_append(f"      {status} {key}: {value}")
                        security_checks = normalized_security
                    else:
                        log_and_append(f"      ⚠️ セキュリティ情報の形式エラー: {type(normalized_security)}")
                        security_checks = {}
                    
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
            
            # 成功判定（商品情報の保存が必須）
            hermes_success = extraction_success and successful_connections > 0
            
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
    successful_connections = 0  # グローバルスコープに変数を移動
    extraction_success = False  # グローバルスコープに変数を移動
    
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
        log_and_append("     商品情報の抽出と保存に成功しました")
        phase6_status = "PASSED"
    else:
        log_and_append("  ❌ 失敗: 商品情報の保存ができませんでした")
        if successful_connections > 0:
            log_and_append("     サイト接続は成功しましたが、商品データを抽出できませんでした")
        else:
            log_and_append("     サイト接続自体が失敗しました")
        phase6_status = "FAILED"
    
    log_and_append("")
    log_and_append(f"Phase 6 ステータス: {phase6_status}")
    
    if phase6_status == "PASSED":
        log_and_append("")
        log_and_append("🎉 Phase 6合格！Phase 7に進む準備ができました。")
        log_and_append("ユーザーからの承認をお待ちしています。")
        log_and_append("")
        log_and_append("📋 合格基準:")
        log_and_append("  ✅ エルメスサイトへのアクセス成功")
        log_and_append("  ✅ 商品情報の抽出成功")
        log_and_append("  ✅ 4種類のファイル保存成功（HTML/JSON/CSV/TXT）")
    else:
        log_and_append("")
        log_and_append("❌ Phase 6で問題が発見されました。")
        log_and_append("商品情報の保存ができませんでした。")
        log_and_append("")
        log_and_append("🔍 問題の可能性:")
        log_and_append("  - HTMLの取得方法が不適切")
        log_and_append("  - ページのレンダリング待機時間が不足")
        log_and_append("  - 商品要素のセレクタが変更された")
        log_and_append("  - アンチボット対策による制限")
    
    # 保存されたファイルのリストを表示
    log_and_append("")
    log_and_append("📁 出力ファイル:")
    import glob
    import os
    
    # 各種ファイルの存在確認
    files_to_check = [
        ("hermes_page.html", "完全なHTMLファイル"),
        ("hermes_products.json", "JSON形式の商品データ"),
        ("hermes_products.csv", "CSV形式の商品データ"),
        ("hermes_products.txt", "テキスト形式の商品データ")
    ]
    
    for filename, description in files_to_check:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            log_and_append(f"  ✅ {filename} ({size:,} bytes) - {description}")
        else:
            log_and_append(f"  ❌ {filename} - 未生成")
    
    return "\n".join(results)

# ファイルダウンロード用の関数
def get_downloadable_files():
    """保存されたファイルのリストを返す"""
    import glob
    import os
    files = []
    
    # 固定ファイル名のファイルを確認
    fixed_files = [
        "hermes_page.html",
        "hermes_products.json",
        "hermes_products.csv",
        "hermes_products.txt"
    ]
    
    for filename in fixed_files:
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            files.append(filename)
    
    return files if files else None

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
    
    with gr.Row():
        gr.Markdown("### 📥 デバッグファイルダウンロード")
    
    with gr.Row():
        file_output = gr.File(
            label="ダウンロード可能なファイル（JSON/CSV）",
            file_count="multiple",
            interactive=False
        )
        refresh_btn = gr.Button("🔄 ファイルリスト更新")
    
    def run_test_and_update_files():
        result = test_hermes_site_scraping()
        files = get_downloadable_files()
        return result, files
    
    test_btn.click(
        fn=run_test_and_update_files,
        outputs=[output, file_output]
    )
    
    refresh_btn.click(
        fn=get_downloadable_files,
        outputs=file_output
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