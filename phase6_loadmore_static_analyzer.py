"""
Phase 6 改善: 「アイテムをもっと見る」ボタンの静的解析
保存されたHTMLから技術情報を抽出
"""

from bs4 import BeautifulSoup
import re
import json

def analyze_loadmore_button_from_html(html_file='hermes_page.html'):
    """保存されたHTMLからLoad Moreボタンの技術詳細を分析"""
    
    print("=== Load Moreボタン静的解析 ===")
    print("")
    
    try:
        # HTMLファイルを読み込み
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. Load Moreボタンを探す
        print("1. Load Moreボタンの検索")
        
        # 複数の方法でボタンを探す
        button = None
        button_selectors = [
            {'data-testid': 'Load more items'},
            {'name': 'undefined'},
            {'class': re.compile('button-secondary')},
        ]
        
        for selector in button_selectors:
            button = soup.find('button', selector)
            if button:
                print(f"✅ ボタン発見: {selector}")
                break
        
        # テキストで検索
        if not button:
            all_buttons = soup.find_all('button')
            for btn in all_buttons:
                if 'アイテムをもっと見る' in btn.get_text():
                    button = btn
                    print("✅ ボタン発見: テキスト検索")
                    break
        
        if button:
            print("\n2. ボタンの詳細情報:")
            print(f"- タグ: {button.name}")
            print(f"- テキスト: {button.get_text(strip=True)}")
            print(f"- クラス: {' '.join(button.get('class', []))}")
            
            # 属性を表示
            print("\n属性:")
            for attr, value in button.attrs.items():
                print(f"  - {attr}: {value}")
            
            # 親要素の情報
            parent = button.parent
            if parent:
                print(f"\n親要素: {parent.name}")
                if parent.get('class'):
                    print(f"親要素クラス: {' '.join(parent.get('class', []))}")
            
            # Angular属性の確認
            angular_attrs = [attr for attr in button.attrs if attr.startswith('_ng')]
            if angular_attrs:
                print(f"\nAngular属性: {angular_attrs}")
            
            # ボタンの完全なHTML
            print("\nボタンの完全なHTML:")
            print(str(button)[:500] + "..." if len(str(button)) > 500 else str(button))
            
        else:
            print("❌ Load Moreボタンが見つかりません")
        
        # 3. 商品グリッドの分析
        print("\n\n3. 商品グリッドの分析")
        
        # h-grid-result-item要素を探す
        grid_items = soup.find_all('h-grid-result-item')
        print(f"- h-grid-result-item要素数: {len(grid_items)}")
        
        # グリッドコンテナを探す
        grid_container = soup.find('h-grid-results')
        if grid_container:
            print("✅ h-grid-resultsコンテナ発見")
            if grid_container.get('class'):
                print(f"  クラス: {' '.join(grid_container.get('class', []))}")
        
        # 4. JavaScriptコードの分析
        print("\n\n4. JavaScriptコードの分析")
        
        # スクリプトタグを探す
        scripts = soup.find_all('script')
        print(f"- スクリプトタグ数: {len(scripts)}")
        
        # Load More関連のコードを探す
        loadmore_patterns = [
            r'loadMore',
            r'load.?more',
            r'pagination',
            r'infinite.?scroll',
            r'アイテムをもっと見る',
            r'Load more items'
        ]
        
        for i, script in enumerate(scripts):
            if script.string:
                for pattern in loadmore_patterns:
                    if re.search(pattern, script.string, re.IGNORECASE):
                        print(f"\n✅ スクリプト#{i}にLoad More関連コード発見:")
                        # 該当部分の前後を表示
                        match = re.search(pattern, script.string, re.IGNORECASE)
                        if match:
                            start = max(0, match.start() - 100)
                            end = min(len(script.string), match.end() + 100)
                            print(f"  ...{script.string[start:end]}...")
                        break
        
        # 5. APIエンドポイントの推測
        print("\n\n5. APIエンドポイントの推測")
        
        # リンクやフォームからAPIパターンを探す
        api_patterns = [
            r'/api/',
            r'/search/',
            r'/products/',
            r'/catalog/',
            r'page=',
            r'offset=',
            r'limit='
        ]
        
        # href属性を持つ全要素をチェック
        links = soup.find_all(href=True)
        api_candidates = set()
        
        for link in links:
            href = link['href']
            for pattern in api_patterns:
                if re.search(pattern, href):
                    api_candidates.add(href)
        
        if api_candidates:
            print("APIエンドポイント候補:")
            for api in list(api_candidates)[:10]:  # 最初の10個のみ表示
                print(f"  - {api}")
        
        # 6. 総商品数の確認
        print("\n\n6. 総商品数の確認")
        
        # 総数を表示する要素を探す
        total_patterns = [
            {'data-testid': 'number-current-result'},
            {'class': re.compile('header-title-current-number-result')},
        ]
        
        for pattern in total_patterns:
            total_elem = soup.find(attrs=pattern)
            if total_elem:
                print(f"✅ 総数要素発見: {pattern}")
                print(f"  テキスト: {total_elem.get_text(strip=True)}")
                # 数字を抽出
                numbers = re.findall(r'\d+', total_elem.get_text())
                if numbers:
                    print(f"  抽出された数字: {numbers}")
                break
        
        # 7. 推奨実装方法
        print("\n\n7. 技術的な推奨事項:")
        print("- ボタンクリック: button[data-testid='Load more items']を使用")
        print("- クリック後の待機: 新しいh-grid-result-item要素の出現を監視")
        print("- 完了判定: ボタンの非表示化または商品数の変化なし")
        print("- タイムアウト: 各クリック後10-15秒の最大待機時間")
        print("- レート制限: クリック間に2-3秒の待機時間を設ける")
        
        # 結果をJSONファイルに保存
        analysis_result = {
            "button_found": button is not None,
            "button_selector": "button[data-testid='Load more items']" if button else None,
            "initial_product_count": len(grid_items),
            "has_angular": bool(angular_attrs) if button else False,
            "recommendations": {
                "click_method": "evaluate with button.click()",
                "wait_for": "new h-grid-result-item elements",
                "timeout": "10-15 seconds per click",
                "rate_limit": "2-3 seconds between clicks"
            }
        }
        
        with open('loadmore_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 分析結果を loadmore_analysis.json に保存")
        
    except FileNotFoundError:
        print(f"❌ HTMLファイル '{html_file}' が見つかりません")
        print("app.pyを実行してHTMLを生成してください")
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 複数のファイル名を試す
    possible_files = ['hermes_page.html', '../hermes_page.html', 'download_sample/hermes_page.html']
    
    for file_path in possible_files:
        import os
        if os.path.exists(file_path):
            print(f"HTMLファイル発見: {file_path}\n")
            analyze_loadmore_button_from_html(file_path)
            break
    else:
        print("❌ hermes_page.htmlが見つかりません")
        print("利用可能なHTMLファイルを探しています...")
        
        # download_sampleディレクトリをチェック
        if os.path.exists('download_sample'):
            html_files = [f for f in os.listdir('download_sample') if f.endswith('.html')]
            if html_files:
                print(f"\ndownload_sampleディレクトリで{len(html_files)}個のHTMLファイル発見:")
                for f in html_files[:5]:
                    print(f"  - {f}")
                
                # 最初のファイルで分析を実行
                first_file = os.path.join('download_sample', html_files[0])
                print(f"\n{first_file}を使用して分析を実行します...\n")
                analyze_loadmore_button_from_html(first_file)