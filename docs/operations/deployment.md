# デプロイ手順

このドキュメントでは、orchestrator-cc を環境にデプロイする手順について説明します。

**注意**: 2026-02-07をもって、tmux方式からAgent Teams方式へ完全移行しました。古いtmux方式のデプロイ手順は `docs/archive/` にアーカイブされています。

---

## 現在の状況

### ローカル実行のみ対応

現在、orchestrator-cc はローカル環境での実行に対応しています。Agent Teams は Claude Code Desktop 内で動作し、ダッシュボードは FastAPI サーバーで起動します。

**制限事項**:
- Docker コンテナ化未対応（Claude Code Desktopが必要）
- システムサービス化未対応
- 自動デプロイスクリプト未対応

---

## 推奨されるデプロイ方法

### 方法1: 直接デプロイ（現在利用可能）

#### 前提条件

```bash
# システム要件確認
python3 --version    # 3.10+
claude --version     # Claude Codeがインストールされていること
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

# 4. ダッシュボードの起動
python -m orchestrator.web.dashboard

# 5. ブラウザでアクセス
open http://localhost:8000
```

---

### 方法2: systemd サービス化（推奨、実装必要）

Linux 環境では、systemd サービスとして登録することで、システム起動時の自動起動やプロセス管理が可能になります。

#### サービスファイルの作成

**提案**: `/etc/systemd/system/orchestrator-cc-dashboard.service`

```ini
[Unit]
Description=Orchestrator CC Dashboard
After=network.target

[Service]
Type=simple
User=orchestrator
Group=orchestrator
WorkingDirectory=/opt/orchestrator-cc
Environment="PATH=/opt/orchestrator-cc/venv/bin:/usr/bin:/bin"
Environment="ORCHESTRATOR_LOG_LEVEL=INFO"
Environment="ORCHESTRATOR_DASHBOARD_PORT=8000"
ExecStart=/opt/orchestrator-cc/venv/bin/python -m orchestrator.web.dashboard
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### サービスの有効化

```bash
# サービスファイルの配置
sudo cp orchestrator-cc-dashboard.service /etc/systemd/system/

# サービスのリロード
sudo systemctl daemon-reload

# サービスの有効化（自動起動設定）
sudo systemctl enable orchestrator-cc-dashboard

# サービスの起動
sudo systemctl start orchestrator-cc-dashboard

# ステータス確認
sudo systemctl status orchestrator-cc-dashboard

# ログの確認
sudo journalctl -u orchestrator-cc-dashboard -f
```

---

### 方法3: launchd サービス化（macOS、実装必要）

macOS 環境では、launchd でサービスを管理します。

#### 提案: ~/Library/LaunchAgents/com.orchestrator-cc.dashboard.plist

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.orchestrator-cc.dashboard</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/orchestrator-cc/venv/bin/python</string>
        <string>-m</string>
        <string>orchestrator.web.dashboard</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/opt/orchestrator-cc</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/opt/orchestrator-cc/logs/dashboard.log</string>
    <key>StandardErrorPath</key>
    <string>/opt/orchestrator-cc/logs/dashboard.error</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>ORCHESTRATOR_LOG_LEVEL</key>
        <string>INFO</string>
        <key>ORCHESTRATOR_DASHBOARD_PORT</key>
        <string>8000</string>
    </dict>
</dict>
</plist>
```

#### サービスの登録

```bash
# plist ファイルのコピー
cp com.orchestrator-cc.dashboard.plist ~/Library/LaunchAgents/

# サービスの読み込み
launchctl load ~/Library/LaunchAgents/com.orchestrator-cc.dashboard.plist

# サービスの起動
launchctl start com.orchestrator-cc.dashboard

# サービスの停止
launchctl stop com.orchestrator-cc.dashboard

# サービスの削除
launchctl unload ~/Library/LaunchAgents/com.orchestrator-cc.dashboard.plist
```

---

## 本番環境設定

### ディレクトリ構成

```bash
# 本番用ディレクトリ構造
/opt/orchestrator-cc/
├── orchestrator/               # メインパッケージ
├── logs/                       # ログファイル
├── venv/                       # Python仮想環境
└── README.md
```

### 環境変数の設定

**提案**: `.env` ファイルまたは環境変数で設定

```bash
# .env
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

# macOS (Application Firewall)
# システム設定 > セキュリティとプライバシー > ファイアウォール
```

---

## ヘルスチェック

### ダッシュボードステータス確認

```bash
# API からの確認
curl http://localhost:8000/api/health

# 出力例
# {"status": "healthy", "version": "2.0.0"}
```

### systemd サービスの監視

```bash
# サービスステータス
sudo systemctl status orchestrator-cc-dashboard

# ジャーナルログ
sudo journalctl -u orchestrator-cc-dashboard -f
```

---

## ロールバック手順

### システムの復元

```bash
# 1. サービスの停止
sudo systemctl stop orchestrator-cc-dashboard

# 2. 以前のバージョンの復元
git checkout <previous-version>

# 3. 依存関係の再インストール
pip install -e .

# 4. サービスの再開
sudo systemctl start orchestrator-cc-dashboard
```

---

## 関連ドキュメント

- [configuration.md](configuration.md) - 設定管理
- [security.md](security.md) - セキュリティ設定
- [troubleshooting.md](troubleshooting.md) - トラブルシューティング
