"""
Phase 6.5: HTMLファイル解析モジュール
"""

from bs4 import BeautifulSoup
import re
import json
import os

def analyze_hermes_html(html_file='hermes_page.html', log_func=print):
    """
    保存されたHTMLファイルを解析して商品情報を抽出
    
    Args:
        html_file: HTMLファイルのパス
        log_func: ログ出力関数
        
    Returns:
        dict: 抽出結果（成功/失敗、商品リスト）
    """
    
    if not os.path.exists(html_file):
        log_func(f"❌ HTMLファイルが見つかりません: {html_file}")
        return {'success': False, 'products': [], 'error': 'HTMLファイルが存在しません'}
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        products = []
        
        # 複数の方法で商品情報を抽出
        
        # 方法1: h-grid-result-item要素から
        grid_items = soup.find_all('h-grid-result-item')
        log_func(f"  h-grid-result-item要素: {len(grid_items)}個発見")
        
        if grid_items:
            for item in grid_items:
                product = extract_from_grid_item(item)
                if product and product.get('name') != 'N/A':
                    products.append(product)
        
        # 方法2: 商品リンクから直接
        if not products:
            log_func("  方法1で抽出失敗。方法2（商品リンク直接）を試行...")
            product_links = soup.find_all('a', href=re.compile(r'/jp/ja/product/'))
            log_func(f"  商品リンク: {len(product_links)}個発見")
            
            for link in product_links[:20]:  # 最大20個
                product = extract_from_link(link, soup)
                if product and product.get('name') != 'N/A':
                    products.append(product)
        
        # 方法3: テキストパターンマッチング
        if not products:
            log_func("  方法2でも失敗。方法3（パターンマッチング）を試行...")
            products = extract_by_pattern(html_content)
        
        if products:
            log_func(f"  ✅ {len(products)}個の商品情報を抽出成功")
            return {'success': True, 'products': products}
        else:
            log_func("  ⚠️ 商品情報の抽出に失敗")
            return {'success': False, 'products': [], 'error': '商品情報が見つかりません'}
            
    except Exception as e:
        log_func(f"  ❌ 解析エラー: {str(e)}")
        return {'success': False, 'products': [], 'error': str(e)}

def extract_from_grid_item(item):
    """h-grid-result-item要素から商品情報を抽出"""
    product = {
        'name': 'N/A',
        'url': '',
        'price': 'N/A',
        'color': '',
        'sku': ''
    }
    
    # リンクを探す
    link = item.find('a', id=re.compile(r'product-item-meta'))
    if link:
        product['url'] = link.get('href', '')
        if product['url']:
            # SKU抽出
            match = re.search(r'/product/([^/]+)', product['url'])
            if match:
                product['sku'] = match.group(1)
    
    # 商品名を探す（複数の方法）
    # 内部のすべてのテキストを調査
    texts = item.find_all(text=True)
    for text in texts:
        text = text.strip()
        if text and len(text) > 10:
            # 商品名のパターン
            if any(keyword in text for keyword in ['財布', 'バッグ', '《', '》']):
                product['name'] = text
                break
    
    # 価格を探す
    price_pattern = re.compile(r'¥[\d,]+')
    price_match = price_pattern.search(str(item))
    if price_match:
        product['price'] = price_match.group()
    
    return product

def extract_from_link(link, soup):
    """商品リンクから情報を抽出"""
    product = {
        'name': 'N/A',
        'url': link.get('href', ''),
        'price': 'N/A',
        'color': '',
        'sku': ''
    }
    
    # SKU抽出
    if product['url']:
        match = re.search(r'/product/([^/]+)', product['url'])
        if match:
            product['sku'] = match.group(1)
    
    # リンクの親要素から情報を探す
    parent = link.find_parent()
    while parent and parent.name != 'body':
        # 商品名を探す
        if product['name'] == 'N/A':
            for text_elem in parent.find_all(text=True):
                text = text_elem.strip()
                if text and any(kw in text for kw in ['財布', 'バッグ', '《', '》']):
                    product['name'] = text
                    break
        
        # 価格を探す
        if product['price'] == 'N/A':
            price_match = re.search(r'¥[\d,]+', str(parent))
            if price_match:
                product['price'] = price_match.group()
        
        parent = parent.find_parent()
    
    return product

def extract_by_pattern(html_content):
    """正規表現パターンマッチングで抽出"""
    products = []
    
    # 商品パターンを定義
    pattern = re.compile(
        r'href="(/jp/ja/product/[^"]+)"[^>]*>.*?'
        r'((?:財布|バッグ|ケリー|バーキン)[^<]+)',
        re.DOTALL | re.IGNORECASE
    )
    
    matches = pattern.findall(html_content)
    for i, (url, name) in enumerate(matches[:20]):
        if i >= 20:
            break
        
        product = {
            'name': name.strip(),
            'url': url,
            'price': 'N/A',
            'color': '',
            'sku': ''
        }
        
        # SKU抽出
        match = re.search(r'/product/([^/]+)', url)
        if match:
            product['sku'] = match.group(1)
        
        products.append(product)
    
    return products