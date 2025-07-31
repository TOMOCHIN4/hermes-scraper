# 新商品読み込み監視方法の詳細設計

## 1. 基本的な監視方法

### 方法1: 商品数の変化を監視
```javascript
// クリック前の商品数を記録
const initialCount = await tab.evaluate('document.querySelectorAll("h-grid-result-item").length');

// クリック実行
await tab.evaluate('document.querySelector(\'button[data-testid="Load more items"]\').click()');

// 商品数の変化を監視
let newCount = initialCount;
for (let i = 0; i < 20; i++) {  // 最大10秒待機
    await asyncio.sleep(0.5);
    newCount = await tab.evaluate('document.querySelectorAll("h-grid-result-item").length');
    if (newCount > initialCount) {
        console.log(`新商品検出: ${initialCount} → ${newCount}`);
        break;
    }
}
```

### 方法2: 最後の商品要素のIDを追跡
```javascript
// クリック前の最後の商品IDを記録
const lastProductId = await tab.evaluate('''
    const items = document.querySelectorAll('h-grid-result-item');
    const lastItem = items[items.length - 1];
    const link = lastItem ? lastItem.querySelector('a[id^="product-item-meta-"]') : null;
    return link ? link.id : null;
''');

// クリック後、新しい商品が追加されたか確認
const hasNewProducts = await tab.evaluate(`
    const items = document.querySelectorAll('h-grid-result-item');
    let foundOldLast = false;
    for (let item of items) {
        const link = item.querySelector('a[id^="product-item-meta-"]');
        if (link && link.id === '${lastProductId}') {
            foundOldLast = true;
        } else if (foundOldLast && link) {
            // 古い最後の要素の後に新しい要素がある
            return true;
        }
    }
    return false;
`);
```

## 2. 高度な監視方法

### 方法3: MutationObserverを使用（最も確実）
```javascript
// MutationObserverを設定してDOM変更を監視
await tab.evaluate('''
    window.newProductsAdded = false;
    window.addedProductCount = 0;
    
    // 既存の商品IDを記録
    window.existingProductIds = new Set();
    document.querySelectorAll('h-grid-result-item a[id^="product-item-meta-"]').forEach(link => {
        window.existingProductIds.add(link.id);
    });
    
    // MutationObserverを設定
    window.productObserver = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === 1 && node.tagName === 'H-GRID-RESULT-ITEM') {
                    const link = node.querySelector('a[id^="product-item-meta-"]');
                    if (link && !window.existingProductIds.has(link.id)) {
                        window.newProductsAdded = true;
                        window.addedProductCount++;
                        window.existingProductIds.add(link.id);
                    }
                }
            });
        });
    });
    
    // 監視開始
    const container = document.querySelector('h-grid-results');
    if (container) {
        window.productObserver.observe(container, { 
            childList: true, 
            subtree: true 
        });
    }
''');

// クリック実行
await tab.evaluate('document.querySelector(\'button[data-testid="Load more items"]\').click()');

// 新商品の追加を待機
for (let i = 0; i < 20; i++) {
    await asyncio.sleep(0.5);
    const result = await tab.evaluate('({ added: window.newProductsAdded, count: window.addedProductCount })');
    if (result.added) {
        console.log(`新商品${result.count}個を検出`);
        break;
    }
}

// オブザーバーをクリーンアップ
await tab.evaluate('if (window.productObserver) window.productObserver.disconnect()');
```

### 方法4: ネットワーク要求の完了を監視
```javascript
// Fetchをインターセプトしてネットワーク要求を監視
await tab.evaluate('''
    window.pendingRequests = 0;
    window.lastRequestCompleted = null;
    
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        window.pendingRequests++;
        return originalFetch.apply(this, args)
            .then(response => {
                window.pendingRequests--;
                window.lastRequestCompleted = Date.now();
                // 商品データのAPIかチェック
                if (args[0].includes('/search') || args[0].includes('/products')) {
                    window.productDataLoaded = true;
                }
                return response;
            })
            .catch(error => {
                window.pendingRequests--;
                throw error;
            });
    };
''');

// ネットワーク要求の完了を待つ
const waitForNetwork = async () => {
    for (let i = 0; i < 20; i++) {
        await asyncio.sleep(0.5);
        const status = await tab.evaluate('({ pending: window.pendingRequests, loaded: window.productDataLoaded })');
        if (status.pending === 0 && status.loaded) {
            return true;
        }
    }
    return false;
};
```

## 3. 複合的な監視戦略

### 最も堅牢な実装
```python
async def wait_for_new_products(tab, timeout=10):
    """新商品の読み込みを複数の方法で監視"""
    
    # 1. 初期状態を記録
    initial_state = await tab.evaluate('''
        (function() {
            const items = document.querySelectorAll('h-grid-result-item');
            const lastItem = items[items.length - 1];
            const lastLink = lastItem ? lastItem.querySelector('a[id^="product-item-meta-"]') : null;
            
            return {
                count: items.length,
                lastId: lastLink ? lastLink.id : null,
                scrollHeight: document.body.scrollHeight,
                buttonDisabled: document.querySelector('button[data-testid="Load more items"]')?.disabled || false
            };
        })()
    ''')
    
    # 2. MutationObserverを設定
    await tab.evaluate('''
        window.loadMoreStatus = {
            newItemsAdded: false,
            addedCount: 0,
            isLoading: false,
            error: null
        };
        
        // ローディング状態の検出
        const checkLoadingIndicators = () => {
            const indicators = document.querySelectorAll('.loading, .spinner, [class*="loading"]');
            return indicators.length > 0;
        };
        
        window.loadMoreStatus.isLoading = checkLoadingIndicators();
        
        // MutationObserverで変更を監視
        const observer = new MutationObserver((mutations) => {
            // 新商品の検出
            const currentItems = document.querySelectorAll('h-grid-result-item');
            if (currentItems.length > window.loadMoreStatus.initialCount) {
                window.loadMoreStatus.newItemsAdded = true;
                window.loadMoreStatus.addedCount = currentItems.length - window.loadMoreStatus.initialCount;
            }
            
            // ローディング状態の更新
            window.loadMoreStatus.isLoading = checkLoadingIndicators();
        });
        
        window.loadMoreStatus.initialCount = document.querySelectorAll('h-grid-result-item').length;
        observer.observe(document.body, { childList: true, subtree: true });
        window.loadMoreObserver = observer;
    ''')
    
    # 3. 監視ループ
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        status = await tab.evaluate('window.loadMoreStatus')
        
        # 成功: 新商品が追加された
        if status['newItemsAdded']:
            await tab.evaluate('window.loadMoreObserver.disconnect()')
            return {
                'success': True,
                'added_count': status['addedCount'],
                'method': 'mutation_observer'
            }
        
        # ローディング中から完了への変化を検出
        if not status['isLoading'] and initial_state['buttonDisabled']:
            # ボタンが再度有効になったかチェック
            button_enabled = await tab.evaluate('''
                const btn = document.querySelector('button[data-testid="Load more items"]');
                btn && !btn.disabled && btn.getAttribute('aria-disabled') !== 'true'
            ''')
            
            if button_enabled:
                # DOM更新を待つ
                await asyncio.sleep(0.5)
                
                # 最終的な商品数をチェック
                final_count = await tab.evaluate('document.querySelectorAll("h-grid-result-item").length')
                if final_count > initial_state['count']:
                    await tab.evaluate('window.loadMoreObserver.disconnect()')
                    return {
                        'success': True,
                        'added_count': final_count - initial_state['count'],
                        'method': 'button_state_change'
                    }
        
        await asyncio.sleep(0.5)
    
    # タイムアウト
    await tab.evaluate('window.loadMoreObserver.disconnect()')
    return {
        'success': False,
        'reason': 'timeout',
        'final_count': await tab.evaluate('document.querySelectorAll("h-grid-result-item").length')
    }
```

## 4. エラー検出と対処

### 監視中のエラー検出
```javascript
// エラー状態の検出
const errorDetection = await tab.evaluate('''
    (function() {
        // エラーメッセージの検出
        const errorSelectors = [
            '.error-message',
            '[class*="error"]',
            '[data-testid="error"]',
            '.alert-danger'
        ];
        
        for (let selector of errorSelectors) {
            const errorElement = document.querySelector(selector);
            if (errorElement && errorElement.offsetParent !== null) {
                return {
                    hasError: true,
                    errorText: errorElement.textContent.trim()
                };
            }
        }
        
        // ボタンが予期せず消えた場合
        const button = document.querySelector('button[data-testid="Load more items"]');
        if (!button && document.querySelectorAll('h-grid-result-item').length < 100) {
            return {
                hasError: true,
                errorText: 'Load more button disappeared unexpectedly'
            };
        }
        
        return { hasError: false };
    })()
''');
```

## 5. パフォーマンス監視

### 読み込み時間の計測
```javascript
const performanceMetrics = await tab.evaluate('''
    (function() {
        // Navigation Timing API
        const navTiming = performance.getEntriesByType('navigation')[0];
        
        // Resource Timing API（最新のAPI呼び出し）
        const resources = performance.getEntriesByType('resource');
        const apiCalls = resources.filter(r => 
            r.name.includes('/api/') || r.name.includes('/search')
        ).slice(-5);  // 最新5件
        
        return {
            pageLoadTime: navTiming ? navTiming.loadEventEnd - navTiming.fetchStart : null,
            recentApiCalls: apiCalls.map(r => ({
                url: r.name,
                duration: r.duration,
                size: r.transferSize
            }))
        };
    })()
''');
```

## 推奨実装

最も信頼性の高い監視方法は**MutationObserver**と**商品数カウント**の組み合わせです。

1. MutationObserverで即座にDOM変更を検出
2. 商品数で確実に新商品追加を確認
3. エラー状態も同時に監視
4. タイムアウトで無限待機を防ぐ