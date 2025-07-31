# Phase 6.5 実装計画

## 背景
Phase 6.0では以下を達成しました：
- ✅ エルメスサイトへの接続成功
- ✅ JavaScript描画後の完全なHTMLファイルの保存（約500KB）
- ✅ 48個の商品URLの抽出
- ❌ 商品詳細情報（名前、価格、カラー）が "N/A"

**重要**: Phase 1-5は完璧に動作。問題はPhase 6の商品詳細抽出のみ。

## Phase 6.5の目的
商品の詳細情報を正確に抽出できるようにする

## 実装方針（3つのアプローチ）

### アプローチ1: HTMLファイル解析の強化（推奨）
**メリット**:
- 既に保存済みのHTMLを活用
- サイトへの追加アクセス不要
- 高速な開発とテストが可能

**実装内容**:
```python
# BeautifulSoupでの詳細解析
from bs4 import BeautifulSoup

def analyze_saved_html():
    with open('hermes_page.html', 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    # Angular属性の活用
    products = soup.find_all('h-grid-result-item')
    
    # データ属性の探索
    for product in products:
        # ng-reflect-* 属性
        # data-* 属性
        # 隠れた価格情報の探索
```

### アプローチ2: JavaScript変数の直接抽出
**メリット**:
- Angularのデータストアに直接アクセス
- レンダリング前の生データ取得

**実装内容**:
```javascript
// Angularコンポーネントからのデータ取得
const angularElements = document.querySelectorAll('[_ngcontent-*]');
const componentData = [];

// window オブジェクトの探索
if (window.__hermes_data__) {
    return window.__hermes_data__;
}
```

### アプローチ3: 個別商品ページへのアクセス
**メリット**:
- 最も確実な情報取得
- 在庫情報なども取得可能

**デメリット**:
- 時間がかかる（48ページ × 数秒）
- レート制限のリスク

## 推奨実装順序

1. **Phase 6.5a**: HTMLファイル解析の強化
   - BeautifulSoupでの詳細パース
   - 正規表現での価格抽出
   - データ属性の完全探索

2. **Phase 6.5b**: JavaScript実行での追加情報取得
   - Angular変数へのアクセス
   - 動的生成されたデータの取得

3. **Phase 6.5c**: 個別ページアクセス（オプション）
   - 最初の5商品のみテスト
   - 成功したら全商品へ展開

## 成功指標

### 最小成功基準
- 商品名の50%以上で正確な名前を取得
- 価格情報の30%以上で数値を取得

### 理想的な成功基準
- 商品名の90%以上で正確な名前を取得
- 価格情報の80%以上で正確な価格を取得
- カラー情報の取得

## テスト方法

1. 保存済みのHTMLファイルを使用
2. 抽出結果を目視確認
3. CSVファイルでのデータ品質チェック

## リスクと対策

**リスク**: HTMLの構造が動的に変わる
**対策**: 複数のセレクタを用意し、フォールバック処理を実装

**リスク**: 価格が JavaScript で後から挿入される
**対策**: 複数の抽出方法を組み合わせる

## 実装開始の承認待ち

上記のアプローチ1（HTMLファイル解析の強化）から始めることを提案します。
ユーザーの承認をお待ちしています。