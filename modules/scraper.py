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
    
    async def _scroll_page(self, tab):
        """ページをスクロールして全商品を読み込む"""
        self.logger.log(f"    📜 高度な動的スクロール処理開始...")
        
        try:
            # 初期商品数を取得（重複を考慮）
            initial_count_raw = await tab.evaluate('''
                // 重複を除外してユニークな商品数をカウント
                (function() {
                    const items = document.querySelectorAll('h-grid-result-item');
                    const uniqueUrls = new Set();
                    items.forEach(item => {
                        const link = item.querySelector('a');
                        if (link && link.href) {
                            uniqueUrls.add(link.href);
                        }
                    });
                    return uniqueUrls.size;
                })()
            ''')
            initial_count = normalize_nodriver_result(initial_count_raw)
            if isinstance(initial_count, dict):
                initial_count = initial_count.get('value', 0)
            
            self.logger.log(f"      初期商品数: {initial_count}（ユニーク）")
            
            # スクロール前のサービスセクション目印を検出
            service_section_raw = await tab.evaluate('''
                (function() {
                    const sections = document.querySelectorAll('section');
                    for (let section of sections) {
                        const heading = section.querySelector('h2');
                        if (heading && heading.textContent.includes('サービス')) {
                            return {
                                found: true,
                                position: section.offsetTop,
                                text: heading.textContent
                            };
                        }
                    }
                    return { found: false };
                })()
            ''')
            service_section = normalize_nodriver_result(service_section_raw)
            
            if safe_get(service_section, 'found'):
                self.logger.log(f"      🎯 サービスセクション検出: '{safe_get(service_section, 'text')}' at {safe_get(service_section, 'position')}px")
            
            # 動的スクロール処理
            max_scroll_attempts = 10  # 最大試行回数を削減
            no_new_items_count = 0
            last_count = initial_count
            
            for scroll_attempt in range(max_scroll_attempts):
                self.logger.log(f"      スクロール試行 {scroll_attempt + 1}/{max_scroll_attempts}")
                
                # スムーズスクロール
                await tab.evaluate('''
                    window.scrollBy({
                        top: window.innerHeight * 0.8,
                        behavior: 'smooth'
                    });
                ''')
                
                # DOM安定性待機
                await asyncio.sleep(1.5)
                
                # 現在の商品数を確認（ユニーク）
                current_count_raw = await tab.evaluate('''
                    (function() {
                        const items = document.querySelectorAll('h-grid-result-item');
                        const uniqueUrls = new Set();
                        items.forEach(item => {
                            const link = item.querySelector('a');
                            if (link && link.href) {
                                uniqueUrls.add(link.href);
                            }
                        });
                        return uniqueUrls.size;
                    })()
                ''')
                current_count = normalize_nodriver_result(current_count_raw)
                if isinstance(current_count, dict):
                    current_count = current_count.get('value', 0)
                
                self.logger.log(f"        現在の商品数: {current_count}（ユニーク）")
                
                # 新しい商品が読み込まれたかチェック
                if current_count > last_count:
                    self.logger.log(f"        ✅ 新規商品検出: +{current_count - last_count}")
                    no_new_items_count = 0
                else:
                    no_new_items_count += 1
                    self.logger.log(f"        ⏸️ 新規商品なし (連続{no_new_items_count}回)")
                
                last_count = current_count
                
                # スクロール位置確認
                scroll_info_raw = await tab.evaluate('''
                    ({
                        scrollY: window.scrollY,
                        scrollHeight: document.body.scrollHeight,
                        clientHeight: window.innerHeight,
                        atBottom: window.scrollY + window.innerHeight >= document.body.scrollHeight - 100
                    })
                ''')
                scroll_info = normalize_nodriver_result(scroll_info_raw)
                
                at_bottom = safe_get(scroll_info, 'atBottom', False)
                if at_bottom:
                    self.logger.log(f"        📍 ページ最下部到達")
                
                # 終了条件（早期終了）
                if no_new_items_count >= 2 or at_bottom:  # 2回に削減
                    if no_new_items_count >= 2:
                        self.logger.log(f"      🏁 スクロール完了: 2回連続で新規商品なし")
                    break
                
                # Load Moreボタンチェック（省略可能）
                if scroll_attempt < 3:  # 最初の3回のみチェック
                    load_more_exists_raw = await tab.evaluate('''
                        document.querySelector('button[aria-label*="Load"], button[class*="load"], button[data-testid*="load"]') !== null
                    ''')
                    load_more_exists = normalize_nodriver_result(load_more_exists_raw)
                    if isinstance(load_more_exists, dict):
                        load_more_exists = load_more_exists.get('value', False)
                    
                    if load_more_exists:
                        self.logger.log(f"        🔘 Load Moreボタン検出")
                        try:
                            await tab.evaluate('''
                                const btn = document.querySelector('button[aria-label*="Load"], button[class*="load"], button[data-testid*="load"]');
                                if (btn) btn.click();
                            ''')
                            self.logger.log(f"        ✅ Load Moreボタンクリック")
                            await asyncio.sleep(2)
                        except:
                            pass
            
            self.logger.log(f"    ✅ スクロール処理完了: 総商品数 {last_count}（ユニーク）")
            
        except Exception as scroll_error:
            self.logger.log(f"    ⚠️ スクロールエラー: {scroll_error}")
    
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
            
            self.logger.log(f"    📊 HTML内の商品タグ数: {len(items)}（総数）")
            self.logger.log(f"    📊 ユニーク商品数: {len(unique_urls)}")
            
            return True
            
        except Exception as e:
            self.logger.log(f"    ❌ HTMLダウンロードエラー: {e}")
            return False
    
    def get_results(self):
        """実行結果を取得"""
        return self.logger.get_results()