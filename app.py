"""
Hermes商品情報抽出アプリケーション
FastAPIとGradioを統合したバージョン（HuggingFace Spaces対応）
"""
import sys
import os
import asyncio
import gradio as gr
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime
import traceback
import time
import urllib.parse
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# モジュールのインポート
from modules import (
    check_environment,
    HermesScraper,
    HermesParser,
    FileHandler
)

# FastAPIアプリケーションの初期化（root_path設定）
app = FastAPI(
    title="Hermes Scraper API",
    description="エルメス商品情報抽出システムのAPIサーバー",
    version="1.0.0",
    root_path="/"  # HuggingFace Spaces対応
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# リクエスト/レスポンスモデル
class ScrapeRequest(BaseModel):
    keyword: str = "バッグ"
    worker_id: Optional[str] = None

class ScrapeResponse(BaseModel):
    status: str
    timestamp: str
    worker_id: Optional[str]
    keyword: str
    total_products: int
    unique_products: int
    files: Dict[str, str]
    products: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    execution_time: float

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str

# Gradio UI用のメイン処理関数
def main_process(search_keyword="バッグ"):
    """メイン処理を実行"""
    results = []
    
    def log_and_append(message):
        results.append(message)
        print(message)
        sys.stdout.flush()
    
    log_and_append("=== Hermes商品情報抽出システム (15000px版) ===")
    log_and_append(f"実行時刻: {datetime.now()}")
    log_and_append("")
    
    try:
        # Phase 1-5: 環境チェック
        log_and_append("📋 Phase 1-5: 環境チェック実行中...")
        env_ok, env_results = check_environment()
        results.extend(env_results)
        
        if not env_ok:
            log_and_append("\n❌ 環境チェックでエラーが発生しました。")
            return "\n".join(results)
        
        log_and_append("\n✅ 環境チェック完了！")
        log_and_append("")
        
        # Phase 6.0: スクレイピング実行
        log_and_append("🌐 Phase 6.0: Hermesサイトスクレイピング開始...")
        log_and_append(f"🔍 検索キーワード: {search_keyword}")
        
        async def run_scraping():
            scraper = HermesScraper()
            success = await scraper.scrape_hermes_site(search_keyword=search_keyword)
            return success, scraper.get_results()
        
        # 非同期処理を実行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        scraping_success, scraping_results = loop.run_until_complete(run_scraping())
        loop.close()
        
        results.extend(scraping_results)
        
        if not scraping_success:
            log_and_append("\n❌ スクレイピングに失敗しました。")
            return "\n".join(results)
        
        log_and_append("\n✅ Phase 6.0完了！")
        log_and_append("")
        
        # Phase 6.5: HTML解析
        log_and_append("📊 Phase 6.5: HTML解析開始...")
        parser = HermesParser()
        parse_success = parser.parse_html_file()
        results.extend(parser.get_results())
        
        if not parse_success:
            log_and_append("\n❌ HTML解析に失敗しました。")
            return "\n".join(results)
        
        products = parser.get_products()
        log_and_append(f"\n✅ Phase 6.5完了！ {len(products)}個の商品情報を抽出しました。")
        
        # 結果サマリー
        log_and_append("\n" + "="*50)
        log_and_append("📊 実行結果サマリー")
        log_and_append("="*50)
        log_and_append(f"✅ Phase 1-5: 環境チェック - 成功")
        log_and_append(f"✅ Phase 6.0: スクレイピング - 成功")
        log_and_append(f"✅ Phase 6.5: HTML解析 - 成功")
        log_and_append(f"📦 抽出商品数: {len(products)}個")
        
        # ダウンロード可能ファイル
        files = FileHandler.get_downloadable_files()
        if files:
            log_and_append(f"\n💾 生成されたファイル:")
            for file in files[:5]:  # 最新5件まで表示
                log_and_append(f"  - {file['name']} ({file['size_kb']})")
        
    except Exception as e:
        log_and_append(f"\n❌ エラーが発生しました: {type(e).__name__}: {str(e)}")
        log_and_append(traceback.format_exc())
    
    return "\n".join(results)


def get_downloadable_files():
    """ダウンロード可能なファイルリストを取得"""
    files = FileHandler.get_downloadable_files()
    
    # クリック前後のHTMLファイルも追加
    additional_files = ['before_click.html', 'after_click.html']
    for filename in additional_files:
        if os.path.exists(filename):
            stat = os.stat(filename)
            file_size = stat.st_size / 1024
            modified_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))
            files.append({
                'name': filename,
                'size_kb': f"{file_size:.1f} KB",
                'modified': modified_time
            })
    
    if not files:
        return [("ファイルがありません", None)]
    
    # Gradio用のファイルリストを作成
    file_list = []
    for file in files[:15]:  # 最斖15件まで
        file_list.append((f"{file['name']} ({file['size_kb']}, {file['modified']})", file['name']))
    
    return file_list


# FastAPIエンドポイント
@app.get("/api/info")
async def api_info():
    """API情報エンドポイント"""
    return {
        "message": "Hermes Scraper API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/v1/health",
            "scrape": "/api/v1/scrape"
        }
    }

@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """ヘルスチェックエンドポイント"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/v1/scrape", response_model=ScrapeResponse)
async def scrape_hermes(request: ScrapeRequest):
    """エルメスサイトをスクレイピングして商品情報を抽出"""
    start_time = time.time()
    
    try:
        # 環境チェック
        env_ok, env_results = check_environment()
        if not env_ok:
            raise HTTPException(
                status_code=500,
                detail="環境チェックに失敗しました"
            )
        
        # スクレイピング実行
        scraper = HermesScraper()
        success = await scraper.scrape_hermes_site(search_keyword=request.keyword)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="スクレイピングに失敗しました"
            )
        
        # HTML解析
        parser = HermesParser()
        parse_success = parser.parse_html_file()
        
        if not parse_success:
            raise HTTPException(
                status_code=500,
                detail="HTML解析に失敗しました"
            )
        
        products = parser.get_products()
        
        # ファイル名にタイムスタンプとワーカーIDを追加
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        worker_suffix = f"_{request.worker_id}" if request.worker_id else ""
        
        # ファイル名を変更
        html_file = f"hermes_page_{timestamp}{worker_suffix}.html"
        json_file = f"hermes_products_{timestamp}{worker_suffix}.json"
        
        # 既存のファイルをリネーム
        if os.path.exists("hermes_page.html"):
            os.rename("hermes_page.html", html_file)
        if os.path.exists("hermes_products.json"):
            os.rename("hermes_products.json", json_file)
        
        # 実行時間を計算
        execution_time = time.time() - start_time
        
        # レスポンスを作成
        return ScrapeResponse(
            status="success",
            timestamp=datetime.now().isoformat(),
            worker_id=request.worker_id,
            keyword=request.keyword,
            total_products=len(products),
            unique_products=len(products),
            files={
                "html": html_file,
                "json": json_file
            },
            products=products if len(products) <= 10 else None,
            execution_time=execution_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        execution_time = time.time() - start_time
        return ScrapeResponse(
            status="error",
            timestamp=datetime.now().isoformat(),
            worker_id=request.worker_id,
            keyword=request.keyword,
            total_products=0,
            unique_products=0,
            files={},
            error=str(e),
            execution_time=execution_time
        )


# Gradioインターフェース
with gr.Blocks(title="Hermes商品情報抽出システム") as demo:
    gr.Markdown("""
    # 🛍️ Hermes商品情報抽出システム
    
    エルメス公式サイトから商品情報を自動抽出します。
    
    ## 実行フロー
    1. **Phase 1-5**: 環境チェック（Python、依存関係、Chromium、ネットワーク）
    2. **Phase 6.0**: Hermesサイトスクレイピング（HTMLダウンロード）
    3. **Phase 6.5**: HTML解析（商品情報抽出）
    
    ## 使い方
    1. 検索キーワードを入力（デフォルト: バッグ）
    2. 「実行」ボタンをクリック
    3. 処理完了を待つ（約1-2分）
    4. 生成されたファイルをダウンロード
    
    ## API利用
    - **Health Check**: `GET /api/v1/health`
    - **Scrape**: `POST /api/v1/scrape`
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            search_input = gr.Textbox(
                label="🔍 検索キーワード",
                placeholder="例: バッグ、財布、時計など",
                value="バッグ",
                info="エルメス公式サイトで検索したい商品カテゴリを入力"
            )
            run_button = gr.Button("🚀 実行", variant="primary", size="lg")
            
            gr.Markdown("""
            ### 📝 メモ
            - 処理には1-2分かかります
            - エラーが発生した場合は再実行してください
            - 生成ファイルは自動的に保存されます
            """)
    
    with gr.Row():
        output_text = gr.Textbox(
            label="実行ログ", 
            lines=30, 
            max_lines=50,
            show_copy_button=True
        )
    
    with gr.Row():
        file_dropdown = gr.Dropdown(
            label="📥 ダウンロード可能なファイル",
            choices=[],
            interactive=True
        )
        download_button = gr.DownloadButton(
            label="⬇️ ダウンロード",
            visible=False
        )
    
    def update_file_list():
        """ファイルリストを更新"""
        files = get_downloadable_files()
        return gr.update(choices=files, value=files[0][1] if files and files[0][1] else None)
    
    def prepare_download(selected_file):
        """選択されたファイルをダウンロード準備"""
        if selected_file and os.path.exists(selected_file):
            return gr.update(visible=True, value=selected_file)
        return gr.update(visible=False)
    
    # イベントハンドラー
    run_button.click(
        fn=main_process,
        inputs=search_input,
        outputs=output_text
    ).then(
        fn=update_file_list,
        outputs=file_dropdown
    )
    
    file_dropdown.change(
        fn=prepare_download,
        inputs=file_dropdown,
        outputs=download_button
    )
    
    # 初期表示時にファイルリストを更新
    demo.load(
        fn=update_file_list,
        outputs=file_dropdown
    )


# StaticFiles → gr.mount_gradio_app の順でマウント（StaticFilesを先に）
# 注: 現在は静的ファイルなしだが、必要に応じて追加可能
# app.mount("/static", StaticFiles(directory="static"), name="static")

# FastAPIにGradioをマウント（HuggingFace Spaces対応）
app = gr.mount_gradio_app(app, demo, path="/", root_path="/")

# HuggingFace Spaces用の起動設定
if __name__ == "__main__":
    import uvicorn
    
    # 環境変数の設定（HuggingFace Spaces対応）
    os.environ["GRADIO_SERVER_NAME"] = "0.0.0.0"
    os.environ["GRADIO_ROOT_PATH"] = "/"
    
    print("Hermes商品情報抽出システム（FastAPI + Gradio統合版）を起動しています...")
    print(f"Python version: {sys.version}")
    print(f"Gradio version: {gr.__version__}")
    print("")
    
    # HuggingFace Spacesではポート7860を使用、プロキシヘッダー有効
    logger.info("Starting server on http://0.0.0.0:7860")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=7860, 
        log_level="info",
        proxy_headers=True  # HuggingFace Spacesのリバースプロキシ対応
    )