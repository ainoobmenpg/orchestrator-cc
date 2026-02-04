# デプロイ手順

このドキュメントでは、orchestrator-cc を本番環境にデプロイする手順について説明します。

---

## 現在の状況

### ローカル実行のみ対応

現在、orchestrator-cc はローカル環境での実行のみに対応しています。クラスタは tmux セッション内で動作し、ダッシュボードは開発用サーバーで起動します。

**制限事項**:
- Docker コンテナ化未対応
- システムサービス化未対応
- 自動デプロイスクリプト未対応

---

## 推奨されるデプロイ方法

### 方法1: 直接デプロイ（現在利用可能）

#### 前提条件

```bash
# システム要件確認
python3 --version    # 3.10+
tmux -V             # 3.0+
```

#### デプロイ手順

```bash
# 1. リポジトリのクローン
git clone https://github.com/your-org/orchestrator-cc.git
cd orchestrator-cc

# 2. Python 仮想環境の作成
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# または venv\Scripts\activate  # Windows

# 3. 依存関係のインストール
pip install -e .
pip install -r requirements-dev.txt

# 4. 設定ファイルの編集
vi config/cc-cluster.yaml
# work_dir をデプロイ先の絶対パスに変更

# 5. クラスタの起動
python -m orchestrator.cli start

# 6. ダッシュボードの起動（別のターミナルで）
python -m orchestrator.cli dashboard
```

#### 起動確認

```bash
# tmux セッションの確認
tmux ls

# ダッシュボードへのアクセス
# http://localhost:8000
```

---

### 方法2: systemd サービス化（推奨、実装必要）

Linux 環境では、systemd サービスとして登録することで、システム起動時の自動起動やプロセス管理が可能になります。

#### サービスファイルの作成

**提案**: `/etc/systemd/system/orchestrator-cc.service`

```ini
[Unit]
Description=Orchestrator CC Cluster
After=network.target tmux.service

[Service]
Type=forking
User=orchestrator
Group=orchestrator
WorkingDirectory=/opt/orchestrator-cc
Environment="PATH=/opt/orchestrator-cc/venv/bin:/usr/bin:/bin"
ExecStart=/opt/orchestrator-cc/venv/bin/python -m orchestrator.cli start
ExecStop=/opt/orchestrator-cc/venv/bin/python -m orchestrator.cli stop
ExecReload=/opt/orchestrator-cc/venv/bin/python -m orchestrator.cli restart
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**ダッシュボード用サービス**: `/etc/systemd/system/orchestrator-cc-dashboard.service`

```ini
[Unit]
Description=Orchestrator CC Dashboard
After=network.target orchestrator-cc.service

[Service]
Type=simple
User=orchestrator
Group=orchestrator
WorkingDirectory=/opt/orchestrator-cc
Environment="PATH=/opt/orchestrator-cc/venv/bin:/usr/bin:/bin"
ExecStart=/opt/orchestrator-cc/venv/bin/python -m orchestrator.cli dashboard
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### サービスの有効化

```bash
# サービスファイルの配置
sudo cp orchestrator-cc.service /etc/systemd/system/
sudo cp orchestrator-cc-dashboard.service /etc/systemd/system/

# サービスのリロード
sudo systemctl daemon-reload

# サービスの有効化（自動起動設定）
sudo systemctl enable orchestrator-cc
sudo systemctl enable orchestrator-cc-dashboard

# サービスの起動
sudo systemctl start orchestrator-cc
sudo systemctl start orchestrator-cc-dashboard

# ステータス確認
sudo systemctl status orchestrator-cc
sudo systemctl status orchestrator-cc-dashboard
```

---

### 方法3: Docker コンテナ化（推奨、実装必要）

Docker を使用することで、環境依存を排除し、デプロイを簡素化できます。

#### 提案: Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# システム依存関係のインストール
RUN apt-get update && apt-get install -y \
    tmux \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリの設定
WORKDIR /app

# 依存関係のコピーとインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのコピー
COPY . .

# パッケージのインストール
RUN pip install -e .

# ボリュームの設定
VOLUME ["/app/config", "/app/queue", "/app/status", "/app/logs"]

# ポートの設定
EXPOSE 8000

# デフォルトコマンド
CMD ["python", "-m", "orchestrator.cli", "start"]
```

#### 提案: docker-compose.yml

```yaml
version: '3.8'

services:
  orchestrator-cc:
    build: .
    container_name: orchestrator-cc
    restart: unless-stopped
    volumes:
      - ./config:/app/config
      - ./queue:/app/queue
      - ./status:/app/status
      - ./logs:/app/logs
    environment:
      - ORCHESTRATOR_WORK_DIR=/app
      - ORCHESTRATOR_CONFIG_PATH=/app/config/cc-cluster.yaml
    command: ["python", "-m", "orchestrator.cli", "start"]

  dashboard:
    build: .
    container_name: orchestrator-cc-dashboard
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config
      - ./queue:/app/queue
      - ./status:/app/status
      - ./logs:/app/logs
    environment:
      - ORCHESTRATOR_WORK_DIR=/app
      - ORCHESTRATOR_CONFIG_PATH=/app/config/cc-cluster.yaml
    command: ["python", "-m", "orchestrator.cli", "dashboard"]
    depends_on:
      - orchestrator-cc
```

#### Docker デプロイ手順

```bash
# イメージのビルド
docker-compose build

# サービスの起動
docker-compose up -d

# ログの確認
docker-compose logs -f

# サービスの停止
docker-compose down

# サービスの再起動
docker-compose restart
```

---

### 方法4: launchd サービス化（macOS、実装必要）

macOS 環境では、launchd でサービスを管理します。

#### 提案: ~/Library/LaunchAgents/orchestrator-cc.plist

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.orchestrator-cc</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/orchestrator-cc/venv/bin/python</string>
        <string>-m</string>
        <string>orchestrator.cli</string>
        <string>start</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/opt/orchestrator-cc</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/opt/orchestrator-cc/logs/orchestrator-cc.log</string>
    <key>StandardErrorPath</key>
    <string>/opt/orchestrator-cc/logs/orchestrator-cc.error</string>
</dict>
</plist>
```

#### サービスの登録

```bash
# plist ファイルのコピー
cp orchestrator-cc.plist ~/Library/LaunchAgents/

# サービスの読み込み
launchctl load ~/Library/LaunchAgents/orchestrator-cc.plist

# サービスの起動
launchctl start com.orchestrator-cc

# サービスの停止
launchctl stop com.orchestrator-cc

# サービスの削除
launchctl unload ~/Library/LaunchAgents/orchestrator-cc.plist
```

---

## 本番環境設定

### 設定ファイルの配置

```bash
# 本番用ディレクトリ構造
/opt/orchestrator-cc/
├── config/
│   ├── cc-cluster.yaml          # 本番環境設定
│   └── personalities/           # 性格プロンプト
├── queue/                       # YAML通信メッセージ
├── status/                      # エージェントステータス
├── logs/                        # ログファイル
└── venv/                        # Python仮想環境
```

### 環境変数の設定

**提案**: `.env` ファイルまたは環境変数で設定

```bash
# .env
ORCHESTRATOR_WORK_DIR=/opt/orchestrator-cc
ORCHESTRATOR_CONFIG_PATH=/opt/orchestrator-cc/config/cc-cluster.yaml
ORCHESTRATOR_LOG_LEVEL=INFO
ORCHESTRATOR_DASHBOARD_PORT=8000
ORCHESTRATOR_DASHBOARD_HOST=0.0.0.0
```

---

## ポートとファイアウォール

### デフォルトポート

| サービス | ポート | 説明 |
|---------|--------|------|
| ダッシュボード | 8000 | HTTP/WebSocket |

### ファイアウォール設定

```bash
# Ubuntu/Debian
sudo ufw allow 8000/tcp

# CentOS/RHEL
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload
```

---

## ヘルスチェック

### クラスタステータス確認

```bash
# CLI からの確認
python -m orchestrator.cli status

# API からの確認
curl http://localhost:8000/api/status
```

### systemd サービスの監視

```bash
# サービスステータス
sudo systemctl status orchestrator-cc

# ジャーナルログ
sudo journalctl -u orchestrator-cc -f
```

---

## ロールバック手順

### システムの復元

```bash
# 1. サービスの停止
sudo systemctl stop orchestrator-cc
sudo systemctl stop orchestrator-cc-dashboard

# 2. 以前のバージョンの復元
git checkout <previous-version>

# 3. 依存関係の再インストール
pip install -e .

# 4. サービスの再開
sudo systemctl start orchestrator-cc
sudo systemctl start orchestrator-cc-dashboard
```

---

## 関連ドキュメント

- [configuration.md](configuration.md) - 設定管理
- [security.md](security.md) - セキュリティ設定
- [troubleshooting.md](troubleshooting.md) - トラブルシューティング
