"""
ファイル入出力関連の処理
"""
import os
import json
import glob
from datetime import datetime


class FileHandler:
    """ファイル操作を管理するクラス"""
    
    @staticmethod
    def get_downloadable_files():
        """ダウンロード可能なファイルのリストを取得"""
        files = []
        
        # HTMLファイル（メイン + スナップショット）
        html_files = glob.glob("hermes_page*.html")
        files.extend(html_files)
        
        # スナップショットファイル
        snapshot_files = glob.glob("snapshot_*.html")
        files.extend(snapshot_files)
        
        # その他のHTMLファイル
        other_html = glob.glob("before_click.html") + glob.glob("after_click.html")
        files.extend(other_html)
        
        # JSONファイル
        json_files = glob.glob("hermes_products*.json")
        files.extend(json_files)
        
        # CSVファイル（将来の拡張用）
        csv_files = glob.glob("hermes_products*.csv")
        files.extend(csv_files)
        
        # 除外すべきファイル
        exclude_files = {'requirements.txt', 'README.txt', 'Dockerfile.txt'}
        files = [f for f in files if f not in exclude_files]
        
        # ファイル情報を収集
        file_info = []
        for file in files:
            if os.path.exists(file):
                size = os.path.getsize(file)
                mtime = os.path.getmtime(file)
                file_info.append({
                    'name': file,
                    'size': size,
                    'size_kb': f"{size/1024:.1f} KB",
                    'modified': datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                })
        
        # 更新時刻でソート（新しい順）
        file_info.sort(key=lambda x: x['modified'], reverse=True)
        
        return file_info
    
    @staticmethod
    def clean_old_files(keep_latest=5):
        """古いファイルを削除（最新N個を保持）"""
        patterns = ["hermes_page*.html", "hermes_products*.json"]
        
        for pattern in patterns:
            files = glob.glob(pattern)
            if len(files) > keep_latest:
                # 更新時刻でソート
                files.sort(key=lambda x: os.path.getmtime(x))
                # 古いファイルを削除
                for file in files[:-keep_latest]:
                    try:
                        os.remove(file)
                    except:
                        pass
    
    @staticmethod
    def save_json(data, filename):
        """JSONファイルを保存"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def load_json(filename):
        """JSONファイルを読み込み"""
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    @staticmethod
    def file_exists(filename):
        """ファイルの存在確認"""
        return os.path.exists(filename)