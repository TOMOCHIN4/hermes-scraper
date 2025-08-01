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
        self.console_logs = []  # ブラウザのコンソールログを保持するリストを追加
    
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
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            '--window-size=1920,15000',  # 超巨大縦長ウィンドウ（高さ15000ピクセル）
            '--start-maximized',
            '--incognito'  # プライベートブラウズモード（シークレットモード）を有効化
        ]
        
        self.browser = await nd.start(
            headless=True,
            sandbox=False,
            browser_args=browser_args
        )
        
        self.logger.log(f"    ✅ Browser開始成功: {type(self.browser)}")
        self.logger.log(f"    📐 ウィンドウサイズ: 1920x15000 (超巨大縦長設定)")
        self.logger.log(f"    🔒 プライベートブラウズモード: 有効")
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
            
            # ウィンドウサイズを確認
            window_size = await tab.evaluate('''
                ({
                    width: window.innerWidth,
                    height: window.innerHeight,
                    screenHeight: screen.height
                })
            ''')
            ws = normalize_nodriver_result(window_size)
            self.logger.log(f"    📐 実際のビューポート: {ws.get('width', 'N/A')}x{ws.get('height', 'N/A')}px")
            
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
        """ページをスクロールして全商品を読み込む（エルメスサイト仕様に特化）"""
        self.logger.log(f"    📜 動的読み込み処理開始 (エルメスサイト特化版)")

        # 初期商品数を確認
        initial_count_raw = await tab.evaluate("document.querySelectorAll('h-grid-result-item').length")
        initial_count = normalize_nodriver_result(initial_count_raw)
        if isinstance(initial_count, dict):
            initial_count = initial_count.get('value', 0)
        self.logger.log(f"\n    [初期状態] ボタンクリック前の商品数: {initial_count}個")
        
        # --- フェーズ1: ボタンクリック（成功実績のあるコード）---
        self.logger.log("\n    --- フェーズ1: 「アイテムをもっと見る」ボタンのクリック試行 ---")
        
        # 総商品数が48以下の場合はボタンが存在しない
        total_products = getattr(self, 'total_items', 0)
        skip_button = False
        if total_products > 0 and total_products <= 48:
            self.logger.log(f"      [スキップ] 総商品数が{total_products}個のため、Load Moreボタンは存在しません")
            self.logger.log(f"      [完了] 全商品が既に表示されています")
            return  # ボタンもスクロールも不要
        
        try:
            button_selector = 'button[data-testid="Load more items"]'
            # まずボタンの存在を確認
            button_exists = await tab.evaluate(f'!!document.querySelector("{button_selector}")')
            button_exists = normalize_nodriver_result(button_exists)
            
            if not button_exists or skip_button:
                self.logger.log("      [情報] Load Moreボタンが見つかりません（スキップしてスクロール処理へ）")
                skip_button = True
            
            if not skip_button:
                button = await tab.wait_for(button_selector, timeout=5000)
                
                # ボタンの可視性を確認
                is_visible = await tab.evaluate(f'''
                    (function() {{
                        const button = document.querySelector('{button_selector}');
                        return button && button.offsetParent !== null;
                    }})()
                ''')
                is_visible = normalize_nodriver_result(is_visible)
                
                if button and is_visible:
                    self.logger.log("      [成功] ボタンを発見。クリックを実行します。")
                    await tab.evaluate(f'''
                        document.querySelector('{button_selector}').scrollIntoView({{behavior: 'smooth', block: 'center'}});
                    ''')
                    await asyncio.sleep(1)
                    await button.click()
                    self.logger.log("      [待機] クリック後の商品読み込み待機中（10秒）...")
                    await asyncio.sleep(10)
        except Exception:
            self.logger.log("      [情報] ボタン処理でタイムアウトまたはエラー。")
        
        # --- フェーズ2: 商品数に応じた段階的スクロール処理 ---
        self.logger.log("\n    --- フェーズ2: 商品数に応じた段階的スクロール処理 ---")
        
        # 総商品数に基づいてスクロール回数を決定
        total_products = getattr(self, 'total_items', 0)
        if total_products <= 96:
            self.logger.log(f"      [スキップ] 総商品数が{total_products}個のため、スクロール不要")
            return
        
        # 48の倍数で必要なスクロール回数を計算
        scroll_rounds = max(1, (total_products - 48) // 48)
        self.logger.log(f"      [計画] 総商品数{total_products}個に対して{scroll_rounds}回のスクロールを実行")
        
        # 固定値スクロール戦略（7500pxずつ95%まで）
        self.logger.log(f"\n      [スクロール戦略] 7500pxずつ固定スクロール（95%到達まで）")
        
        scroll_position = 0
        scroll_increment = 7500
        scroll_count = 0
        previous_count = 0
        
        while True:
            scroll_count += 1
            scroll_position += scroll_increment
            
            self.logger.log(f"\n      [スクロール {scroll_count}] {scroll_position}px地点へ")
            
            scroll_result = await tab.evaluate(f'''
                (() => {{
                    const before = window.scrollY;
                    window.scrollTo(0, {scroll_position});
                    const after = window.scrollY;
                    const itemCount = document.querySelectorAll('h-grid-result-item').length;
                    const bodyHeight = document.body.scrollHeight;
                    return {{
                        before: before,
                        after: after,
                        itemCount: itemCount,
                        bodyHeight: bodyHeight,
                        reachedBottom: after + window.innerHeight >= bodyHeight
                    }};
                }})()
            ''')
            
            result = normalize_nodriver_result(scroll_result)
            current_count = result.get('itemCount', 0)
            self.logger.log(f"      スクロール位置: {result.get('before', 0)} → {result.get('after', 0)}")
            self.logger.log(f"      現在の商品数: {current_count}個")
            
            # 取得率を計算
            if self.total_items > 0:
                current_rate = (current_count / self.total_items) * 100
                self.logger.log(f"      取得率: {current_rate:.1f}%")
                
                # 95%以上到達したら成功判定
                if current_rate >= 95.0:
                    self.logger.log(f"      ✅ {current_rate:.1f}%到達！成功判定（{current_count}/{self.total_items}商品）")
                    break
            
            # ページ最下部に到達したら終了
            if result.get('reachedBottom', False):
                self.logger.log(f"      ⚠️ ページ最下部に到達（商品数: {current_count}個）")
                break
            
            # 商品数が増えなくなったらもう少し待機
            if current_count == previous_count:
                self.logger.log(f"      [追加待機] 商品数が増えないため5秒待機...")
                await asyncio.sleep(5)
            else:
                await asyncio.sleep(3)
            
            previous_count = current_count
            
            # 安全のため最大10回まで
            if scroll_count >= 10:
                self.logger.log(f"      ⚠️ 最大スクロール回数に到達")
                break
        
        
        self.logger.log("      [待機] 最終読み込み待機中（10秒）...")
        await asyncio.sleep(10)
        
        # 読み込み状況を確認
        item_count = await tab.evaluate("document.querySelectorAll('h-grid-result-item').length")
        count = normalize_nodriver_result(item_count)
        if isinstance(count, dict):
            count = count.get('value', 0)
        self.logger.log(f"      [確認] 最終的な商品数: {count}個")
        
        # 85%以上だが95%に達していない場合、追加スクロールを試行
        if self.total_items > 0 and count < self.total_items and count / self.total_items >= 0.85 and count / self.total_items < 0.95:
            self.logger.log(f"      [追加処理] 85%以上95%未満（{count}/{self.total_items}）- 追加スクロール実行")

            # 最下部で微小なスクロールを複数回実行
            for i in range(3):
                await tab.evaluate('''
                    window.scrollTo(0, document.body.scrollHeight - 100);
                ''')
                await asyncio.sleep(2)
                await tab.evaluate('''
                    window.scrollTo(0, document.body.scrollHeight);
                ''')
                await asyncio.sleep(3)
            
            # 最終確認
            final_count = await tab.evaluate("document.querySelectorAll('h-grid-result-item').length")
            final_count = normalize_nodriver_result(final_count)
            if isinstance(final_count, dict):
                final_count = final_count.get('value', 0)
            self.logger.log(f"      [最終確認] 追加スクロール後の商品数: {final_count}個")
    
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
    
    def get_results(self):
        """実行結果のログを取得"""
        # TypeErrorを修正し、コンソールログも追加で返すように変更
        full_logs = self.logger.get_results()
        
        # コンソールログを追加
        if self.console_logs:
            full_logs.append("\n--- Browser Console Logs ---")
            for log in self.console_logs:
                full_logs.append(f"  - {log}")
        
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
            full_logs.append("\n📸 生成されたスナップショットファイル:")
            for file in sorted(set(generated_files)):
                if os.path.exists(file):
                    size = os.path.getsize(file) / 1024
                    full_logs.append(f"  - {file} ({size:.1f} KB)")
        
        return full_logs
