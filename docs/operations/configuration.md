# 設定管理

このドキュメントでは、orchestrator-cc の設定管理について説明します。

---

## 現在の状況

### 設定ファイル方式

現在、orchestrator-cc は `config/cc-cluster.yaml` で設定を管理しています。

**設定項目**:
- クラスタ名
- tmux セッション名
- 作業ディレクトリ
- エージェント設定（名前、役割、性格プロンプト、マーカー、ペイン番号）

**制限事項**:
- 環境変数による設定の上書き未対応
- シークレット（APIキー等）の管理方法未定義
- 本番環境・開発環境の設定切り替え未対応

---

## 設定ファイル構成

### cc-cluster.yaml

```yaml
cluster:
  name: "orchestrator-cc"              # クラスタ名
  session_name: "orchestrator-cc"      # tmuxセッション名
  work_dir: "/path/to/orchestrator-cc" # 作業ディレクトリ

agents:
  - name: "grand_boss"
    role: "grand_boss"
    personality_prompt_path: "personalities/grand_boss.txt"
    marker: "GRAND BOSS OK"
    pane_index: 0
    # オプション
    wait_time: 5.0        # 初期化待機時間（秒）
    poll_interval: 0.5    # ポーリング間隔（秒）
```

### 設定項目一覧

#### cluster セクション

| 項目 | 型 | 必須 | 説明 |
|------|----|----|------|
| `name` | string | ✅ | クラスタ名 |
| `session_name` | string | ✅ | tmuxセッション名 |
| `work_dir` | string | ✅ | 作業ディレクトリの絶対パス |

#### agents セクション

| 項目 | 型 | 必須 | 説明 |
|------|----|----|------|
| `name` | string | ✅ | エージェントの一意な名前 |
| `role` | string | ✅ | エージェントの役割 |
| `personality_prompt_path` | string | ✅ | 性格プロンプトファイルのパス |
| `marker` | string | ✅ | 応答完了検出用のキーワード |
| `pane_index` | int | ✅ | tmuxペイン番号（0-4） |
| `wait_time` | float | ❌ | 初期化待機時間（秒、デフォルト5.0） |
| `poll_interval` | float | ❌ | ポーリング間隔（秒、デフォルト0.5） |

---

## 推奨される改善策

### 1. 環境変数対応

**提案**: 設定ファイルの値を環境変数で上書き可能にする

```bash
# 環境変数で設定を上書き
export ORCHESTRATOR_WORK_DIR=/opt/orchestrator-cc
export ORCHESTRATOR_SESSION_NAME=prod-cluster
export ORCHESTRATOR_DASHBOARD_PORT=8080
```

**実装例**:

```python
# orchestrator/core/config_loader.py
import os
from pathlib import Path

def load_config(config_path: str) -> CCClusterConfig:
    """設定ファイルを読み込み、環境変数で上書きします"""
    # YAMLファイルの読み込み
    with open(config_path) as f:
        data = yaml.safe_load(f)

    # 環境変数で上書き
    cluster_data = data["cluster"]
    cluster_data["work_dir"] = os.getenv(
        "ORCHESTRATOR_WORK_DIR",
        cluster_data["work_dir"]
    )
    cluster_data["session_name"] = os.getenv(
        "ORCHESTRATOR_SESSION_NAME",
        cluster_data["session_name"]
    )

    # ...
```

**サポートする環境変数**:

| 環境変数 | 説明 | デフォルト値 |
|---------|------|-------------|
| `ORCHESTRATOR_WORK_DIR` | 作業ディレクトリ | YAML設定値 |
| `ORCHESTRATOR_SESSION_NAME` | tmuxセッション名 | YAML設定値 |
| `ORCHESTRATOR_CONFIG_PATH` | 設定ファイルパス | `config/cc-cluster.yaml` |
| `ORCHESTRATOR_LOG_LEVEL` | ログレベル | `INFO` |
| `ORCHESTRATOR_DASHBOARD_PORT` | ダッシュボードポート | `8000` |
| `ORCHESTRATOR_DASHBOARD_HOST` | ダッシュボードホスト | `127.0.0.1` |

---

### 2. シークレット管理

**提案**: `.env` ファイルでシークレットを管理

```bash
# .env（バージョン管理に含めない）
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx
SLACK_WEBHOOK_URL=https://hooks.slack.com/xxxxx
```

**実装例**:

```python
# python-dotenv を使用
from dotenv import load_dotenv

load_dotenv()  # .envファイルから環境変数を読み込み

api_key = os.getenv("ANTHROPIC_API_KEY")
```

**`.gitignore` に追加**:

```
.env
.env.local
.env.production
```

---

### 3. 環境別設定

**提案**: 環境ごとの設定ファイルを用意

```
config/
├── cc-cluster.yaml           # デフォルト（開発環境）
├── cc-cluster.dev.yaml       # 開発環境
├── cc-cluster.staging.yaml   # ステージング環境
└── cc-cluster.prod.yaml      # 本番環境
```

**使用方法**:

```bash
# 環境変数で設定ファイルを指定
export ORCHESTRATOR_ENV=production
python -m orchestrator.cli start --config config/cc-cluster.${ORCHESTRATOR_ENV}.yaml
```

---

### 4. 設定バリデーション

**提案**: 設定ファイルのバリデーションを強化

```python
# orchestrator/core/config_validator.py
from pydantic import BaseModel, Field, validator

class ClusterConfig(BaseModel):
    name: str = Field(..., min_length=1)
    session_name: str = Field(..., min_length=1)
    work_dir: str = Field(..., min_length=1)

    @validator("work_dir")
    def validate_work_dir(cls, v):
        path = Path(v)
        if not path.is_absolute():
            raise ValueError("work_dir must be an absolute path")
        return v

class AgentConfig(BaseModel):
    name: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    personality_prompt_path: str = Field(..., min_length=1)
    marker: str = Field(..., min_length=1)
    pane_index: int = Field(..., ge=0, le=4)
```

---

## 設定変更の手順

### 1. 設定ファイルの編集

```bash
# 設定ファイルをバックアップ
cp config/cc-cluster.yaml config/cc-cluster.yaml.backup

# 設定ファイルを編集
vi config/cc-cluster.yaml
```

### 2. 設定の反映

```bash
# クラスタが起動中の場合は再起動が必要
python -m orchestrator.cli restart

# または、シャットダウンしてから再起動
python -m orchestrator.cli shutdown
python -m orchestrator.cli start
```

### 3. 設定の検証

```bash
# ステータス確認
python -m orchestrator.cli status

# ダッシュボードで確認
open http://localhost:8000
```

---

## 性格プロンプトの管理

### プロンプトファイルの場所

```
config/
└── personalities/
    ├── grand_boss.txt
    ├── middle_manager.txt
    ├── coding_writing_specialist.txt
    ├── research_analysis_specialist.txt
    └── testing_specialist.txt
```

### プロンプトの変更

```bash
# プロンプトファイルを編集
vi config/personalities/grand_boss.txt

# クラスタを再起動して反映
python -m orchestrator.cli restart
```

---

## 設定のベストプラクティス

### 1. バージョン管理

- 設定ファイルはバージョン管理する
- シークレットは含めない
- 環境固有の設定は別ファイルにする

### 2. ドキュメント化

- 設定項目の変更をドキュメントに反映
- 設定変更の理由をコメントに記載

### 3. バリデーション

- 設定変更後は必ずバリデーションを実行
- テスト環境で確認してから本番環境に適用

### 4. バックアップ

- 設定変更前は必ずバックアップを作成
- 過去の設定を保持しておく

---

## 関連ドキュメント

- [deployment.md](deployment.md) - デプロイ手順
- [security.md](security.md) - セキュリティ設定
- [troubleshooting.md](troubleshooting.md) - トラブルシューティング
