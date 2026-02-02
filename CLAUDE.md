# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 🔴 最優先ルール（必ず従ってください）

このプロジェクトで作業する際は、以下のルールを**最優先**で守ってください。

詳細は [docs/workflows/development-process.md](docs/workflows/development-process.md) を参照してください。

### ルール0: 作業開始前に必ずブランチを作成

**絶対に main ブランチで作業しないでください。必ず作業ブランチを作成してから作業を開始してください。**

```bash
git checkout -b feature/<task-name>
```

### ルール1: 開発完了の定義

**「開発完了」はPRを作成した時点です。プッシュのみで完了報告しないでください。**

### ルール2: レビュー対応時のフロー

レビュー対応時は、必ず `PullRequests/pr-XXXX-review.md` を先頭から最後まで読んでください。

---

## プロジェクト概要

orchestrator-cc は、**複数の Claude Code インスタンスを実際に走らせて、それらに生のやり取りをさせるシステム**です。

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
- **tmux方式**: tmuxセッション内の各ペインでClaude Codeを起動・管理
- **プログラム制御**: `tmux send-keys`でコマンド送信、`tmux capture-pane`で出力取得
- **性格設定**: `--system-prompt`で各エージェントに異なる役割・性格を設定
- **LLM分散**: 各インスタンスが独立してLLMを呼び出し（レートリミット回避）

## 現在の状態

### Phase 0: 事前検証 ✅ 完了（2026-02-01）

**Phase 0**では「Claude Codeをプログラムから制御できるか？」を検証しました。

#### 検証結果

| 項目 | 結果 | 説明 |
|------|------|------|
| V-001 | ✅ 成功 | Claude CodeがMCPサーバーとして動くことを確認 |
| V-002 | ⚠️ 代替案採用 | コマンドオプションでのプロンプト設定は不可 → **tmux方式**を採用 |
| V-003 | ✅ 成功 | Pythonからプロセス起動・通信が可能 |

### Phase 0.5: 中間検証 ✅ 完了（2026-02-01）

**Phase 0.5**では「tmux方式でClaude Codeを制御できるか？」を検証しました。

#### 検証結果

| 項目 | 結果 | 説明 |
|------|------|------|
| V-101 | ✅ 成功 | tmuxで複数のClaude Codeプロセスを別ペインで起動できる |
| V-102 | ✅ 成功 | Pythonからtmuxペインにコマンドを送信できる |
| V-103 | ✅ 成功 | tmux capture-paneで出力をキャプチャ・パースできる |

#### 採用した方式: tmux方式

tmuxセッション内の各ペインでClaude Codeを起動し、プログラムから制御します。

```
tmuxセッション (orchestrator-cc)
├── ペイン0: Grand Boss
│   └── claude --system-prompt "あなたはGrand Bossです..."
├── ペイン1: Middle Manager
│   └── claude --system-prompt "あなたはMiddle Managerです..."
└── ペイン2: Coding Specialist
    └── claude --system-prompt "あなたはCoding Specialistです..."
```

**制御方法**:
- `tmux send-keys -t session:0.0 "コマンド" Enter` → ペインにコマンド送信
- `tmux capture-pane -t session:0.0 -p` → ペインの出力を取得

この方式の良いところ：
- ✅ **性格設定**: `--system-prompt`で各エージェントに異なる役割を設定できる
- ✅ **独立性**: 各ペインが独立したClaude Codeプロセスとして動作
- ✅ **可視性**: tmux attachで各エージェントの状態を直接確認できる

---

## 初学者さんへ（用語解説）

このプロジェクトでは色々な専門用語が出てきます。わからない用語があったらここを参照してください！

### 用語集

| 用語 | 読み方 | 意味 |
|------|--------|------|
| **プロセス** | ぷろせす | コンピュータ上で動いているプログラムの「実体」。例えば、ブラウザを2つ開けると2つのプロセスが動いています。orchestrator-ccでは、各エージェントが別々のプロセスとして動きます。 |
| **tmux** | てぃーまっくす | ターミナルマルチプレクサー。1つのターミナルウィンドウで複数の端末（ペイン）を管理できるツール。 |
| **ペイン** | ぺいん | tmuxで分割された1つ1つの端末画面のこと。各ペインで独立したClaude Codeプロセスを動かします。 |
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
│   ├── overview.md        ← システム全体の説明
│   ├── architecture.md    ← 技術的な設計図
│   ├── validation.md      ← 検証結果の記録
│   ├── workflows/         ← ワークフロー関連ドキュメント
│   │   ├── review-process.md
│   │   ├── development-process.md
│   │   └── post-merge-workflow.md
│   ├── quality/           ← 品質管理関連ドキュメント
│   │   └── quality-management.md
│   └── documentation/     ← ドキュメント管理関連
│       └── documentation-update-process.md
│   └── specs/             ← 仕様書
│       ├── communication.md  ← 通信方式の決まり
│       └── personality.md    ← 性格設定の決まり
├── orchestrator/          ← メインのコード（これから作る）
│   ├── core/              ← 基本的な処理
│   └── agents/            ← 各エージェントの処理
├── config/                ← 設定ファイル（これから作る）
│   ├── personalities/     ← 性格プロンプトのテキスト
│   └── cc-cluster.yaml    ← クラスタの設定
└── tests/                 ← テストコード
```

### 開発の進め方（ステップバイステップ）

1. **作業ブランチを作る**
   ```bash
   git checkout -b feature/phase1-process-launcher
   ```
   （これで `main` から分岐した作業スペースができます）

2. **コードを書く**
   - まだプロジェクトは空っぽなので、これから `orchestrator/` 以下にコードを追加していきます

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
   git commit -m "feat: プロセス起動機能の実装"
   ```

6. **GitHubにプッシュしてPRを作る**
   ```bash
   git push -u origin feature/phase1-process-launcher
   ```
   （その後、GitHub上でPull Requestを作成します）

---

## 次のステップ: Phase 1

**Phase 1**では「tmux方式でClaude Codeのプロセスを起動・管理する機能」を実装します。

### 作成するファイル

| ファイル | 役割 | 初学者向けの説明 |
|---------|------|------------------|
| `orchestrator/core/tmux_session_manager.py` | tmuxセッション管理 | tmuxセッションの作成・ペイン分割を管理するクラス |
| `orchestrator/core/cc_process_launcher.py` | プロセス起動 | 各ペインでClaude Codeを起動・監視する仕組み |
| `orchestrator/core/pane_io.py` | ペイン入出力 | ペインへのコマンド送信・出力取得を行うクラス |
| `config/personalities/*.txt` | 性格プロンプト | 各エージェントの性格（「あなたは〇〇です...」）を書いたテキストファイル |
| `config/cc-cluster.yaml` | クラスタ設定 | エージェント構成やペイン番号などを定義するYAMLファイル |

### 開発完了チェックリスト（PR作成時）

**開発完了の定義**: PRを作成してレビュー依頼を出した時点を「開発完了」とします。
プッシュのみで完了報告をしないよう注意してください。

- [ ] テストがパスする
- [ ] リントチェックが通る
- [ ] PRを作成してレビューを受ける

---

## 開発に関する詳細ドキュメント

開発ワークフロー、品質管理、レビュー運用などの詳細は以下のドキュメントを参照してください。

### ワークフロー

- [docs/workflows/development-process.md](docs/workflows/development-process.md) - 開発ワークフロー（ブランチ作成〜PRマージまでの手順）
- [docs/workflows/post-merge-workflow.md](docs/workflows/post-merge-workflow.md) - マージ後のワークフロー（ブランチ整理、Issueクローズ）
- [docs/workflows/review-process.md](docs/workflows/review-process.md) - レビュー運用フロー（ハイブリッド方式、チェックリスト）

### 品質管理

- [docs/quality/quality-management.md](docs/quality/quality-management.md) - コード品質管理（mypy、ruff、pytest、カバレッジ）

### ドキュメント管理

- [docs/documentation/documentation-update-process.md](docs/documentation/documentation-update-process.md) - ドキュメント更新フロー（更新が必要なケース、手順）
