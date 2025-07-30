FROM python:3.10-slim

# システムパッケージの更新とChromiumの依存関係をインストール
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    gnupg \
    fonts-liberation \
    fonts-roboto \
    fonts-noto-cjk \
    xvfb \
    libnss3 \
    libgconf-2-4 \
    libxss1 \
    libxtst6 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcairo-gobject2 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    libxext6 \
    libxfixes3 \
    libxrender1 \
    ca-certificates \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Chromiumのパスと環境変数を設定
ENV CHROMIUM_PATH=/usr/bin/chromium \
    DISPLAY=:99 \
    CHROME_BIN=/usr/bin/chromium \
    CHROME_PATH=/usr/bin/chromium

# ユーザーの作成（権限問題を回避）
RUN useradd -m -u 1000 -s /bin/bash user

# アプリケーション用ディレクトリの作成と権限設定
RUN mkdir -p /home/user/app /home/user/.cache /home/user/.local \
    && chown -R user:user /home/user

USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONPATH=/home/user/app

WORKDIR $HOME/app

# 依存関係のインストール
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --user -r requirements.txt

# アプリケーションファイルのコピー
COPY --chown=user:user . .

# ポートを公開
EXPOSE 7860

# アプリケーション実行コマンド
CMD ["python", "app.py"]