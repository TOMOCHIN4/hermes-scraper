import gradio as gr
import asyncio
import json
import re
import subprocess
import sys
import os

# nodriverをインストール
try:
    import nodriver as nd
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "nodriver"], check=True)
    import nodriver as nd

async def extract_hermes_products(search_term=""):
    """エルメス公式サイトから商品情報を抽出する"""
    browser = None
    try:
        print("=== デバッグ開始 ===")
        print(f"Python version: {sys.version}")
        print(f"nodriver version: {nd.__version__ if hasattr(nd, '__version__') else 'unknown'}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Environment variables: DISPLAY={os.environ.get('DISPLAY', 'not set')}")
        
        print("\n1. ブラウザ起動パラメータ準備中...")
        
        browser_args = [
            '--incognito',  # プライベートモード
            '--no-sandbox',
            '--disable-dev-shm-usage', 
            '--disable-gpu',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-images',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        ]
        
        print(f"Browser args: {browser_args}")
        
        print("\n2. nodriver.start() 呼び出し開始...")
        try:
            browser = await nd.start(
                headless=True,
                sandbox=False,  # Docker環境では必須
                browser_args=browser_args
            )
            print(f"nodriver.start() 戻り値: {type(browser)} - {browser}")
        except Exception as start_error:
            print(f"nodriver.start() でエラー: {type(start_error).__name__}: {start_error}")
            import traceback
            traceback.print_exc()
            raise
        
        if browser is None:
            print("ERROR: browser is None after nd.start()")
            raise Exception("ブラウザの起動に失敗しました - browser is None")
        
        print(f"3. ブラウザ起動成功! Browser object: {browser}")
        print(f"Browser type: {type(browser)}")
        print(f"Browser attributes: {dir(browser)}")
        
        print("\n4. ページアクセス準備中...")
        
        # エルメス公式サイトのバッグページにアクセス
        base_url = "https://www.hermes.com/jp/ja/category/women/bags-and-small-leather-goods/bags-and-clutches/"
        print(f"アクセス先URL: {base_url}")
        
        print("\n5. browser.get() 呼び出し開始...")
        try:
            print(f"browser.get() を呼び出し中... browser={browser}")
            tab = await browser.get(base_url)
            print(f"browser.get() 戻り値: {type(tab)} - {tab}")
        except Exception as get_error:
            print(f"browser.get() でエラー: {type(get_error).__name__}: {get_error}")
            import traceback
            traceback.print_exc()
            raise
        
        if tab is None:
            print("ERROR: tab is None after browser.get()")
            raise Exception("ページの取得に失敗しました - tab is None")
        
        print(f"6. ページアクセス成功! Tab object: {tab}")
        print(f"Tab type: {type(tab)}")
        print(f"Tab attributes: {dir(tab) if hasattr(tab, '__dict__') else 'no attributes'}")
        
        print("\n7. ページ読み込み待機中...")
        # ページの読み込みを待つ
        await asyncio.sleep(8)
        print("8. 待機完了")
        
        # JavaScriptで商品情報を抽出
        products_script = """
        () => {
            const products = [];
            const productElements = document.querySelectorAll('.product-item, .grid-item, [data-product], .product-card, .item');
            
            productElements.forEach((element, index) => {
                try {
                    let name = '';
                    let url = '';
                    let price = '';
                    
                    // 商品名を取得
                    const nameSelectors = ['.product-name', '.product-title', 'h3', 'h2', '.title'];
                    for (const selector of nameSelectors) {
                        const nameElement = element.querySelector(selector);
                        if (nameElement && nameElement.textContent.trim()) {
                            name = nameElement.textContent.trim();
                            break;
                        }
                    }
                    
                    // URLを取得
                    const linkElement = element.querySelector('a[href]');
                    if (linkElement) {
                        url = linkElement.href;
                    }
                    
                    // 価格を取得
                    const priceSelectors = ['.price', '.product-price', '[data-price]', '.amount'];
                    for (const selector of priceSelectors) {
                        const priceElement = element.querySelector(selector);
                        if (priceElement && priceElement.textContent.trim()) {
                            price = priceElement.textContent.trim();
                            break;
                        }
                    }
                    
                    if (name && url) {
                        products.push({
                            id: index + 1,
                            name: name,
                            url: url,
                            price: price || '価格情報なし'
                        });
                    }
                } catch (error) {
                    console.error('商品情報抽出エラー:', error);
                }
            });
            
            return products;
        }
        """
        
        # 商品情報を抽出
        print("\n9. JavaScript実行開始...")
        try:
            print(f"tab.evaluate() を呼び出し中... tab={tab}")
            products = await tab.evaluate(products_script)
            print(f"tab.evaluate() 戻り値: {type(products)} - {products}")
        except Exception as eval_error:
            print(f"tab.evaluate() でエラー: {type(eval_error).__name__}: {eval_error}")
            import traceback
            traceback.print_exc()
            raise
        
        print(f"10. JavaScript実行完了! 抽出した商品数: {len(products) if products else 0}")
        if products:
            print(f"商品サンプル (最初の3件): {products[:3]}")
        else:
            print("商品が抽出されませんでした")
        
        # フィルタリング
        print("\n11. フィルタリング開始...")
        if search_term:
            print(f"検索キーワード: '{search_term}'")
            filtered_products = [
                product for product in products 
                if search_term.lower() in product['name'].lower()
            ]
            print(f"フィルタリング後: {len(filtered_products)} 商品")
        else:
            print("検索キーワードなし、全商品を対象")
            filtered_products = products
        
        result = {
            'success': True,
            'total_products': len(filtered_products),
            'products': filtered_products[:20],
            'message': f'合計 {len(filtered_products)} 商品が見つかりました'
        }
        
        print(f"12. 処理完了! 戻り値: {result}")
        return result
        
    except Exception as e:
        error_message = f'エラーが発生しました: {str(e)}'
        print(f"\n=== エラー発生 ===")
        print(f"エラータイプ: {type(e).__name__}")
        print(f"エラーメッセージ: {str(e)}")
        import traceback
        traceback.print_exc()
        print("=== エラー終了 ===")
        
        return {
            'success': False,
            'error': str(e),
            'total_products': 0,
            'products': [],
            'message': error_message
        }
    finally:
        print("\n=== クリーンアップ開始 ===")
        if browser:
            try:
                print(f"ブラウザを終了中... browser={browser}")
                await browser.stop()
                print("ブラウザ終了完了")
            except Exception as e:
                print(f"ブラウザ終了時エラー: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("ブラウザオブジェクトが存在しません")
        print("=== クリーンアップ完了 ===")

def run_extraction(search_term=""):
    """非同期関数を同期的に実行"""
    try:
        print("非同期処理開始...")
        # 既存のイベントループをチェック
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                print("既存のループを使用")
                import nest_asyncio
                nest_asyncio.apply()
                result = asyncio.create_task(extract_hermes_products(search_term))
                return result
        except RuntimeError:
            print("新しいイベントループを作成")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(extract_hermes_products(search_term))
        loop.close()
        print("非同期処理完了")
        return result
    except Exception as e:
        print(f"実行エラーの詳細: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'total_products': 0,
            'products': [],
            'message': f'実行エラー: {str(e)}'
        }

def format_products_output(result):
    """商品情報をフォーマット"""
    if not result['success']:
        return f"❌ {result['message']}", ""
    
    summary = f"✅ {result['message']}"
    
    products_text = ""
    for i, product in enumerate(result['products'], 1):
        products_text += f"\n--- 商品 {i} ---\n"
        products_text += f"商品名: {product['name']}\n"
        products_text += f"URL: {product['url']}\n"
        products_text += f"価格: {product['price']}\n"
    
    return summary, products_text

def scrape_hermes_products(search_term):
    """Gradioインターフェース用の関数"""
    result = run_extraction(search_term)
    summary, products = format_products_output(result)
    return summary, products

# Gradio 5.x インターフェース
with gr.Blocks(
    title="エルメス商品情報抽出ツール",
    theme=gr.themes.Citrus()
) as app:
    gr.Markdown("# 🛍️ エルメス公式サイト商品情報抽出ツール")
    gr.Markdown("エルメス公式オンラインストアから商品情報を自動抽出します")
    
    with gr.Row():
        with gr.Column():
            search_input = gr.Textbox(
                label="検索キーワード（オプション）",
                placeholder="例: バーキン, ケリー, ピコタン",
                value=""
            )
            extract_btn = gr.Button("🔍 商品情報を取得", variant="primary")
    
    with gr.Row():
        with gr.Column():
            summary_output = gr.Textbox(
                label="取得結果サマリー",
                interactive=False
            )
            products_output = gr.Textbox(
                label="商品詳細リスト",
                lines=20,
                interactive=False
            )
    
    # イベントリスナーを設定
    extract_btn.click(
        fn=scrape_hermes_products,
        inputs=[search_input],
        outputs=[summary_output, products_output]
    )
    
    gr.Markdown("""
    ## 使用方法
    1. 検索キーワードを入力（任意）
    2. 「商品情報を取得」ボタンをクリック
    3. 結果が表示されるまでお待ちください
    
    ## 注意事項
    - プライベートモード（シークレットモード）でアクセスします
    - 抽出には数秒〜数十秒かかる場合があります
    - エルメス公式サイトの利用規約を遵守してください
    - 商用利用は控え、個人の研究・学習目的でご利用ください
    """)

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)