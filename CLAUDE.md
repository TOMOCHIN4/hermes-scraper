# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

このプロジェクトは、Hugging Face Spacesを使用したエルメス公式オンラインストア商品情報抽出アプリケーションの開発プロジェクトです。nodriverライブラリとChromiumを使用してWebスクレイピングを行い、Gradioでユーザーインターフェースを提供します。

**Hugging Face Space ID**: `tomo2chin2/Her`

## 技術スタック

- **フレームワーク**: Gradio (Webインターフェース)
- **Webスクレイピング**: nodriver + Chromium
- **実行環境**: Docker (Hugging Face Spaces)
- **言語**: Python 3.10

## プロジェクト構造

```
Hermes/
├── app.py                 # メインアプリケーション (予定)
├── requirements.txt       # Python依存関係 (予定) 
├── Dockerfile            # Docker設定 (予定)
├── README.md             # プロジェクト説明 (予定)
├── HF_TOKEN.txt          # Hugging Face認証情報
├── research1.txt         # 開発手順書・技術仕様書
└── download_sample/      # スクレイピングサンプルデータ
```

## 開発コマンド

### アプリケーション実行
```bash
python app.py
```

### Gradioアプリケーション（デフォルトポート）
- ローカル: http://localhost:7860
- サーバー: 0.0.0.0:7860

### Docker関連
```bash
# イメージビルド
docker build -t hermes-scraper .

# コンテナ実行
docker run -p 7860:7860 hermes-scraper
```

## 主要な機能仕様

### エルメス商品情報抽出
- プライベートモード（`--incognito`）でブラウザアクセス
- 商品名、URL、価格の自動抽出
- キーワード検索による絞り込み機能  
- 最大20商品の表示制限

### セレクタ仕様
- **商品名**: `.product-name`, `.product-title`, `h3`, `h2`, `.title`
- **商品URL**: `a[href]`要素
- **価格情報**: `.price`, `.product-price`, `[data-price]`, `.amount`

## 技術的な注意事項

### nodriverの設定
- ヘッドレスモード: `headless=True`  
- プライベートモード: `--incognito`
- セキュリティオプション: `--no-sandbox`, `--disable-dev-shm-usage`
- パフォーマンス: `--disable-images`, `--disable-plugins`

### Hugging Face Spaces配置要件
- SDKタイプ: Docker
- 必須ファイル: app.py, requirements.txt, Dockerfile, README.md
- ポート: 7860 (固定)

### スクレイピング規約
- エルメス公式サイト利用規約の遵守
- 過度なアクセス頻度の回避
- プライベートモードでの履歴・クッキー無効化

## セキュリティ考慮事項

- HF_TOKEN.txtは機密情報を含むため、リポジトリへのコミット禁止
- User-Agent文字列の設定でボット検出回避  
- アンチボット回避のためnodriverを使用（Seleniumより検出されにくい）

## 段階的開発計画（重要）

### 開発方針
**各Phase完了時にユーザーからの明確な合格承認が必要です。承認なしに次のPhaseには進みません。**

### Phase 1: 基本環境テスト 🔧
**目標**: Python/Docker環境の完全な動作確認
**合格基準**:
- Python 3.10が正常動作
- 全依存関係のインポート成功
- Docker環境でのファイル権限確認
- システム情報の正常取得

**実装内容**:
```python
# 基本環境テスト用の最小限アプリ
def test_basic_environment():
    print("=== Phase 1: 基本環境テスト ===")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"User: {os.getenv('USER', 'unknown')}")
    # 依存関係テスト
    try:
        import gradio as gr
        import nodriver as nd
        import asyncio
        import nest_asyncio
        print("✅ All dependencies imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False
```

### Phase 2: Chromium起動テスト 🌐
**目標**: Chromiumブラウザの単体起動確認
**合格基準**:
- Chromiumバイナリの存在確認
- 最小設定でのプロセス起動成功
- 適切なプロセス終了確認

**実装内容**:
```python
def test_chromium_startup():
    print("=== Phase 2: Chromium起動テスト ===")
    # Chromiumバイナリ確認
    # 最小設定での起動テスト
    # プロセス管理テスト
```

### Phase 3: nodriver基本動作テスト 🚀
**目標**: nodriverの最小限機能確認
**合格基準**:
- nodriver.start()の成功
- ローカルHTMLページでの動作確認
- 基本的なページ操作（title取得等）

### Phase 4: ネットワーク接続テスト 🔗
**目標**: 外部サイトへの接続確認
**合格基準**:
- DNS解決の成功
- HTTPS接続の確立
- 簡単なサイトでのページ取得

### Phase 5: JavaScript実行テスト ⚡
**目標**: DOM操作とスクレイピング機能
**合格基準**:
- JavaScript実行の成功
- DOM要素の取得・操作
- 基本的なデータ抽出

### Phase 6: エルメスサイト特化テスト 🛍️
**目標**: 実際のターゲットサイトでのテスト
**合格基準**:
- エルメスサイトへの接続
- 商品ページの構造解析
- 実際の商品データ抽出

### Phase 7: Gradioインターフェース統合 🎨
**目標**: UIとバックエンドの統合
**合格基準**:
- 完全なUI機能
- エラー表示の適切化
- ユーザビリティ確保

### Phase 8: 最終調整とエラーハンドリング ✨
**目標**: 本番環境向け最適化
**合格基準**:
- 安定したパフォーマンス
- 完全なエラーハンドリング
- 本番環境での継続動作

### 現在のステータス
**現在**: Phase 6実装完了（完全なHTMLダウンロード版）
**完了済み**: Phase 1-5全て合格、Phase 6.0/6.5全て合格
**次のアクション**: Phase 6の合格承認待ち → Phase 7へ

### 重要な変更履歴（2025-01-31）

#### Phase 6 最新実装（コミット: 75b58a0）
**主な機能**:
1. **Phase 6.0: HTMLダウンロード専用**
   - JavaScript描画後の完全なHTMLを`hermes_page.html`に保存
   - DOM解析は行わず、HTMLダウンロード成功後即座に終了
   - 495KB以上のHTMLファイルを正常に保存

2. **Phase 6.5: HTML解析専用**
   - BeautifulSoupで保存されたHTMLを解析
   - h-grid-result-item要素から48個の商品情報を抽出
   - JSON形式のみで保存（CSV/TXT形式は削除）

3. **抽出データ**
   - 商品名、URL、価格、カラー情報、SKU（商品ID）、総商品数

**技術的な改善**:
- Phase 6.0とPhase 6.5の役割を明確に分離
- DOM解析エラーを完全に排除
- ファイル形式をJSON単一に簡素化

### Phase 6.5: HTMLファイル解析の強化 🔍
**目標**: Phase 6.0で取得したJavaScript描画後のHTMLファイルを解析し、商品データベースを構築
**重要**: Phase 1-5は完璧に動作。Phase 6.0でJavaScript描画後のHTML取得は成功済み
**課題**: 保存されたHTMLファイルから商品詳細情報を正確に抽出する
**アプローチ**: BeautifulSoupやlxmlを使用したオフライン解析
**合格基準**:
- 商品名の正確な取得（現在は "N/A"）
- 価格情報の確実な抽出（現在は "N/A"）
- カラー・サイズ情報の取得
- 構造化されたデータベースの作成

### 重要な開発状況（2025-01-31）

#### Phase 1-5: 完璧に動作 ✅
- すべての基礎機能は正常動作
- 変更の必要なし

#### Phase 6.0: HTML取得は成功、解析が課題
**成功した部分**:
- JavaScript描画後のHTML取得 ✅
- 48個の商品URL抽出 ✅
- ファイル保存機能 ✅

**失敗した部分**:
- 商品名の取得（すべて "N/A"）❌
- 価格情報の取得（すべて "N/A"）❌
- カラー情報の取得（すべて空）❌

#### Phase 6 最新実装（コミット: eb33076）
**主な機能**:
1. **完全なHTMLダウンロード**
   - ページの完全なHTMLを`hermes_page.html`に保存
   - レンダリング後の完全なDOM構造を取得

2. **商品データの3形式出力**
   - **JSON形式** (`hermes_products.json`): プログラム利用向け
   - **CSV形式** (`hermes_products.csv`): Excel分析向け
   - **TXT形式** (`hermes_products.txt`): 人間が読みやすい形式

3. **抽出データ**
   - 商品名、URL、価格、カラー情報、SKU（商品ID）、総商品数

**技術的な改善**:
- nodriverのリスト形式データ処理を完全対応
- safe_get関数を改善（`[['key', {'value': xxx}]]`形式対応）
- ファイル名を固定化（タイムスタンプ削除）

#### Phase 6 変更履歴
**初期実装**（コミット: 39721d2）:
- hermes-state JSONデータの解析を試行
- 約1000行のコード

**簡素化版**（コミット: fe02d52）:
- HTML直接解析のみに一本化
- 約500行のコード（50%削減）

**最新版**（コミット: 2e135f2）:
- 完全なHTMLダウンロード機能追加
- 3形式でのデータ出力（JSON/CSV/TXT）

**元に戻す方法**:
```bash
git checkout 39721d2  # JSON解析版
git checkout fe02d52  # 簡素化版
git checkout 2e135f2  # 最新版（HTMLダウンロード版）
```

### 重要な開発ルール
1. **各Phaseは独立したテストアプリとして実装**
2. **ユーザーの明確な合格承認なしに次に進まない**
3. **問題発生時は前のPhaseに戻って再検証**
4. **全てのログと結果を詳細に記録**