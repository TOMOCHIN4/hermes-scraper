"""
Phase 6.5: HTML解析機能
"""
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
from .utils import create_logger


class HermesParser:
    """保存されたHTMLファイルを解析するクラス"""
    
    def __init__(self):
        self.logger = create_logger()
        self.products = []
    
    def parse_html_file(self, filename='hermes_page.html'):
        """HTMLファイルを解析して商品情報を抽出"""
        self.logger.log("\n=== Phase 6.5: HTML解析 ===")
        self.logger.log(f"対象ファイル: {filename}")
        
        if not os.path.exists(filename):
            self.logger.log(f"❌ ファイルが見つかりません: {filename}")
            return False
        
        try:
            # HTMLファイルを読み込み
            with open(filename, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            self.logger.log(f"✅ ファイル読み込み成功: {len(html_content):,} bytes")
            
            # BeautifulSoupで解析
            soup = BeautifulSoup(html_content, 'lxml')
            
            # 商品要素を検索
            product_items = soup.find_all('h-grid-result-item')
            self.logger.log(f"📊 検出された商品数: {len(product_items)}")
            
            # 各商品の情報を抽出
            for idx, item in enumerate(product_items):
                product_data = self._extract_product_info(item, idx + 1)
                if product_data:
                    self.products.append(product_data)
            
            self.logger.log(f"\n✅ 解析完了: {len(self.products)}個の商品情報を抽出")
            
            # 結果を保存
            self._save_results()
            
            return True
            
        except Exception as e:
            self.logger.log(f"❌ 解析エラー: {e}")
            return False
    
    def _extract_product_info(self, item, index):
        """個別の商品情報を抽出"""
        try:
            product = {
                'index': index,
                'name': 'N/A',
                'url': 'N/A',
                'price': 'N/A',
                'colors': [],
                'sku': 'N/A'
            }
            
            # 商品リンクとURL
            link = item.find('a')
            if link and link.get('href'):
                product['url'] = f"https://www.hermes.com{link['href']}" if link['href'].startswith('/') else link['href']
            
            # 商品名（複数の可能性を試行）
            name_selectors = [
                ('h3', None),
                ('h2', None),
                (None, 'product-name'),
                (None, 'product-title'),
                (None, 'title')
            ]
            
            for tag, class_name in name_selectors:
                if tag:
                    name_elem = item.find(tag, class_=class_name) if class_name else item.find(tag)
                else:
                    name_elem = item.find(class_=class_name)
                
                if name_elem and name_elem.text.strip():
                    product['name'] = name_elem.text.strip()
                    break
            
            # 価格情報
            price_selectors = [
                (None, 'price'),
                (None, 'product-price'),
                (None, 'amount'),
                ('span', 'price'),
                ('div', 'price')
            ]
            
            for tag, class_name in price_selectors:
                if tag:
                    price_elem = item.find(tag, class_=class_name)
                else:
                    price_elem = item.find(class_=class_name)
                
                if price_elem and price_elem.text.strip():
                    product['price'] = price_elem.text.strip()
                    break
            
            # カラー情報
            color_elements = item.find_all(class_='color') or item.find_all(attrs={'data-color': True})
            for color_elem in color_elements:
                color_value = color_elem.get('data-color') or color_elem.text.strip()
                if color_value:
                    product['colors'].append(color_value)
            
            # SKU/商品ID
            sku_elem = item.find(attrs={'data-sku': True}) or item.find(class_='sku')
            if sku_elem:
                product['sku'] = sku_elem.get('data-sku') or sku_elem.text.strip()
            
            return product
            
        except Exception as e:
            self.logger.log(f"  ⚠️ 商品{index}の解析エラー: {e}")
            return None
    
    def _save_results(self):
        """解析結果を保存"""
        if not self.products:
            self.logger.log("⚠️ 保存する商品データがありません")
            return
        
        # JSON形式で保存
        filename = 'hermes_products.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'extraction_date': datetime.now().isoformat(),
                'total_products': len(self.products),
                'products': self.products
            }, f, ensure_ascii=False, indent=2)
        
        self.logger.log(f"💾 JSONファイル保存: {filename}")
    
    def get_results(self):
        """解析結果を取得"""
        return self.logger.get_results()
    
    def get_products(self):
        """抽出した商品リストを取得"""
        return self.products