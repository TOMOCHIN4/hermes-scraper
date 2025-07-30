FROM python:3.10-slim

# システムパッケージの更新とChromiumのインストール
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    gnupg \
    fonts-liberation \
    fonts-roboto \
    xvfb \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Chromiumのパスを設定
ENV CHROMIUM_PATH=/usr/bin/chromium

# ユーザーの作成（権限問題を回避）
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# 依存関係のインストール
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# アプリケーションファイルのコピー
COPY --chown=user . .

# ポートを公開
EXPOSE 7860

# アプリケーション実行コマンド
CMD ["python", "app.py"]