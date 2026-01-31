# 参考文献・リソース

## 公式ドキュメント

### Claude Code

| リソース | URL | 説明 |
|---------|-----|------|
| **Claude Code ドキュメント** | https://code.claude.com/docs | Claude Codeの公式ドキュメント |
| **Claude Code MCPガイド** | https://code.claude.com/docs/en/mcp | MCP接続方法の公式ガイド |
| **Claude Code CLI リファレンス** | `claude --help` | CLIコマンドのヘルプ |
| **MCP サーバーコマンド** | `claude mcp serve --help` | MCPサーバーのヘルプ |

### MCP（Model Context Protocol）

| リソース | URL | 説明 |
|---------|-----|------|
| **MCP公式仕様** | https://modelcontextprotocol.io/specification/2025-06-18 | MCPプロトコルの公式仕様書 |
| **MCPアーキテクチャ** | https://modelcontextprotocol.info/docs/concepts/architecture/ | MCPの設計哲学とアーキテクチャ |
| **JSON-RPC 2.0 仕様** | https://www.jsonrpc.org/specification | JSON-RPC 2.0の公式仕様 |

## GitHub リポジトリ

### orchestrator（既存プロジェクト）

| リソース | URL | 説明 |
|---------|-----|------|
| **orchestrator リポジトリ** | https://github.com/mo9mo9-uwu-mo9mo9/orchestrator | 既存のorchestratorプロジェクト |
| **process_launcher.py** | `orchestrator/core/process_launcher.py` | プロセス起動・管理の実装 |
| **cluster_manager.py** | `orchestrator/core/cluster_manager.py` | クラスタ管理の実装 |
| **mcp_client.py** | `orchestrator/llm/providers/mcp_client.py` | MCPクライアントの実装 |

### orchestrator-cc（本プロジェクト）

| リソース | URL | 説明 |
|---------|-----|------|
| **orchestrator-cc リポジトリ** | https://github.com/mo9mo9-uwu-mo9mo9/orchestrator-cc | 本プロジェクトのリポジトリ |
| **Issue トラッカー** | https://github.com/mo9mo9-uwu-mo9mo9/orchestrator-cc/issues | バグ報告・機能要求 |

## 技術記事・ブログ

### MCP関連

| タイトル | URL | 日付 |
|--------|-----|------|
| **How to Add MCP to Claude Code** | https://medium.com/@Michael38/how-to-add-mcp-to-claude-code-step-by-step-plain-english-865fec18e07d | 2025-12-29 |
| **Claude Code MCP Servers: Complete Configuration Guide** | https://www.braingrid.ai/blog/claude-code-mcp | 2025-12-24 |
| **Ultimate Guide to Claude MCP Servers & Setup** | https://generect.com/blog/claude-mcp/ | 2025-05-05 |
| **Connect Claude to an MCP Server** | https://liblab.com/docs/mcp/howto-connect-mcp-to-claude | - |

### マルチエージェントシステム

| タイトル | URL | 日付 |
|--------|-----|------|
| **Claude Code Swarm Orchestration** | https://gist.github.com/kieranklaassen/4f2aba89594a4aea4ad64d753984b2ea | - |
| **AIエージェント会議室** | （非公開） | - |

## Pythonライブラリ

### コアライブラリ

| ライブラリ | バージョン | 用途 |
|----------|----------|------|
| **asyncio** | 標準ライブラリ | 非同期処理 |
| **subprocess** | 標準ライブラリ | プロセス管理 |
| **dataclasses** | 標準ライブラリ | データモデル |
| **enum** | 標準ライブラリ | 列挙型 |

### 外部ライブラリ

| ライブラリ | バージョン | 用途 |
|----------|----------|------|
| **pydantic** | 2.0+ | データバリデーション |
| **typer** | 0.9+ | CLIフレームワーク |
| **pyyaml** | 6.0+ | YAML設定ファイル |
| **fastapi** | 0.100+ | Web API（Phase 4） |
| **websockets** | 11.0+ | WebSocket（Phase 4） |
| **pytest** | 7.0+ | テストフレームワーク |
| **pytest-asyncio** | 0.21+ | 非同期テスト |

## 開発ツール

### 品質管理

| ツール | 用途 |
|------|------|
| **mypy** | 静的型チェック |
| **ruff** | リント・フォーマット |
| **pytest** | テスト実行 |
| **pytest-cov** | カバレッジ計測 |

### 開発環境

| ツール | 用途 |
|------|------|
| **Git** | バージョン管理 |
| **GitHub** | ホスティング |
| **pre-commit** | Gitフック |
| **python-dotenv** | 環境変数管理 |

## 設定ファイル

### Python

| ファイル | 用途 |
|------|------|
| **pyproject.toml** | プロジェクト設定 |
| **.python-version** | Pythonバージョン指定 |
| **.mypy.ini** | mypy設定 |
| **ruff.toml** | ruff設定 |

### Git

| ファイル | 用途 |
|------|------|
| **.gitignore** | 除外ファイル |
| **.pre-commit-config.yaml** | pre-commit設定 |

### プロジェクト

| ファイル | 用途 |
|------|------|
| **README.md** | プロジェクト概要 |
| **CLAUDE.md** | Claude Code用ガイド |
| **LICENSE** | ライセンス |

## 関連プロジェクト

### 類似プロジェクト

| プロジェクト | URL | 説明 |
|------------|-----|------|
| **LangGraph** | https://github.com/langchain-ai/langgraph | Langchainの状態機関ベースエージェント |
| **AutoGen** | https://github.com/microsoft/autogen | マルチエージェント会話フレームワーク |
| **CrewAI** | https://github.com/joaomdmoura/crewAI | エージェントチームのオーケストレーション |
| **OpenDevin** | https://github.com/OpenDevin/OpenDevin | ソフトウェア開発エージェント |

### 参考実装

| プロジェクト | URL | 説明 |
|------------|-----|------|
| **MCP Servers** | https://github.com/modelcontextprotocol | MCPサーバーの実装例 |
| **FastAPI Realtime** | https://github.com/fastapi/fastapi | Realtime通信の実装例 |

## 学習リソース

### 書籍

| タイトル | 著者 | ISBN |
|--------|------|------|
| **Python Concurrency with asyncio** | Matthew Fowler | 978-1492075435 |
| **Growing Object-Oriented Software, Guided by Tests** | Steve Freeman | 978-0201616224 |
| **Designing Data-Intensive Applications** | Martin Kleppmann | 978-1449373320 |

### オンラインコース

| コース | プラットフォーム | URL |
|-------|--------------|-----|
| **AsyncIO** | Real Python | https://realpython.com/async-python/ |
| **FastAPI** | FastAPI公式 | https://fastapi.tiangolo.com/tutorial/ |
| **MCP開発** | Model Context Protocol | https://modelcontextprotocol.io/docs/concepts/development/ |

## コミュニティ

### フォーラム・Discord

| コミュニティ | URL |
|----------|-----|
| **Anthropic Discord** | https://discord.gg/anthropic |
| **Claude Code Discussions** | https://github.com/anthropics/claude-code/discussions |

### スタックオーバーフロー

| タグ | URL |
|-----|-----|
| **claude-code** | https://stackoverflow.com/questions/tagged/claude-code |
| **model-context-protocol** | https://stackoverflow.com/questions/tagged/model-context-protocol |

## 用語集

| 用語 | 説明 |
|------|------|
| **MCP** | Model Context Protocol。AIモデルとツール間の通信プロトコル |
| **JSON-RPC 2.0** | リモートプロシージャコールのためのJSONベースのプロトコル |
| **stdio** | 標準入出力。プロセス間通信の一形態 |
| **Grand Boss** | 最上位のエージェント。ユーザーとのインターフェースを担当 |
| **Middle Manager** | 中間管理職。タスク分解と割り当てを担当 |
| **Specialist** | 専門家。特定のタスクを実行 |
| **思考ログ** | エージェントの思考過程を出力したログ |
| **システムプロンプト** | AIエージェントの基本的な振る舞いを定義するプロンプト |

## 更新履歴

| 日付 | バージョン | 変更内容 |
|------|----------|----------|
| 2026-02-01 | 0.1.0 | 初版作成 |

---

## フィードバック

本ドキュメントへのフィードバッグをお待ちしています。

- **バグ報告**: https://github.com/mo9mo9-uwu-mo9mo9/orchestrator-cc/issues
- **改善提案**: https://github.com/mo9mo9-uwu-mo9mo9/orchestrator-cc/pulls
- **質問**: GitHub Discussionsで質問してください
