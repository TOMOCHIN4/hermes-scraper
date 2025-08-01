"""
Phase 6.0: Hermesサイトスクレイピング機能
"""
import asyncio
import time
import json
from datetime import datetime
from .utils import create_logger, normalize_nodriver_result, safe_get


class HermesScraper:
    """エルメスサイトのスクレイピングを実行するクラス"""
    
    def __init__(self):
        self.logger = create_logger()
        self.browser = None
        self.results = []
        self.total_items = 0
    
    async def start_browser(self):
        """ブラウザを起動"""
        import nodriver as nd
        import nest_asyncio
        nest_asyncio.apply()
        
        self.logger.log("  Step 1: 特殊ブラウザ設定でnodriver起動")
        
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
        
        self.browser = await nd.start(
            headless=True,
            sandbox=False,
            browser_args=browser_args
        )
        
        self.logger.log(f"    ✅ Browser開始成功: {type(self.browser)}")
        self.logger.log("")
    
    async def close_browser(self):
        """ブラウザを終了"""
        if self.browser:
            try:
                self.logger.log("🧹 ブラウザクリーンアップ開始...")
                # エラーを回避するため、browser.stop()の結果を確認
                if hasattr(self.browser, 'stop') and callable(self.browser.stop):
                    stop_result = self.browser.stop()
                    # awaitableかどうかを確認
                    if hasattr(stop_result, '__await__'):
                        await stop_result
                self.logger.log("✅ ブラウザが正常に終了しました")
            except Exception as e:
                self.logger.log(f"⚠️ ブラウザ終了時の警告: {e}")
                # エラーが発生してもプロセスは継続
    
    async def scrape_hermes_site(self, url="https://www.hermes.com/jp/ja/search/?s=%E3%83%90%E3%83%83%E3%82%B0#"):
        """エルメスサイトをスクレイピング"""
        success = False
        
        try:
            await self.start_browser()
            
            self.logger.log("  Step 2: エルメス公式サイト接続テスト")
            self.logger.log(f"    URL: {url}")
            self.logger.log(f"    ⏳ 接続中 (タイムアウト: 45秒)...")
            
            # ページアクセス
            tab = await asyncio.wait_for(
                self.browser.get(url), 
                timeout=45
            )
            
            if tab is None:
                self.logger.log(f"    ❌ タブ取得失敗")
                return success
            
            self.logger.log(f"    ✅ ページアクセス成功")
            
            # ページ読み込み待機とスクロール処理
            await self._wait_for_page_load(tab)
            await self._scroll_page(tab)
            
            # HTMLダウンロード
            success = await self._download_html(tab)
            
        except asyncio.TimeoutError:
            self.logger.log(f"    ❌ タイムアウト: 45秒以内に接続できませんでした")
        except Exception as e:
            self.logger.log(f"    ❌ 接続エラー: {type(e).__name__}: {str(e)}")
        finally:
            await self.close_browser()
        
        return success
    
    async def _wait_for_page_load(self, tab):
        """ページの読み込みを待機"""
        self.logger.log(f"    ⏳ Angular初期化・商品リスト読み込み待機...")
        
        # 基本待機
        await asyncio.sleep(10)
        
        # 総商品数を取得
        try:
            total_count_raw = await tab.evaluate('''
                (function() {
                    // 複数のパターンで総商品数を検索
                    const patterns = [
                        /(\d+)\s*アイテム/,
                        /(\d+)\s*items?/i,
                        /(\d+)\s*製品/,
                        /(\d+)\s*商品/,
                        /(\d+)\s*results?/i
                    ];
                    
                    // ページ全体のテキストから検索
                    const pageText = document.body.innerText || document.body.textContent || '';
                    
                    for (let pattern of patterns) {
                        const match = pageText.match(pattern);
                        if (match && match[1]) {
                            return {
                                found: true,
                                count: parseInt(match[1]),
                                text: match[0]
                            };
                        }
                    }
                    
                    // h-total-result要素から取得を試行
                    const totalElement = document.querySelector('h-total-result, .total-result, [class*="total"]');
                    if (totalElement) {
                        const text = totalElement.innerText || totalElement.textContent || '';
                        for (let pattern of patterns) {
                            const match = text.match(pattern);
                            if (match && match[1]) {
                                return {
                                    found: true,
                                    count: parseInt(match[1]),
                                    text: match[0],
                                    element: 'h-total-result'
                                };
                            }
                        }
                    }
                    
                    return { found: false };
                })()
            ''')
            
            total_count_info = normalize_nodriver_result(total_count_raw)
            if safe_get(total_count_info, 'found'):
                self.total_items = safe_get(total_count_info, 'count', 0)
                self.logger.log(f"    📊 総商品数を検出: {self.total_items} ({safe_get(total_count_info, 'text')})")
                element_source = safe_get(total_count_info, 'element', None)
                if element_source:
                    self.logger.log(f"    📍 取得元: {element_source}要素")
                else:
                    self.logger.log(f"    📍 取得元: ページ全体のテキスト")
            else:
                self.logger.log(f"    ⚠️ 総商品数を検出できませんでした")
                
        except Exception as e:
            self.logger.log(f"    ⚠️ 総商品数取得エラー: {e}")
        
        # 商品コンテナ要素の出現を待機
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
                self.logger.log(f"      要素待機: {selector}")
                for attempt in range(40):  # 0.5秒 × 40回 = 20秒
                    element_exists_raw = await tab.evaluate(f'document.querySelector("{selector}") ? true : false')
                    element_exists = normalize_nodriver_result(element_exists_raw)
                    if isinstance(element_exists, dict):
                        element_exists = element_exists.get('exists', element_exists.get('value', False))
                    if element_exists:
                        self.logger.log(f"      ✅ 要素発見: {selector}")
                        container_found = True
                        break
                    await asyncio.sleep(0.5)
                
                if container_found:
                    break
                    
            except Exception as wait_error:
                self.logger.log(f"      ⚠️ 要素待機エラー: {selector} - {wait_error}")
        
        if not container_found:
            self.logger.log(f"    ⚠️ 商品コンテナ要素が見つかりません（20秒経過）")
    
    async def _analyze_load_more_buttons(self, tab):
        """ページ内のLoad Moreボタンを事前分析"""
        self.logger.log(f"    🔍 ページ全体のボタン分析を開始...")
        
        try:
            page_analysis = await tab.evaluate('''
                (function() {
                    // 全ボタンを収集
                    const allButtons = Array.from(document.querySelectorAll('button, a[role="button"], [role="button"]'));
                    
                    // キーワードリスト（日本語・英語）
                    const keywords = [
                        // 日本語（エルメス固有を追加）
                        'アイテムをもっと見る', 'もっと見る', 'もっと表示', '続きを見る', '次へ', '追加',
                        'さらに表示', 'すべて表示', '全て表示', 'より多く',
                        // 英語
                        'load more items', 'load more', 'show more', 'view more', 'see more',
                        'next', 'continue', 'expand', 'additional'
                    ];
                    
                    const results = {
                        totalElements: allButtons.length,
                        byText: [],
                        byAriaLabel: [],
                        byClassName: [],
                        byDataAttribute: []
                    };
                    
                    allButtons.forEach((btn, index) => {
                        const text = (btn.textContent || '').trim().toLowerCase();
                        const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
                        const className = (btn.className || '').toLowerCase();
                        const dataTestId = btn.getAttribute('data-testid') || '';
                        
                        // テキストマッチ
                        keywords.forEach(keyword => {
                            if (text.includes(keyword.toLowerCase())) {
                                results.byText.push({
                                    keyword: keyword,
                                    text: btn.textContent.trim(),
                                    index: index
                                });
                            }
                        });
                        
                        // aria-labelマッチ
                        keywords.forEach(keyword => {
                            if (ariaLabel.includes(keyword.toLowerCase())) {
                                results.byAriaLabel.push({
                                    keyword: keyword,
                                    ariaLabel: btn.getAttribute('aria-label'),
                                    index: index
                                });
                            }
                        });
                        
                        // クラス名マッチ
                        ['load', 'more', 'show', 'expand'].forEach(term => {
                            if (className.includes(term)) {
                                results.byClassName.push({
                                    term: term,
                                    className: btn.className,
                                    text: btn.textContent.trim(),
                                    index: index
                                });
                            }
                        });
                        
                        // data属性マッチ
                        if (dataTestId.includes('load') || dataTestId.includes('more')) {
                            results.byDataAttribute.push({
                                dataTestId: dataTestId,
                                text: btn.textContent.trim(),
                                index: index
                            });
                        }
                    });
                    
                    return results;
                })()
            ''')
            
            analysis = normalize_nodriver_result(page_analysis)
            
            self.logger.log(f"    📊 ボタン分析結果:")
            self.logger.log(f"       - 総要素数: {safe_get(analysis, 'totalElements', 0)}")
            self.logger.log(f"       - テキストマッチ: {len(safe_get(analysis, 'byText', []))}件")
            self.logger.log(f"       - aria-labelマッチ: {len(safe_get(analysis, 'byAriaLabel', []))}件")
            self.logger.log(f"       - クラス名マッチ: {len(safe_get(analysis, 'byClassName', []))}件")
            self.logger.log(f"       - data属性マッチ: {len(safe_get(analysis, 'byDataAttribute', []))}件")
            
            # 詳細をログ出力
            if safe_get(analysis, 'byText'):
                self.logger.log(f"    📝 テキストによる候補:")
                for item in safe_get(analysis, 'byText', [])[:3]:  # 最初の3件のみ
                    self.logger.log(f"       - '{safe_get(item, 'text')}' (キーワード: {safe_get(item, 'keyword')})")
            
            return analysis
            
        except Exception as e:
            self.logger.log(f"    ⚠️ ボタン分析エラー: {e}")
            return None
    
    async def _scroll_page(self, tab):
        """ページをスクロールして全商品を読み込む（ボタンクリック＋無限スクロール対応／詳細ロギング版）"""
        self.logger.log(f"    📜 **新**動的スクロール処理開始 (ボタンクリック + 無限スクロール)")

        # --- 実行前の状態を記録 ---
        initial_count_raw = await tab.evaluate("document.querySelectorAll('h-grid-result-item').length")
        initial_count = normalize_nodriver_result(initial_count_raw)
        if isinstance(initial_count, dict): initial_count = initial_count.get('value', 0)
        self.logger.log(f"    [事前分析] スクロール開始前の商品数: {initial_count}個")
        if self.total_items > 0:
            self.logger.log(f"    [事前分析] 宣言されている総商品数: {self.total_items}個")
        else:
            self.logger.log(f"    [事前分析] ⚠️ 宣言されている総商品数は取得できませんでした。")


        # --- フェーズ1: 「アイテムをもっと見る」ボタンの処理 ---
        self.logger.log("\n    --- フェーズ1: 「アイテムをもっと見る」ボタンのクリック試行 ---")
        try:
            button_selector = 'button[data-testid="Load more items"]'
            
            try:
                button = await tab.wait_for(button_selector, timeout=7000)
                
                # ボタンの可視性を確認
                is_visible = await tab.evaluate(f'''
                    (function() {{
                        const button = document.querySelector('{button_selector}');
                        return button && button.offsetParent !== null;
                    }})()
                ''')
                is_visible = normalize_nodriver_result(is_visible)

                if button and is_visible:
                    # ボタンのテキストを取得
                    button_text = await tab.evaluate(f'''
                        document.querySelector('{button_selector}').textContent.trim()
                    ''')
                    button_text = normalize_nodriver_result(button_text)
                    self.logger.log(f"      [成功] 「{button_text}」ボタンを発見。クリックを実行します。")
                    await self._save_html_snapshot(tab, 'snapshot_before_click.html', '[デバッグ] クリック直前')
                    
                    await tab.evaluate(f'''
                        document.querySelector('{button_selector}').scrollIntoView({{behavior: 'smooth', block: 'center'}});
                    ''')
                    await asyncio.sleep(1)
                    await button.click()

                    self.logger.log("      [待機] クリック後の商品読み込み待機中（10秒）...")
                    await asyncio.sleep(10)
                    
                    after_click_count_raw = await tab.evaluate("document.querySelectorAll('h-grid-result-item').length")
                    after_click_count = normalize_nodriver_result(after_click_count_raw)
                    if isinstance(after_click_count, dict): after_click_count = after_click_count.get('value', 0)
                    self.logger.log(f"      [検証] クリック後の商品数: {after_click_count}個 (+{after_click_count - initial_count}個)")
                    await self._save_html_snapshot(tab, 'snapshot_after_click.html', '[デバッグ] クリック直後')

                else:
                    self.logger.log("      [情報] ボタンは存在しないか、非表示です。これは想定内の挙動です。")
            except:
                self.logger.log("      [情報] ボタンが見つかりません。無限スクロールフェーズに移行します。")

        except Exception as e:
            self.logger.log(f"      [情報] ボタン処理中にタイムアウトまたはエラー ({type(e).__name__})。これも想定内の挙動の場合があります。")

        # --- フェーズ2: 無限スクロールによる全件取得 ---
        self.logger.log("\n    --- フェーズ2: 無限スクロールで全件取得 ---")
        
        last_count_raw = await tab.evaluate("document.querySelectorAll('h-grid-result-item').length")
        last_count = normalize_nodriver_result(last_count_raw)
        if isinstance(last_count, dict): last_count = last_count.get('value', 0)

        no_new_items_streak = 0
        max_scrolls = 15

        for i in range(max_scrolls):
            scroll_attempt = i + 1
            self.logger.log(f"\n      --- スクロール試行 {scroll_attempt}/{max_scrolls} ---")

            # [実行] ページ最下部へスクロール
            self.logger.log("        [実行] ページ最下部へスクロールを実行します。")
            
            # 96商品以降は無限スクロールのトリガーを確実にする
            if last_count >= 96:
                # より確実に最下部に到達するため、複数回スクロール
                await tab.evaluate("""
                    // 最下部へスクロール
                    window.scrollTo(0, document.body.scrollHeight);
                """)
                await asyncio.sleep(1)
                
                # フッター要素が見えるまでスクロール（無限スクロールのトリガー）
                await tab.evaluate("""
                    // フッターまたは最下部要素を確実に表示
                    const footer = document.querySelector('footer') || document.querySelector('[class*="footer"]');
                    if (footer) {
                        footer.scrollIntoView({behavior: 'smooth', block: 'end'});
                    } else {
                        // フッターがない場合は最下部へ
                        window.scrollTo(0, document.body.scrollHeight + 100);
                    }
                """)
                self.logger.log("        [実行] フッター要素まで確実にスクロール（無限スクロールトリガー）")
            else:
                await tab.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            
            # [待機] ネットワークとレンダリングのための待機
            # 96商品以降は無限スクロールモードなので、より長い待機が必要
            if last_count >= 96:
                self.logger.log("        [待機] 無限スクロールモード: 自動読み込みを待機中 (10秒)...")
                await asyncio.sleep(10)
            else:
                self.logger.log("        [待機] 自動読み込みとレンダリングを待機中 (5秒)...")
                await asyncio.sleep(5)

            # [検証] スクロール後の状態を多角的に分析
            current_state_raw = await tab.evaluate('''
                ({
                    itemCount: document.querySelectorAll('h-grid-result-item').length,
                    scrollHeight: document.body.scrollHeight,
                    currentY: window.scrollY
                })
            ''')
            current_state = normalize_nodriver_result(current_state_raw)
            if isinstance(current_state, dict):
                current_count = current_state.get('itemCount', 0)
            else:
                current_count = 0
            
            self.logger.log(f"        [検証] 現在の商品数: {current_count}個")
            self.logger.log(f"        [検証] ページの全高: {current_state.get('scrollHeight', 'N/A')}px")

            # [判断] 新規商品が読み込まれたかチェック
            if current_count > last_count:
                newly_loaded = current_count - last_count
                self.logger.log(f"        [判断] ✅ 新規商品 {newly_loaded}個を検出しました。")
                no_new_items_streak = 0
                if scroll_attempt in [1, 5, 10]: # 特定の回でスナップショットを保存
                     await self._save_html_snapshot(tab, f'snapshot_scroll_{scroll_attempt}.html', f'[デバッグ] スクロール{scroll_attempt}回目')
            else:
                no_new_items_streak += 1
                self.logger.log(f"        [判断] ⏸️ 新規商品はありませんでした。(連続 {no_new_items_streak}回)")
            
            # [終了条件]
            if no_new_items_streak >= 3:
                self.logger.log("\n      [終了] 3回連続で新規商品がなかったため、全件取得完了と判断し、処理を終了します。")
                break
            
            if self.total_items > 0 and current_count >= self.total_items:
                self.logger.log(f"\n      [終了] 宣言されている総商品数 ({self.total_items}個) に到達したため、処理を終了します。")
                break

            last_count = current_count
            
            if scroll_attempt == max_scrolls:
                self.logger.log(f"\n      [警告] 最大スクロール回数 ({max_scrolls}回) に到達しました。処理を強制終了します。")

        # --- 最終結果のサマリー ---
        final_count_raw = await tab.evaluate("document.querySelectorAll('h-grid-result-item').length")
        final_count = normalize_nodriver_result(final_count_raw)
        if isinstance(final_count, dict): final_count = final_count.get('value', 0)
        self.logger.log(f"\n    [最終結果] スクロール処理完了。")
        self.logger.log(f"    [最終結果] 最終的な取得見込み商品数: {final_count}個")
        if self.total_items > 0:
            coverage = (final_count / self.total_items) * 100 if self.total_items > 0 else 0
            self.logger.log(f"    [最終結果] 宣言に対する取得率: {coverage:.1f}% ({final_count}/{self.total_items})")
            if coverage < 95:
                 self.logger.log(f"    [要確認] ⚠️ 取得率が95%未満です。サイトの挙動が変更された可能性があります。")
        
        await self._save_html_snapshot(tab, 'snapshot_final_page.html', '[デバッグ] 最終状態')
    
    async def _handle_hermes_load_more(self, tab):
        """エルメス専用「もっと見る」ボタン処理"""
        self.logger.log(f"        🔍 エルメスLoad Moreボタンを検索中...")
        
        # 確実なセレクター
        selector = 'button[data-testid="Load more items"]'
        
        try:
            # ボタンの存在確認
            button_info = await tab.evaluate(f'''
                (function() {{
                    const button = document.querySelector('{selector}');
                    if (button) {{
                        return {{
                            exists: true,
                            visible: button.offsetParent !== null,
                            disabled: button.disabled || button.getAttribute('aria-disabled') === 'true',
                            text: button.textContent.trim()
                        }};
                    }}
                    return {{ exists: false }};
                }})()
            ''')
            
            button_data = normalize_nodriver_result(button_info)
            
            if safe_get(button_data, 'exists'):
                is_visible = safe_get(button_data, 'visible', False)
                is_disabled = safe_get(button_data, 'disabled', False)
                
                self.logger.log(f"        ⭐ Load Moreボタン発見")
                self.logger.log(f"           - 表示状態: {is_visible}")
                self.logger.log(f"           - 無効状態: {is_disabled}")
                
                if is_visible and not is_disabled:
                    # シンプルなクリック処理
                    success = await self._click_hermes_button(tab, selector)
                    return success
                else:
                    self.logger.log(f"           - ⚠️ ボタンはクリック不可状態")
                    return False
            else:
                self.logger.log(f"        ℹ️ Load Moreボタンが見つかりませんでした")
                return False
                
        except Exception as e:
            self.logger.log(f"        ❌ エラー: {str(e)}")
            return False
    
    async def _click_hermes_button(self, tab, selector):
        """エルメスボタンの確実クリック"""
        try:
            # nodriverでボタンを見つけてクリック
            self.logger.log("           🔍 ボタンを検索中...")
            
            # 方法1: wait_forを使用してボタンを取得
            try:
                button = await tab.wait_for(selector, timeout=5000)
                if button:
                    self.logger.log("           🎯 ボタンを発見（wait_for）")
                    
                    # スクロールしてボタンを表示
                    await tab.evaluate(f'''
                        const button = document.querySelector('{selector}');
                        if (button) {{
                            button.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                        }}
                    ''')
                    await asyncio.sleep(1)
                    
                    # ボタンをクリック
                    await button.click()
                    self.logger.log("           ✅ ボタンクリック実行（nodriver API）")
                    
                    # 読み込み待機
                    await asyncio.sleep(5)
                    return True
            except:
                # 方法1が失敗した場合、方法2を試す
                self.logger.log("           ⚠️ wait_forメソッドが失敗、代替方法を試行")
            
            # 方法2: evaluateでクリック
            result = await tab.evaluate(f'''
                (async () => {{
                    const button = document.querySelector('{selector}');
                    if (!button) return {{success: false, error: 'Button not found'}};
                    
                    // ボタンの状態確認
                    const isVisible = button.offsetParent !== null;
                    const isDisabled = button.disabled || button.getAttribute('aria-disabled') === 'true';
                    
                    if (!isVisible) return {{success: false, error: 'Button not visible'}};
                    if (isDisabled) return {{success: false, error: 'Button disabled'}};
                    
                    // スクロール
                    button.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    
                    // クリック
                    button.click();
                    
                    return {{success: true}};
                }})()
            ''')
            
            result_normalized = normalize_nodriver_result(result)
            if safe_get(result_normalized, 'success'):
                self.logger.log("           ✅ ボタンクリック実行（evaluate）")
                await asyncio.sleep(5)
                return True
            else:
                error_msg = safe_get(result_normalized, 'error', 'Unknown error')
                self.logger.log(f"           ❌ クリック失敗: {error_msg}")
                return False
            
        except Exception as e:
            self.logger.log(f"           💥 クリック処理エラー: {e}")
            import traceback
            self.logger.log(traceback.format_exc())
            return False
    
    
    async def _download_html(self, tab):
        """HTMLをダウンロード"""
        self.logger.log("  Step 3: HTMLダウンロード")
        
        try:
            # 完全なHTMLを取得
            full_html_raw = await tab.evaluate('document.documentElement.outerHTML')
            full_html = normalize_nodriver_result(full_html_raw)
            if isinstance(full_html, dict):
                full_html = full_html.get('html', full_html.get('value', str(full_html_raw)))
            
            # HTMLを保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = 'hermes_page.html'
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(full_html)
            
            file_size = len(full_html.encode('utf-8'))
            self.logger.log(f"    ✅ HTMLファイル保存完了: {filename}")
            self.logger.log(f"    📁 ファイルサイズ: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            
            # 商品数の確認（重複考慮）
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(full_html, 'lxml')
            items = soup.find_all('h-grid-result-item')
            unique_urls = set()
            for item in items:
                link = item.find('a')
                if link and link.get('href'):
                    unique_urls.add(link['href'])
            
            # 商品タグ数を直接カウント（元の実装通り）
            tag_count = full_html.count('h-grid-result-item')
            
            self.logger.log(f"    📊 HTML内の商品タグ数: {tag_count}（総数）")
            self.logger.log(f"    📊 ユニーク商品数: {len(unique_urls)}")
            
            # 総商品数との比較
            if hasattr(self, 'total_items') and self.total_items > 0:
                if len(unique_urls) < self.total_items:
                    self.logger.log(f"    ⚠️ 取得率: {len(unique_urls)}/{self.total_items} ({len(unique_urls)/self.total_items*100:.1f}%)")
            
            return True
            
        except Exception as e:
            self.logger.log(f"    ❌ HTMLダウンロードエラー: {e}")
            return False
    
    async def _check_loading_animation(self, tab):
        """ローディングアニメーション（3つのドット）を検出"""
        self.logger.log(f"        🔎 ローディングアニメーション検出開始...")
        try:
            # ローディングインジケーターの一般的なセレクター
            loading_selectors = [
                '.loading',
                '.loader',
                '[class*="loading"]',
                '[class*="loader"]',
                '.dots',
                '.spinner',
                '[aria-label*="loading"]',
                '[aria-label*="Loading"]',
                'div[class*="dot"]',
                # エルメス固有の可能性
                'h-loading',
                '[class*="load-more"]',
                '.progress'
            ]
            
            for selector in loading_selectors:
                try:
                    loading_exists = await tab.evaluate(f'''
                        (function() {{
                            const elem = document.querySelector('{selector}');
                            if (elem) {{
                                const isVisible = elem.offsetParent !== null;
                                const style = window.getComputedStyle(elem);
                                const isDisplayed = style.display !== 'none' && style.visibility !== 'hidden';
                                return isVisible && isDisplayed;
                            }}
                            return false;
                        }})()
                    ''')
                    
                    if normalize_nodriver_result(loading_exists):
                        self.logger.log(f"        🔍 ローディング要素検出: {selector}")
                        return True
                except:
                    continue
            
            # アニメーション中の要素を検出（より汎用的）
            animating_elements = await tab.evaluate('''
                (function() {
                    const elements = document.querySelectorAll('*');
                    for (let elem of elements) {
                        const style = window.getComputedStyle(elem);
                        if (style.animationName !== 'none' || style.transition !== 'none') {
                            const rect = elem.getBoundingClientRect();
                            // 画面内に表示されているアニメーション要素
                            if (rect.top >= 0 && rect.bottom <= window.innerHeight) {
                                return true;
                            }
                        }
                    }
                    return false;
                })()
            ''')
            
            result = normalize_nodriver_result(animating_elements)
            if not result:
                self.logger.log(f"        ❌ ローディングアニメーション検出なし")
            return result
            
        except Exception as e:
            self.logger.log(f"        ⚠️ ローディング検出エラー: {e}")
            return False
    
    async def _detect_dom_changes(self, tab, wait_time=2):
        """DOM変更を検出（新商品読み込みの間接的な検出）"""
        try:
            # 現在のDOM状態を記録
            initial_state = await tab.evaluate('''
                (function() {
                    const items = document.querySelectorAll('h-grid-result-item');
                    return {
                        itemCount: items.length,
                        lastItemId: items.length > 0 ? items[items.length - 1].getAttribute('id') || 'no-id' : null,
                        bodyHeight: document.body.scrollHeight
                    };
                })()
            ''')
            
            await asyncio.sleep(wait_time)
            
            # 変更後の状態を確認
            final_state = await tab.evaluate('''
                (function() {
                    const items = document.querySelectorAll('h-grid-result-item');
                    return {
                        itemCount: items.length,
                        lastItemId: items.length > 0 ? items[items.length - 1].getAttribute('id') || 'no-id' : null,
                        bodyHeight: document.body.scrollHeight
                    };
                })()
            ''')
            
            initial = normalize_nodriver_result(initial_state)
            final = normalize_nodriver_result(final_state)
            
            changes_detected = (
                safe_get(initial, 'itemCount') != safe_get(final, 'itemCount') or
                safe_get(initial, 'lastItemId') != safe_get(final, 'lastItemId') or
                safe_get(initial, 'bodyHeight') != safe_get(final, 'bodyHeight')
            )
            
            if changes_detected:
                self.logger.log(f"        📊 DOM変更検出: アイテム数 {safe_get(initial, 'itemCount')} → {safe_get(final, 'itemCount')}")
            
            return changes_detected
            
        except Exception as e:
            self.logger.log(f"        ⚠️ DOM変更検出エラー: {e}")
            return False
    
    async def _save_html_snapshot(self, tab, filename, label):
        """現在のHTMLスナップショットを保存"""
        try:
            self.logger.log(f"    📸 {label}のHTMLを保存中...")
            
            # 完全なHTMLを取得
            html_raw = await tab.evaluate('document.documentElement.outerHTML')
            html_content = normalize_nodriver_result(html_raw)
            if isinstance(html_content, dict):
                html_content = html_content.get('html', html_content.get('value', str(html_raw)))
            
            # HTMLを保存
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            file_size = len(html_content.encode('utf-8'))
            self.logger.log(f"    ✅ {label}HTML保存完了: {filename} ({file_size/1024:.1f} KB)")
            
            # 商品数をカウント
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'lxml')
            items = soup.find_all('h-grid-result-item')
            unique_urls = set()
            for item in items:
                link = item.find('a')
                if link and link.get('href'):
                    unique_urls.add(link['href'])
            
            self.logger.log(f"    📊 {label}商品数: {len(unique_urls)}個")
            
        except Exception as e:
            self.logger.log(f"    ❌ {label}HTML保存エラー: {e}")
    
    def get_results(self):
        """実行結果を取得"""
        # ログメッセージのリストを取得
        log_messages = self.logger.get_results()
        
        # 生成されたファイルのリストを取得
        import os
        import glob
        generated_files = []
        
        # スナップショットファイルを検索
        snapshot_patterns = ['snapshot_*.html', 'before_click.html', 'after_click.html', 'hermes_page.html']
        for pattern in snapshot_patterns:
            files = glob.glob(pattern)
            generated_files.extend(files)
        
        # 生成されたファイル情報をログメッセージに追加
        if generated_files:
            log_messages.append("\n📸 生成されたスナップショットファイル:")
            for file in sorted(set(generated_files)):
                if os.path.exists(file):
                    size = os.path.getsize(file) / 1024
                    log_messages.append(f"  - {file} ({size:.1f} KB)")
        
        return log_messages