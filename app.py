"""
Hermes商品情報抽出アプリケーション
モジュール化されたバージョン
"""
import sys
import os
import asyncio
import gradio as gr
from datetime import datetime
import traceback
import time

# モジュールのインポート
from modules import (
    check_environment,
    HermesScraper,
    HermesParser,
    FileHandler
)


def main_process():
    """メイン処理を実行"""
    results = []
    
    def log_and_append(message):
        results.append(message)
        print(message)
        sys.stdout.flush()
    
    log_and_append("=== Hermes商品情報抽出システム ===")
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
        
        async def run_scraping():
            scraper = HermesScraper()
            success = await scraper.scrape_hermes_site()
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
    1. 「実行」ボタンをクリック
    2. 処理完了を待つ（約1-2分）
    3. 生成されたファイルをダウンロード
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
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


if __name__ == "__main__":
    print("Hermes商品情報抽出システムを起動しています...")
    print(f"Python version: {sys.version}")
    print("")
    
    # デモを起動
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )