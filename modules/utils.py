"""
共通ユーティリティ関数
"""
import sys
from datetime import datetime


def normalize_nodriver_result(result):
    """nodriverが返す特殊なリスト形式を辞書形式に変換"""
    if isinstance(result, list):
        try:
            normalized = {}
            for item in result:
                if isinstance(item, list) and len(item) == 2:
                    key = item[0]
                    value_info = item[1]
                    if isinstance(value_info, dict) and 'value' in value_info:
                        normalized[key] = value_info['value']
                    else:
                        normalized[key] = value_info
            return normalized if normalized else result
        except Exception:
            return result
    return result


def create_logger():
    """ログ出力用のロガーを作成"""
    class Logger:
        def __init__(self):
            self.results = []
        
        def log(self, message):
            """メッセージをログに追加し、標準出力にも出力"""
            self.results.append(message)
            print(message)
            sys.stdout.flush()
        
        def get_results(self):
            """蓄積されたログ結果を取得"""
            return self.results
    
    return Logger()


def format_timestamp():
    """現在のタイムスタンプを整形して返す"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_get(obj, key, default="N/A"):
    """辞書から安全に値を取得"""
    if isinstance(obj, dict):
        return obj.get(key, default)
    elif isinstance(obj, list):
        # nodriverのリスト形式に対応
        normalized = normalize_nodriver_result(obj)
        if isinstance(normalized, dict):
            return normalized.get(key, default)
    return default