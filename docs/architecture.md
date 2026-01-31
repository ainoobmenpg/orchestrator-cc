# アーキテクチャ詳細

## システム全体図

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    orchestrator-cc システム全体                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                  orchestrator-cc（親プロセス）                        │   │
│  │                                                                   │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │   │
│  │  │ Claude Code A   │  │ Claude Code B   │  │ Claude Code C   │     │   │
│  │  │  Grand Boss     │  │ Middle Manager  │  │ Specialist      │     │   │
│  │  │                 │  │                 │  │                 │     │   │
│  │  │ stdin  ←────────┼→│ stdout  stdin  ←─┼──→│ stdout  stdin   │     │   │
│  │  │   (JSON-RPC)    │  │   (JSON-RPC)    │  │   (JSON-RPC)    │     │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘     │   │
│  │         ↑                      ↑                     ▲              │   │
│  │         └──────────────────────┴─────────────────────┘              │   │
│  │                            │                                    │   │
│  │  ┌──────────────────────────────────────────────────────────────┐ │   │
│  │  │              orchestrator-cc コア                           │ │   │
│  │  │          - プロセス起動・管理                                │ │   │
│  │  │          - メッセージ中継                                    │ │   │
│  │  │          - 思考ログ表示                                      │ │   │
│  │  │          - 通信プロトコル管理                                │ │   │
│  │  └──────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       ユーザーインターフェース                        │   │
│  │                                                                   │   │
│  │  Phase 1-3: ターミナル出力                                         │   │
│  │  Phase 4:   Webダッシュボード                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## コンポーネント詳細

### 1. orchestrator-cc コア（親プロセス）

#### 役割
- 複数のClaude Codeプロセスの起動・管理
- プロセス間のメッセージ中継
- 思考ログの表示・管理
- ユーザー入力の処理

#### 構成要素

| コンポーネント | 説明 | 再利用元 |
|--------------|------|---------|
| **CCProcessLauncher** | Claude Codeプロセスの起動・管理 | `orchestrator/core/process_launcher.py` |
| **ClusterManager** | 複数プロセスの一元管理 | `orchestrator/core/cluster_manager.py` |
| **MCPMessageBridge** | Message↔MCP変換ブリッジ | 新規実装 |
| **CCAgentRegistry** | エージェント登録・発見 | 新規実装 |
| **ThinkingLogFormatter** | 思考ログのフォーマット・表示 | 新規実装 |

### 2. Claude Code インスタンス

#### プロセス起動コマンド

```bash
claude mcp serve --system-prompt <性格プロンプト>
```

#### 通信方式

- **トランスポート**: stdio（標準入出力）
- **プロトコル**: JSON-RPC 2.0
- **形式**: MCP（Model Context Protocol）

#### プロセス構成

| インスタンス | 役割 | 責任 |
|------------|------|------|
| **Grand Boss** | 上司 | - ユーザーからのタスク受信<br>- Middle Managerへのタスク委譲<br>- 最終結果の集約・報告 |
| **Middle Manager** | 中間管理職 | - タスクの分解<br>- Specialistsへの割り当て<br>- 結果の集約 |
| **Coding Specialist** | プログラミング専門家 | - コーディングタスクの実行<br>- コードレビュー<br>- リファクタリング |
| **Research Specialist** | 調査専門家 | - 情報収集<br>- ドキュメント作成<br>- 技術調査 |
| **Writing Specialist** | ライティング専門家 | - ドキュメント作成・編集<br>- テキストの校正 |
| **Analysis Specialist** | 分析専門家 | - データ分析<br>- 統計処理<br>- 要因分析 |
| **Testing Specialist** | テスト専門家 | - テスト設計<br>- テスト実行<br>- バグ検出 |

### 3. 通信フロー

#### メッセージの流れ

```
ユーザー
  │ タスク入力
  ▼
Grand Boss
  │ 思考ログ出力
  │ タスク分解を依頼
  ▼
Middle Manager
  │ 思考ログ出力
  │ タスクを分解
  │ 専門家に割り当て
  ▼
Specialist
  │ 思考ログ出力
  │ タスク実行
  ▼
Middle Manager
  │ 結果を集約
  ▼
Grand Boss
  │ 最終結果をユーザーに報告
  ▼
ユーザー
```

#### メッセージ構造

```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "method": "tools/call",
  "params": {
    "name": "send_message",
    "arguments": {
      "from": "grand_boss",
      "to": "middle_manager",
      "type": "task_request",
      "content": "タスクの分解をお願い",
      "thinking": "これは複雑なタスクだな。Middle Managerに分解してもらおう。まずは全体の要件を整理して依頼する必要がある。",
      "metadata": {
        "timestamp": "2026-02-01T14:32:10Z",
        "priority": "normal",
        "task_id": "task-123"
      }
    }
  }
}
```

### 4. 思考ログの出力

#### ターミナル出力形式

```
[14:32:10] > ユーザーからタスク受信: Webアプリを作って
[14:32:10] [思考] これは複雑なタスクだな。Middle Managerに分解してもらおう。
[14:32:10]         まずは全体の要件を整理して依頼する必要がある。
[14:32:10]         - フロントエンドが必要
[14:32:10]         - バックエンドが必要
[14:32:10]         - データベース設計が必要
[14:32:11] > Middle Managerへ送信: タスクの分解をお願い
```

#### 思考ログの詳細レベル

| レベル | 説明 | 出力内容 |
|-------|------|----------|
| **simple** | シンプル | 結果のみ |
| **detailed** | 詳細（デフォルト） | 思考の過程、理由付け |
| **verbose** | 非常に詳細 | 全ての思考過程、複数の選択肢の検討 |

### 5. 性格づけ（システムプロンプト）

#### プロンプトファイル構造

```
config/personalities/
├── grand_boss.txt
├── middle_manager.txt
├── coding_specialist.txt
├── research_specialist.txt
├── writing_specialist.txt
├── analysis_specialist.txt
└── testing_specialist.txt
```

#### プロンプトの要素

```
【役割】
- インスタンスの役割定義
- 責任範囲
- 期待される行動

【性格・話し方】
- 口調の特徴
- コミュニケーションスタイル
- 価値観

【思考ログ】
- 思考の出力レベル
- 思考の形式
- 情報の詳細度
```

## データフロー

### 1. プロセス起動フロー

```
orchestrator-cc 起動
  │
  ▼
config/cc-cluster.yaml を読み込み
  │
  ▼
各プロセスの設定を読み込み
  │
  ├─→ Grand Boss:   personality_prompt_path を読み込み
  ├─→ Middle Manager: personality_prompt_path を読み込み
  └─→ Specialists:   personality_prompt_path を読み込み
  │
  ▼
各プロセスを起動
  │
  ├─→ claude mcp serve --system-prompt $(cat config/personalities/grand_boss.txt)
  ├─→ claude mcp serve --system-prompt $(cat config/personalities/middle_manager.txt)
  └─→ ...
  │
  ▼
stdioパイプを確立
  │
  ▼
起動完了
```

### 2. メッセージ通信フロー

```
Grand Boss がメッセージ送信
  │
  ▼
JSON-RPC リクエストを作成
  │
  ├─→ method: "tools/call"
  ├─→ params.name: "send_message"
  └─→ params.arguments: {from, to, content, thinking, ...}
  │
  ▼
Grand Boss の stdout から読み取り
  │
  ▼
orchestrator-cc コアが受信
  │
  ▼
メッセージを解析・ルーティング
  │
  ▼
Middle Manager の stdin に書き込み
  │
  ▼
Middle Manager が受信・処理
  │
  ▼
Middle Manager がレスポンスを作成
  │
  ▼
Middle Manager の stdout から読み取り
  │
  ▼
orchestrator-cc コアが受信
  │
  ▼
Grand Boss の stdin に書き込み（必要な場合）
  │
  ▼
完了
```

## ディレクトリ構成（実装後）

```
orchestrator-cc/
├── docs/                          # ドキュメント
│   ├── overview.md
│   ├── architecture.md            # 本文档
│   ├── requirements.md
│   ├── technical-decisions.md
│   ├── roadmap.md
│   ├── specs/
│   │   ├── thinking-log.md
│   │   ├── personality.md
│   │   ├── communication.md
│   │   └── api.md
│   ├── validation.md
│   ├── risks.md
│   └── references.md
│
├── config/                        # 設定ファイル
│   ├── cc-cluster.yaml           # クラスタ設定
│   └── personalities/            # 性格プロンプト
│       ├── grand_boss.txt
│       ├── middle_manager.txt
│       ├── coding_specialist.txt
│       ├── research_specialist.txt
│       ├── writing_specialist.txt
│       ├── analysis_specialist.txt
│       └── testing_specialist.txt
│
├── orchestrator/                  # 実装コード
│   ├── __init__.py
│   ├── cli/                      # CLI
│   │   ├── __init__.py
│   │   └── cc_cluster.py         # クラスタ管理CLI
│   ├── core/                     # コア機能
│   │   ├── __init__.py
│   │   ├── cc_process_models.py  # プロセスモデル
│   │   ├── cc_process_launcher.py # プロセス起動
│   │   ├── mcp_message_bridge.py # MCPメッセージブリッジ
│   │   └── cc_agent_registry.py  # エージェント登録
│   ├── agents/                   # エージェント実装
│   │   ├── __init__.py
│   │   ├── cc_grand_boss.py
│   │   ├── cc_middle_manager.py
│   │   └── cc_specialists.py
│   └── web/                      # Webダッシュボード（Phase 4）
│       ├── dashboard.py
│       ├── static/
│       └── templates/
│
├── tests/                        # テスト
│   ├── test_core/
│   │   ├── test_cc_process_models.py
│   │   ├── test_cc_process_launcher.py
│   │   └── test_mcp_message_bridge.py
│   └── test_integration/
│       └── test_cc_multi_process.py
│
├── scripts/                      # スクリプト
│   ├── check-quality.sh
│   └── start-cluster.sh
│
├── README.md
├── CLAUDE.md
└── LICENSE
```

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| **言語** | Python 3.12+ |
| **プロセス管理** | asyncio.subprocess |
| **通信プロトコル** | MCP (JSON-RPC 2.0) |
| **トランスポート** | stdio (標準入出力) |
| **データモデル** | Pydantic |
| **CLI** | Typer |
| **Web（将来）** | FastAPI + WebSocket |
| **テスト** | pytest, pytest-asyncio |

## 非機能要件

| 項目 | 要件 |
|------|------|
| **可用性** | 各プロセスがクラッシュしても自動再起動 |
| **拡張性** | 新しいSpecialistを容易に追加可能 |
| **可観測性** | 全ての通信・思考ログをリアルタイムで観察可能 |
| **スケーラビリティ** | 複数マシンでの展開に対応（将来） |
| **保守性** | 既存のorchestratorコードを最大限再利用 |
