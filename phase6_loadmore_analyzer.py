"""
Phase 6 改善: 「アイテムをもっと見る」ボタンの技術調査スクリプト
"""

import asyncio
import sys
import os
from datetime import datetime
import traceback
import json
import time

# nodriverインポート
try:
    import nodriver as nd
    import nest_asyncio
    nest_asyncio.apply()
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

async def analyze_loadmore_button():
    """「アイテムをもっと見る」ボタンの詳細な技術分析"""
    
    browser = None
    
    try:
        print("=== Phase 6 改善: Load Moreボタン技術調査 ===")
        print(f"実行時刻: {datetime.now()}")
        print("")
        
        # ブラウザ起動
        print("1. ブラウザ起動中...")
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
        print("✅ ブラウザ起動成功")
        print("")
        
        # エルメスサイトにアクセス
        url = "https://www.hermes.com/jp/ja/search/?s=%E3%83%90%E3%83%83%E3%82%B0#"
        print(f"2. エルメスサイトアクセス: {url}")
        
        tab = await browser.get(url)
        print("✅ ページアクセス成功")
        
        # 初期レンダリング待機
        print("\n3. 初期レンダリング待機中...")
        await asyncio.sleep(10)
        
        # 初期商品数の確認
        print("\n4. 初期状態の分析")
        initial_analysis = await tab.evaluate('''
        (function() {
            const analysis = {
                // 商品数
                product_count: document.querySelectorAll('h-grid-result-item').length,
                
                // Load Moreボタンの検出
                loadmore_button: null,
                
                // 総商品数
                total_products: null,
                
                // ページネーション情報
                pagination_info: {}
            };
            
            // Load Moreボタンを探す（複数の方法）
            const button_selectors = [
                'button[data-testid="Load more items"]',
                'button[name="undefined"]',
                'h-call-to-action button',
                'button:contains("アイテムをもっと見る")',
                'button.button-secondary'
            ];
            
            for (let selector of button_selectors) {
                try {
                    let button;
                    if (selector.includes(':contains')) {
                        // テキストで検索
                        const buttons = document.querySelectorAll('button');
                        button = Array.from(buttons).find(b => b.textContent.includes('アイテムをもっと見る'));
                    } else {
                        button = document.querySelector(selector);
                    }
                    
                    if (button) {
                        analysis.loadmore_button = {
                            found: true,
                            selector: selector,
                            text: button.textContent.trim(),
                            visible: button.offsetParent !== null,
                            disabled: button.disabled || button.getAttribute('aria-disabled') === 'true',
                            classes: button.className,
                            parent_tag: button.parentElement ? button.parentElement.tagName : null,
                            onclick: button.onclick ? 'has onclick' : 'no onclick',
                            attributes: {}
                        };
                        
                        // 属性を収集
                        for (let attr of button.attributes) {
                            analysis.loadmore_button.attributes[attr.name] = attr.value;
                        }
                        
                        break;
                    }
                } catch (e) {
                    console.error('Button search error:', e);
                }
            }
            
            // 総商品数を取得
            const totalElement = document.querySelector('[data-testid="number-current-result"], span.header-title-current-number-result');
            if (totalElement) {
                const match = totalElement.textContent.match(/\\((\\d+)\\)/);
                if (match) {
                    analysis.total_products = parseInt(match[1]);
                }
            }
            
            // Angular/イベントリスナー情報
            if (analysis.loadmore_button && analysis.loadmore_button.found) {
                const button = document.querySelector(analysis.loadmore_button.selector);
                if (button) {
                    // イベントリスナーを確認
                    const listeners = getEventListeners ? getEventListeners(button) : {};
                    analysis.loadmore_button.event_listeners = Object.keys(listeners);
                    
                    // Angular情報を確認
                    analysis.loadmore_button.angular_info = {
                        has_ng_click: button.hasAttribute('ng-click'),
                        has_ng_bind: button.hasAttribute('ng-bind'),
                        _ngcontent: Array.from(button.attributes).some(attr => attr.name.startsWith('_ngcontent')),
                        _nghost: Array.from(button.attributes).some(attr => attr.name.startsWith('_nghost'))
                    };
                }
            }
            
            // ネットワーク監視準備のための情報
            analysis.window_info = {
                has_angular: !!window.angular || !!window.ng,
                has_zone: !!window.Zone,
                location: window.location.href,
                scroll_height: document.body.scrollHeight,
                client_height: document.documentElement.clientHeight
            };
            
            return analysis;
        })()
        ''')
        
        print("\n初期状態分析結果:")
        print(f"- 表示商品数: {initial_analysis.get('product_count', 0)}個")
        print(f"- 総商品数: {initial_analysis.get('total_products', 'N/A')}個")
        
        if initial_analysis.get('loadmore_button') and initial_analysis['loadmore_button'].get('found'):
            btn_info = initial_analysis['loadmore_button']
            print(f"\n✅ Load Moreボタン発見:")
            print(f"  - セレクタ: {btn_info.get('selector')}")
            print(f"  - テキスト: {btn_info.get('text')}")
            print(f"  - 表示状態: {'表示' if btn_info.get('visible') else '非表示'}")
            print(f"  - 無効状態: {'無効' if btn_info.get('disabled') else '有効'}")
            print(f"  - クラス: {btn_info.get('classes')}")
            print(f"  - 親要素: {btn_info.get('parent_tag')}")
            print(f"  - Angular属性: {btn_info.get('angular_info')}")
            print(f"  - 属性一覧:")
            for attr_name, attr_value in btn_info.get('attributes', {}).items():
                print(f"    - {attr_name}: {attr_value}")
        else:
            print("\n❌ Load Moreボタンが見つかりません")
        
        # ボタンクリック前のネットワーク監視設定
        print("\n5. ネットワーク監視の準備")
        
        # Performance APIを使用したネットワーク監視
        await tab.evaluate('''
        window.networkRequests = [];
        window.originalFetch = window.fetch;
        window.fetch = function(...args) {
            const startTime = performance.now();
            const request = {
                url: args[0],
                method: args[1]?.method || 'GET',
                startTime: startTime,
                timestamp: new Date().toISOString()
            };
            
            return window.originalFetch.apply(this, args).then(response => {
                request.endTime = performance.now();
                request.duration = request.endTime - request.startTime;
                request.status = response.status;
                request.ok = response.ok;
                window.networkRequests.push(request);
                return response;
            });
        };
        ''')
        print("✅ ネットワーク監視開始")
        
        # Load Moreボタンをクリック
        if initial_analysis.get('loadmore_button') and initial_analysis['loadmore_button'].get('found'):
            print("\n6. Load Moreボタンクリック実験")
            
            try:
                # クリック前の状態を記録
                pre_click_state = await tab.evaluate('''
                (function() {
                    return {
                        product_count: document.querySelectorAll('h-grid-result-item').length,
                        scroll_height: document.body.scrollHeight,
                        button_text: document.querySelector('button[data-testid="Load more items"]')?.textContent.trim()
                    };
                })()
                ''')
                
                print(f"クリック前: 商品数={pre_click_state['product_count']}, スクロール高さ={pre_click_state['scroll_height']}")
                
                # ボタンクリック
                click_result = await tab.evaluate('''
                (function() {
                    const button = document.querySelector('button[data-testid="Load more items"]');
                    if (button && !button.disabled) {
                        button.click();
                        return { clicked: true, button_found: true };
                    }
                    return { clicked: false, button_found: !!button, disabled: button?.disabled };
                })()
                ''')
                
                if click_result.get('clicked'):
                    print("✅ ボタンクリック成功")
                    
                    # クリック後の変化を監視
                    print("\n7. クリック後の変化を監視中...")
                    
                    for i in range(10):  # 10秒間監視
                        await asyncio.sleep(1)
                        
                        post_click_state = await tab.evaluate('''
                        (function() {
                            const button = document.querySelector('button[data-testid="Load more items"]');
                            return {
                                product_count: document.querySelectorAll('h-grid-result-item').length,
                                scroll_height: document.body.scrollHeight,
                                button_exists: !!button,
                                button_visible: button ? button.offsetParent !== null : false,
                                button_text: button?.textContent.trim(),
                                loading_indicator: !!document.querySelector('.loading, .spinner, [class*="loading"]'),
                                network_requests: window.networkRequests.length
                            };
                        })()
                        ''')
                        
                        print(f"  {i+1}秒後: 商品数={post_click_state['product_count']}, "
                              f"スクロール高さ={post_click_state['scroll_height']}, "
                              f"ボタン={'表示' if post_click_state['button_visible'] else '非表示/削除'}, "
                              f"ネットワーク要求={post_click_state['network_requests']}")
                        
                        # 商品数が増えたら詳細を記録
                        if post_click_state['product_count'] > pre_click_state['product_count']:
                            print(f"\n  ✅ 商品が追加されました: {pre_click_state['product_count']} → {post_click_state['product_count']}")
                            break
                    
                    # ネットワーク要求の詳細
                    network_details = await tab.evaluate('window.networkRequests')
                    if network_details:
                        print(f"\n8. ネットワーク要求の詳細 ({len(network_details)}件):")
                        for req in network_details[-5:]:  # 最新5件のみ表示
                            print(f"  - {req.get('method')} {req.get('url')[:80]}...")
                            print(f"    状態: {req.get('status')}, 時間: {req.get('duration', 0):.0f}ms")
                    
                else:
                    print(f"❌ ボタンクリック失敗: found={click_result.get('button_found')}, disabled={click_result.get('disabled')}")
            
            except Exception as click_error:
                print(f"❌ クリック実験エラー: {click_error}")
        
        # 最終的な分析
        print("\n9. 技術的な推奨事項:")
        print("- ボタンクリック後、新しい商品の読み込みを待つ必要がある")
        print("- ネットワーク要求の完了を監視する")
        print("- DOM変更（商品数の増加）を検出する")
        print("- ボタンの表示/非表示状態を確認する")
        print("- セキュリティ検出を避けるため、人間らしい待機時間を設ける")
        
        # HTMLを保存
        full_html = await tab.evaluate('document.documentElement.outerHTML')
        with open('loadmore_analysis.html', 'w', encoding='utf-8') as f:
            f.write(full_html)
        print(f"\n✅ 分析用HTMLを loadmore_analysis.html に保存")
        
    except Exception as e:
        print(f"\n❌ エラー発生: {type(e).__name__}: {e}")
        traceback.print_exc()
    
    finally:
        if browser:
            try:
                await browser.stop()
                print("\n✅ ブラウザを終了しました")
            except:
                pass

# メイン実行
if __name__ == "__main__":
    asyncio.run(analyze_loadmore_button())