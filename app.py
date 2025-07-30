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
        print("ブラウザ起動を開始...")
        # プライベートモード（シークレットモード）でブラウザを起動
        browser = await nd.start(
            headless=True,
            sandbox=False,  # Docker環境では必須
            browser_args=[
                '--incognito',  # プライベートモード
                '--no-sandbox',
                '--disable-dev-shm-usage', 
                '--disable-gpu',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
            ]
        )
        
        if browser is None:
            raise Exception("ブラウザの起動に失敗しました")
        
        print("ブラウザ起動成功、ページアクセス開始...")
        
        # エルメス公式サイトのバッグページにアクセス
        base_url = "https://www.hermes.com/jp/ja/category/women/bags-and-small-leather-goods/bags-and-clutches/"
        print(f"アクセス先URL: {base_url}")
        
        tab = await browser.get(base_url)
        if tab is None:
            raise Exception("ページの取得に失敗しました")
        
        print("ページアクセス成功、読み込み待機中...")
        # ページの読み込みを待つ
        await asyncio.sleep(8)
        
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
        print("JavaScript実行開始...")
        products = await tab.evaluate(products_script)
        print(f"抽出した商品数: {len(products) if products else 0}")
        
        # フィルタリング
        if search_term:
            filtered_products = [
                product for product in products 
                if search_term.lower() in product['name'].lower()
            ]
        else:
            filtered_products = products
        
        return {
            'success': True,
            'total_products': len(filtered_products),
            'products': filtered_products[:20],
            'message': f'合計 {len(filtered_products)} 商品が見つかりました'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'total_products': 0,
            'products': [],
            'message': f'エラーが発生しました: {str(e)}'
        }
    finally:
        if browser:
            try:
                print("ブラウザを終了中...")
                await browser.stop()
                print("ブラウザ終了完了")
            except Exception as e:
                print(f"ブラウザ終了時エラー: {e}")
                pass

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