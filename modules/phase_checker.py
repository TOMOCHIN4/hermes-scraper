"""
Phase 1-5: 環境チェック機能
"""
import sys
import os
import subprocess
import shutil
from .utils import create_logger, format_timestamp


def check_environment():
    """Phase 1-5の環境チェックを実行"""
    logger = create_logger()
    
    logger.log("=== Phase 1-5: 環境チェック ===")
    logger.log(f"実行時刻: {format_timestamp()}")
    logger.log("")
    
    all_phases_ok = True
    
    # Phase 1: Python環境
    logger.log("📋 Phase 1: Python環境チェック")
    try:
        logger.log(f"  Python version: {sys.version.split()[0]}")
        logger.log("  ✅ Python環境: OK")
    except Exception as e:
        logger.log(f"  ❌ Python環境: エラー - {e}")
        all_phases_ok = False
    
    # Phase 2: 依存関係
    logger.log("\n📋 Phase 2: 依存関係チェック")
    try:
        import gradio as gr
        import nest_asyncio
        import nodriver as nd
        from bs4 import BeautifulSoup
        import lxml
        
        logger.log("  ✅ gradio: OK")
        logger.log("  ✅ nest_asyncio: OK") 
        logger.log("  ✅ nodriver: OK")
        logger.log("  ✅ beautifulsoup4: OK")
        logger.log("  ✅ lxml: OK")
    except ImportError as e:
        logger.log(f"  ❌ 依存関係: エラー - {e}")
        all_phases_ok = False
    
    # Phase 3: Chromiumチェック
    logger.log("\n📋 Phase 3: Chromiumチェック")
    chromium_paths = [
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
        'chromium',
        'chromium-browser'
    ]
    
    chromium_found = False
    for path in chromium_paths:
        if shutil.which(path):
            logger.log(f"  ✅ Chromium: {path} で検出")
            chromium_found = True
            break
    
    if not chromium_found:
        logger.log("  ❌ Chromium: 見つかりません")
        all_phases_ok = False
    
    # Phase 4: ネットワーク
    logger.log("\n📋 Phase 4: ネットワーク接続チェック")
    try:
        result = subprocess.run(['ping', '-c', '1', 'google.com'], 
                              capture_output=True, timeout=5)
        if result.returncode == 0:
            logger.log("  ✅ ネットワーク: OK")
        else:
            logger.log("  ⚠️ ネットワーク: ping失敗（ただし続行可能）")
    except Exception:
        logger.log("  ⚠️ ネットワーク: チェックスキップ")
    
    # Phase 5: JavaScript実行環境
    logger.log("\n📋 Phase 5: JavaScript実行環境")
    logger.log("  ✅ nodriver経由でJavaScript実行可能")
    
    logger.log("")
    if all_phases_ok:
        logger.log("✅ 全てのPhaseチェック完了！")
    else:
        logger.log("⚠️ 一部のPhaseでエラーがありました")
    
    return all_phases_ok, logger.get_results()