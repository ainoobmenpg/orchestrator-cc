# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 🔴 最優先ルール（必ず従ってください）

このプロジェクトで作業する際は、以下のルールを**最優先**で守ってください。

詳細は [docs/workflows/development-process.md](docs/workflows/development-process.md) を参照してください。

### ルール0: 常にAgent Teamsを使用する

**このプロジェクトでは、すべての作業においてAgent Teams機能を使用してください。**

ユーザーからタスクを受け取った場合、**必ず最初にTeamCreateを使用してチームを作成し、タスクを割り振ってください。**

**例外なく、すべての作業で適用してください：**
- コードの読み取り・分析
- コードの記述・修正
- ファイルの検索
- テストの実行
- ドキュメントの作成
- 問題の調査・デバッグ

**チーム作成の基本パターン:**

1. **シンプルなタスク（1〜2ステップ）:**
   - Team Leader（自分） + 1つのスペシャリスト

2. **標準的なタスク（3〜5ステップ）:**
   - Team Leader（自分）
   - Coding Specialist（実装）
   - Testing Specialist（検証）

3. **複雑なタスク（6ステップ以上）:**
   - Team Leader（自分）
   - Research Specialist（調査）
   - Coding Specialist（実装）
   - Testing Specialist（検証）

**重要:** Agent Teamsを使用することで、タスクの並列実行、専門的な処理の委譲、効率的な進捗管理が可能になります。

### ルール1: 作業開始前に必ずブランチを作成

**絶対に main ブランチで作業しないでください。必ず作業ブランチを作成してから作業を開始してください。**

```bash
git checkout -b feature/<task-name>
```

### ルール1: 開発完了の定義

**「開発完了」はPRを作成した時点です。プッシュのみで完了報告しないでください。**

### ルール2: レビュー対応時のフロー

レビュー対応時は、必ず `PullRequests/pr-XXXX-review.md` を先頭から最後まで読んでください。

---

## 🔵 コミュニケーションルール

### システムプロンプト検証時のルール

ペルソナやシステムプロンプトの検証を求められた場合：

- **指定されたマーカーのみを返す**（例: `TESTING OK`、`CODING OK`）
- 説明、分析、その他のテキストを一切含めない
- マーカーのみの1行で返す
- 理由：ユーザーは簡潔な確認を求めており、冗長な説明は不要

### Agent Teamsの運用ルール

Agent Teamsを使用する場合：

- **SendMessageでエージェント間通信を行う** - メッセージには明確な目的と recipient を指定
- **TaskUpdateでタスク状態を常に最新に保つ** - 進捗、完了、失敗を適時更新
- **思考ログを活用する** - 複雑な判断プロセスをログに残す

### エージェント間通信のベストプラクティス

| 原則 | 説明 |
|------|------|
| **明確なrecipient** | SendMessageでは必ず相手を指定する |
| **簡潔なメッセージ** | 要点を絞った通信を心がける |
| **ステータス更新** | タスクの開始、進捗、完了をTaskUpdateで通知 |
| **エラーハンドリング** | 問題が発生したら速やかに報告 |

### 問題解決時のアプローチ

問題が発生した場合：

1. **現象を正確に把握する** - 何が起きているのかをログから確認
2. **根本原因を特定する** - 表面的な症状ではなく、根本原因を探る
3. **最小限の変更で解決を試みる** - 大幅な変更の前に簡単な解決策を検討
4. **チームメンバーに相談する** - 困ったときはSendMessageで助けを求める

---

## プロジェクト概要

orchestrator-cc は、**Claude CodeのAgent Teams機能を使用したマルチエージェント協調システム**です。

## 目的

**orchestrator-cc** は、Claude CodeのTeamCreate、SendMessage、TaskUpdateツールを使用して、複数のAIエージェントが協調してタスクを完遂するシステムを実現します。

```
Claude Code A (Team Lead)
  ↓ SendMessageで通信
Claude Code B (Specialist)
  ↓ 処理してSendMessageで結果を返す
Claude Code C (Team Lead)
  ↓ TaskUpdateでタスク状態を更新
```

## 主な特徴

- **Agent Teams アーキテクチャ**: Claude CodeのTeamCreate機能を使用したネイティブなマルチエージェントシステム
- **SendMessage ツール**: エージェント間の直接通信
- **TaskUpdate ツール**: タスク状態の共有と管理
- **Webダッシュボード**: FastAPIベースのリアルタイム監視ダッシュボード
- **ヘルスモニタリング**: エージェントの健全性を監視・通知
- **思考ログ**: エージェントの思考プロセスを可視化
- **ファイルベース監視**: `~/.claude/teams/` のファイル監視による状態追跡

## 現在の状態

**Agent Teams移行**: ✅ 完了（コミット `76a5341`）

tmux方式からAgent Teamsへ完全移行しました（13,562行削除）。

**Reactダッシュボード**: ✅ 完了（2026-02-07）

React + TypeScript + Vite によるモダンなダッシュボードを実装しました。

| 機能 | 状態 |
|------|------|
| Agent Teams管理 | ✅ 実装完了 |
| Webダッシュボード（React） | ✅ 実装完了 |
| ヘルスモニタリング | ✅ 実装完了 |
| 思考ログ | ✅ 実装完了 |
| CLIツール | ✅ 実装完了 |

### Webダッシュボード（React）の機能

- ✅ リアルタイム監視（WebSocket）
- ✅ チーム管理・選択
- ✅ タスクボード（ドラッグ&ドロップ）
- ✅ メッセージログ
- ✅ 思考ログ
- ✅ タイムライン
- ✅ システムログ
- ✅ Framer Motion アニメーション
- ✅ 通知システム
- ✅ アクセシビリティ対応（ARIA、キーボードナビゲーション）
- ✅ エラーハンドリング（ErrorBoundary）
- ✅ モバイル対応（レスポンシブデザイン）
- ✅ オンボーディング（チュートリアル）
- ✅ テスト（39テスト、Vitest）

### アーキテクチャ変更履歴

- **2026-02-01**: 設定ファイル分離アプローチから **tmux方式** へ切り替え
- **2026-02-02**: Phase 2完了 - **YAML通信方式**の実装
- **2026-02-07**: **Agent Teamsへ完全移行** - tmux方式、YAML通信方式を廃止
- **2026-02-07**: **Reactダッシュボード完了** - Phase 1-4 完了（フルスクラッチ実装）

---

## 初学者さんへ（用語解説）

このプロジェクトでは色々な専門用語が出てきます。わからない用語があったらここを参照してください！

### 用語集

| 用語 | 読み方 | 意味 |
|------|--------|------|
| **Agent Teams** | えーじェんとちーむず | Claude Codeの機能で、複数のAIエージェントをチームとして協調動作させる仕組み |
| **TeamCreate** | ちーむくりえーと | Claude Codeのツールで、新しいチームを作成する機能 |
| **SendMessage** | せんどめっせーじ | Claude Codeのツールで、チームメンバー間でメッセージを送信する機能 |
| **TaskUpdate** | たすくあっぷでーと | Claude Codeのツールで、タスクの状態を更新する機能 |
| **環境変数** | かんきょうへんすう | プログラムが起動するときに参照できる設定値のこと。`HOME=xxx` のように指定します。 |
| **設定ファイル** | せっていふぁいる | プログラムの動作設定を書いたテキストファイルのこと。 |
| **ブランチ** | ぶらんち | Gitで作業する際の「分岐点」。機能ごとにブランチを作って作業することで、元のコードを安全に保てます。 |
| **コミット** | こみっと | 変更内容をGitに記録すること。「変更を保存」のようなイメージです。 |
| **PR（Pull Request）** | ぴーりくえす | 変更内容を他の人にレビューしてもらうための依頼。GitHub上で行います。 |
| **リント** | りんと | コードの書き方チェック。「ここスペース空いてないよ」などのミスを見つけてくれます。 |
| **フォーマット** | ふぉーまっと | コードの見た目を整形すること。インデントやスペースを統一して、読みやすくします。 |
| **テストカバレッジ** | てすとかばれっじ | テストがどれくらい網羅されているかの割合。80%以上を目標にしています。 |
| **静的型チェック** | せいてきかたチェック | プログラムを実行せずに、型の間違い（例: 文字列なのに数値として扱っている）を見つけるチェック。 |

### ファイル構造のイメージ

このプロジェクトの重要なファイル・ディレクトリはこんな感じです：

```
orchestrator-cc/
├── CLAUDE.md              ← 今読んでいるファイル（Claudeへの説明書）
├── README.md              ← プロジェクトの概要説明
├── docs/                  ← 詳細ドキュメント
│   ├── architecture.md    ← 技術的な設計図
│   ├── workflows/         ← ワークフロー関連ドキュメント
│   │   ├── review-process.md
│   │   ├── development-process.md
│   │   └── post-merge-workflow.md
│   ├── quality/           ← 品質管理関連ドキュメント
│   │   └── quality-management.md
│   ├── documentation/     ← ドキュメント管理関連
│   │   └── documentation-update-process.md
│   └── archive/           ← アーカイブ（古いドキュメント）
├── orchestrator/          ← メインのコード
│   ├── core/              ← 基本的な処理
│   │   ├── agent_teams_manager.py  # Agent Teams管理
│   │   └── agent_health_monitor.py # ヘルスモニタリング
│   ├── web/               ← Webダッシュボード
│   │   ├── frontend/      ← Reactフロントエンド（新規）
│   │   │   ├── src/
│   │   │   │   ├── components/  # UIコンポーネント
│   │   │   │   ├── pages/       # ページ
│   │   │   │   ├── hooks/       # カスタムフック
│   │   │   │   ├── stores/      # Zustandストア
│   │   │   │   ├── services/    # API・WebSocket
│   │   │   │   └── lib/         # ユーティリティ
│   │   │   ├── tests/           # Vitestテスト
│   │   │   └── package.json
│   │   ├── dashboard.py   # FastAPIアプリケーション
│   │   ├── teams_monitor.py
│   │   ├── thinking_log_handler.py
│   │   └── team_models.py
│   └── cli/               ← CLIツール
│       └── main.py
└── tests/                 ← テストコード
```

### 開発の進め方（ステップバイステップ）

**バックエンド（Python）の場合:**

1. **作業ブランチを作る**
   ```bash
   git checkout -b feature/phase1-process-launcher
   ```
   （これで `main` から分岐した作業スペースができます）

2. **コードを書く**
   - Agent Teams関連の機能を追加・修正します

3. **テストを実行する**
   ```bash
   pytest tests/ -v
   ```

4. **リントチェック**
   ```bash
   ruff check .
   ```

5. **変更をコミットする**
   ```bash
   git add .
   git commit -m "feat: チーム管理機能の実装"
   ```

6. **GitHubにプッシュしてPRを作る**
   ```bash
   git push -u origin feature/phase1-process-launcher
   ```
   （その後、GitHub上でPull Requestを作成します）

**フロントエンド（React）の場合:**

1. **作業ブランチを作る**
   ```bash
   git checkout -b feature/react-dashboard-component
   ```

2. **フロントエンドディレクトリへ移動**
   ```bash
   cd orchestrator/web/frontend
   ```

3. **開発サーバー起動**
   ```bash
   npm run dev
   ```

4. **テストを実行する**
   ```bash
   npm run test
   ```

5. **型チェック**
   ```bash
   npm run type-check
   ```

6. **リントチェック**
   ```bash
   npm run lint
   ```

7. **変更をコミットする**
   ```bash
   git add .
   git commit -m "feat: ダッシュボードコンポーネント追加"
   ```

8. **GitHubにプッシュしてPRを作る**
   ```bash
   git push -u origin feature/react-dashboard-component
   ```

---

## 開发に関する詳細ドキュメント

開発ワークフロー、品質管理、レビュー運用などの詳細は以下のドキュメントを参照してください。

### ワークフロー

- [docs/workflows/development-process.md](docs/workflows/development-process.md) - 開発ワークフロー（ブランチ作成〜PRマージまでの手順）
- [docs/workflows/post-merge-workflow.md](docs/workflows/post-merge-workflow.md) - マージ後のワークフロー（ブランチ整理、Issueクローズ）
- [docs/workflows/review-process.md](docs/workflows/review-process.md) - レビュー運用フロー（ハイブリッド方式、チェックリスト）

### 品質管理

- [docs/quality/quality-management.md](docs/quality/quality-management.md) - コード品質管理（mypy、ruff、pytest、カバレッジ）

### ドキュメント管理

- [docs/documentation/documentation-update-process.md](docs/documentation/documentation-update-process.md) - ドキュメント更新フロー（更新が必要なケース、手順）
