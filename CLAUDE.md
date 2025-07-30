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