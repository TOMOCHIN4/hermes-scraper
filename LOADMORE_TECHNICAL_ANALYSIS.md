# 「アイテムをもっと見る」ボタン技術分析

## 1. ボタンの技術仕様

### HTML構造
```html
<h-call-to-action _ngcontent-hermes-c3567160471="" _nghost-hermes-c760651711="" class="ng-star-inserted">
  <button _ngcontent-hermes-c760651711="" 
          class="border-radius-default button-base button-secondary height-normal label-large-uppercase size-large" 
          type="button" 
          name="undefined" 
          aria-disabled="false" 
          data-testid="Load more items">
    <div _ngcontent-hermes-c760651711="" class="button-content-container ng-star-inserted">
      <span _ngcontent-hermes-c760651711="" class="svg-left"></span>
      アイテムをもっと見る
      <span _ngcontent-hermes-c760651711="" class="svg-right"></span>
    </div>
    <span _ngcontent-hermes-c760651711="" class="svg-center ng-star-inserted"></span>
  </button>
</h-call-to-action>
```

### 重要な属性
- **data-testid**: "Load more items" （最も信頼できるセレクタ）
- **aria-disabled**: ボタンの有効/無効状態を示す
- **_ngcontent-hermes-***: Angularコンポーネントの識別子

## 2. 実装における技術的考慮事項

### ボタンクリックの実装
```javascript
// 推奨実装
const button = await tab.evaluate('''
  const btn = document.querySelector('button[data-testid="Load more items"]');
  if (btn && !btn.disabled && btn.getAttribute('aria-disabled') !== 'true') {
    btn.click();
    return true;
  }
  return false;
''');
```

### クリック後の挙動予測

1. **即座の変化**
   - ボタンが無効化される（aria-disabled="true"）
   - ローディングインジケーターが表示される可能性

2. **データ読み込み**
   - APIコール（おそらく `/api/search` または類似のエンドポイント）
   - 次の48商品を取得

3. **DOM更新**
   - 新しい `h-grid-result-item` 要素が追加される
   - スクロール位置は維持される

4. **完了後**
   - まだ商品がある場合：ボタンが再度有効化
   - 全商品表示済みの場合：ボタンが非表示または削除

## 3. セキュリティ回避のベストプラクティス

### 人間らしい操作の模倣
```javascript
// 1. スクロールしてボタンを表示
await tab.evaluate('window.scrollTo(0, document.body.scrollHeight - 1000)');
await asyncio.sleep(1.5);  // 人間の反応時間

// 2. ボタンの位置を確認
const buttonPosition = await tab.evaluate('''
  const btn = document.querySelector('button[data-testid="Load more items"]');
  const rect = btn.getBoundingClientRect();
  return {
    visible: rect.top < window.innerHeight && rect.bottom > 0,
    center: { x: rect.left + rect.width/2, y: rect.top + rect.height/2 }
  };
''');

// 3. 必要に応じて追加スクロール
if (!buttonPosition.visible) {
  await tab.evaluate('document.querySelector("button[data-testid=\'Load more items\']").scrollIntoView({behavior: "smooth"})');
  await asyncio.sleep(1);
}

// 4. クリック
```

### レート制限対策
- 各クリック間に**3-5秒**の待機時間
- ランダムな待機時間の導入（2.5-4.5秒など）
- 一度に全商品を読み込もうとしない

## 4. 実装フロー提案

```python
async def load_all_products(tab, max_clicks=10):
    """全商品を段階的に読み込む"""
    
    loaded_products = set()  # 重複チェック用
    click_count = 0
    
    while click_count < max_clicks:
        # 1. 現在の商品数を取得
        current_count = await tab.evaluate('document.querySelectorAll("h-grid-result-item").length')
        
        # 2. ボタンの状態を確認
        button_state = await tab.evaluate('''
          (function() {
            const btn = document.querySelector('button[data-testid="Load more items"]');
            return {
              exists: !!btn,
              visible: btn ? btn.offsetParent !== null : false,
              disabled: btn ? (btn.disabled || btn.getAttribute('aria-disabled') === 'true') : true
            };
          })()
        ''')
        
        # 3. ボタンがない、または無効なら終了
        if not button_state['exists'] or not button_state['visible'] or button_state['disabled']:
            print(f"Load complete: {current_count} products loaded")
            break
        
        # 4. スクロールしてボタンを表示
        await tab.evaluate('window.scrollTo(0, document.body.scrollHeight - 500)')
        await asyncio.sleep(random.uniform(1.5, 2.5))  # 人間らしい待機
        
        # 5. ボタンクリック
        clicked = await tab.evaluate('''
          const btn = document.querySelector('button[data-testid="Load more items"]');
          if (btn) { btn.click(); return true; }
          return false;
        ''')
        
        if not clicked:
            print("Failed to click Load More button")
            break
        
        click_count += 1
        print(f"Click #{click_count}: Loading more products...")
        
        # 6. 新しい商品の読み込みを待つ
        await asyncio.sleep(2)  # 初期待機
        
        # 商品数の変化を監視（最大10秒）
        for i in range(8):
            new_count = await tab.evaluate('document.querySelectorAll("h-grid-result-item").length')
            if new_count > current_count:
                print(f"  Loaded {new_count - current_count} new products")
                break
            await asyncio.sleep(1)
        
        # 7. レート制限対策の待機
        await asyncio.sleep(random.uniform(2, 4))
    
    return current_count
```

## 5. エラーハンドリング

### 想定されるエラーと対策

1. **セキュリティブロック**
   - 症状：ページがリダイレクトまたはCAPTCHA表示
   - 対策：より長い待機時間、User-Agentの調整

2. **ボタンが見つからない**
   - 症状：セレクタが一致しない
   - 対策：複数のセレクタを試す、DOM構造の再確認

3. **無限ループ**
   - 症状：同じ商品が繰り返し読み込まれる
   - 対策：商品IDの重複チェック、最大クリック数の設定

## 6. パフォーマンス最適化

- 商品データは増分で保存（メモリ効率）
- 大量の商品がある場合は分割処理
- 不要なDOM要素（画像など）の遅延読み込みを活用

## 7. 今後の実装ステップ

1. **Phase 6.1**: Load Moreボタンの単一クリックテスト
2. **Phase 6.2**: 複数回クリックによる段階的読み込み
3. **Phase 6.3**: エラーハンドリングとリトライロジック
4. **Phase 6.4**: 全商品データの効率的な抽出と保存