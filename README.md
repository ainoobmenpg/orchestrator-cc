# orchestrator-cc

## 概要

複数のClaude Codeインスタンスを実際に走らせて、それらに生のやり取りをさせるシステム。

## 目的

現在の `orchestrator` プロジェクトは、Pythonオブジェクトとして実装されたエージェントがLLMを呼び出すアーキテクチャです。これは「マルチLLM調整システム」としては機能しますが、本来の目的とは異なります。

**orchestrator-cc** は、本来の目的である以下を実現します：

```
Claude Code A (プロセス1)
  ↓ Claude Code Bの「入力欄」に文字を入れて送信
Claude Code B (プロセス2)
  ↓ 処理してAに結果を返す + 上司のClaude Codeに通知
Claude Code C (上司、プロセス3)
  ↓ 連絡用ファイルを作って作業完了通知
```

## 主な特徴

- **プロセスベースのアーキテクチャ**: 各Claude Codeインスタンスは独立したプロセス
- **MCPプロトコル**: Claude Code Model Context Protocolを使用した通信
- **設定ファイル分離**: 各エージェントが独立した設定・性格を持てる
- **思考ログの詳細出力**: 各インスタンスが思考過程をログに出力
- **LLM分散**: 各インスタンスが独立してLLMを呼び出し（レートリミット回避）

## 現在の状態

**Phase 0**: ✅ 検証完了（2026-02-01）

| 検証項目 | 結果 |
|---------|------|
| V-001: `claude mcp serve` の基本動作 | ✅ 成功 |
| V-002: システムプロンプト設定 | ⚠️ 代替案採用（設定ファイル分離アプローチ） |
| V-003: Pythonからのプログラム制御 | ✅ 成功 |

**次のフェーズ**: Phase 1 - 基礎プロセス起動・管理機能の実装

### Phase 1 で作成するファイル

| ファイル | 役割 |
|---------|------|
| `orchestrator/core/cc_process_models.py` | エージェントの設定情報（名前、役割、ポート番号など）のデータモデル |
| `orchestrator/core/cc_process_launcher.py` | Claude Codeを起動・停止するプロセス管理クラス |
| `config/personalities/*.txt` | 各エージェントの性格プロンプトテキスト |
| `config/cc-cluster.yaml` | クラスタ全体の設定ファイル |

### 採用アプローチ: 設定ファイル分離（ホームディレクトリ分離方式）

各エージェント専用のHOMEディレクトリを作成し、その中に `.claude/settings.json` を配置して性格設定を管理します。

```
/tmp/orchestrator-cc/
├── agents/
│   ├── grand_boss/
│   │   └── .claude/
│   │       └── settings.json  ← Grand Bossの性格設定
│   ├── middle_manager/
│   │   └── .claude/
│   │       └── settings.json  ← Middle Managerの性格設定
│   └── coding_specialist/
│       └── .claude/
│           └── settings.json  ← Coding Specialistの性格設定
```

起動方法: `HOME=/tmp/orchestrator-cc/agents/grand_boss claude mcp serve`

## 開発

詳細な開発ガイドラインは [CLAUDE.md](CLAUDE.md) を参照してください。
