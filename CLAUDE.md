# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

### 終わったら

- [ ] テストがパスする
- [ ] リントチェックが通る
- [ ] PRを作成してレビューを受ける

---

### マージ後のワークフロー

## コード品質管理

### 品質チェックツール

| ツール | 役割 | 対象 |
|--------|------|------|
| **mypy** | 静的型チェック | プロジェクトルート |
| **ruff check** | リント（インポート順序・未使用変数等） | 全ファイル |
| **ruff format** | コードフォーマット | 全ファイル |
| **pytest** | テスト実行（単体テストは高速、統合テストは並列） | `tests/` |

### 品質チェックコマンド

#### 個別チェック

```bash
# 型チェック
mypy .

# リントチェック
ruff check .

# フォーマットチェック
ruff format --check .

# テスト実行（単体テストのみ、高速）
pytest tests/ -v

# テスト実行（統合テスト含む、並列）
pytest tests/ -v -n 4
```

### テストカバレッジ

**目標値**: 80%以上

カバレッジレポートの確認方法:

```bash
# 単体テストのみ（高速）
pytest --cov=. --cov-report=term-missing -m "not integration"

# 全テスト
pytest --cov=. --override-ini="addopts=" --cov-report=term-missing

# HTMLレポート生成
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

### 問題の自動修正

```bash
# ruff の自動修正（インポート順序等）
ruff check . --fix

# ruff のフォーマット実行
ruff format .

# unsafe fix を含む自動修正
ruff check . --fix --unsafe-fixes
```

### プッシュ前の品質チェック

コミット・プッシュ前に以下のコマンドで全チェックを実行：

```bash
# 全チェック一括実行（単体テストのみ）
mypy . && ruff check . && ruff format --check . && pytest tests/ -v

# 全チェック一括実行（統合テスト含む、並列）
mypy . && ruff check . && ruff format --check . && pytest tests/ -v -n 4
```

## 開発ワークフロー

### 基本フロー

**推奨**: 作業ブランチ（feature/*, fix/* 等）を作成してから実装を開始してください。

1. **mainブランチの最新化**
   ```bash
   git checkout main
   git pull origin main
   ```

2. **ブランチの作成**
   ```bash
   git checkout -b feature/<task-name>
   ```

3. **開発・テスト**
   - コードの実装
   - テストの作成・実行（`pytest tests/ -v`）
   - リントチェック（`ruff check .`）

4. **コミット・プッシュ**
   ```bash
   git add .
   git commit -m "feat: 実装内容の説明"
   git push -u origin feature/your-feature-name
   ```

5. **PR作成**
   - GitHub で Pull Request を作成
   - PRテンプレートに従って記入

6. **レビュー・修正**
   - レビューコメントに対応
   - 指摘事項を修正

7. **マージ**
   - レビュー承認後、main ブランチにマージ
   - マージ後は作業ブランチを削除

### ブランチ命名規則

| プレフィックス | 用途 | 例 |
|--------------|------|-----|
| `feature/` | 新機能の追加 | `feature/add-new-component` |
| `fix/` | バグ修正 | `fix/timeout-handling-error` |
| `docs/` | ドキュメント変更 | `docs/update-readme` |
| `refactor/` | リファクタリング | `refactor/simplify-architecture` |
| `test/` | テスト関連 | `test/add-integration-tests` |

### 推奨されるプラクティス

- **mainブランチ保護**: mainブランチでの実装作業は避けてください

### コミットメッセージ規約（Conventional Commits）

```
<type>: <subject>

<body>

<footer>
```

**タイプ（type）**
- `feat:` - 新機能の追加
- `fix:` - バグ修正
- `docs:` - ドキュメントのみの変更
- `refactor:` - リファクタリング（機能追加やバグ修正を含まない）
- `test:` - テストの追加・修正
- `chore:` - その他の変更（ビルドプロセス、ツール設定等）

**例**
```
feat: 新機能の追加

- 機能の説明
- テストを追加

Closes #3
```

### 開発前チェックリスト

- [ ] main ブランチを最新化している
- [ ] 作業ブランチ（feature/*, fix/* 等）を作成している
- [ ] テストがパスすることを確認（`pytest tests/ -v`）
- [ ] リントが通ることを確認（`ruff check .`）
- [ ] 実装内容の概要を理解している

### 開発完了時チェックリスト

- [ ] 新しい機能にはテストがある
- [ ] すべてのテストがパスする
- [ ] リントが通る
- [ ] コミットメッセージが規約に従っている
- [ ] PR に必要な情報を記入している
  - 変更内容の概要
  - 関連する Issue 番号
  - テスト方法
  - スクリーンショット（該当する場合）
- [ ] CLAUDE.mdの更新が必要な変更か確認
- [ ] 必要に応じてCLAUDE.mdを更新している

## ドキュメント更新フロー

⚠️ **重要**: 新機能追加・アーキテクチャ変更時は、必ずCLAUDE.mdも更新してください。

### ドキュメント更新が必要なケース

以下の場合はCLAUDE.mdの更新が必要です：

- [ ] **新機能の追加**: 新しい主要コンポーネントを追加した場合
- [ ] **アーキテクチャ変更**: システム構造に大きな変更を加えた場合
- [ ] **プロジェクト構成の変更**: 新しいディレクトリやファイルを追加した場合
- [ ] **開発環境の変更**: 依存パッケージやツールを変更した場合

### ドキュメント更新コマンド

```bash
# 1. CLAUDE.mdを編集
vim CLAUDE.md

# 2. 変更を確認
git diff CLAUDE.md

# 3. コミット（コード変更と一緒に）
git add CLAUDE.md
git commit -m "docs: XXX機能の追加に合わせてCLAUDE.mdを更新"
```

### 担当者

ドキュメント更新の責任者：

- **PR作成者**: CLAUDE.mdの更新を実施
- **レビュワー**: ドキュメント更新の漏れを確認

### PR テンプレート推奨項目

```markdown
## 概要
<!-- 変更内容の簡潔な説明 -->

## 変更内容
<!-- 具体的な変更点を箇条書きで -->

## 関連する Issue
<!-- resolves #<issue番号> または closes #<issue番号> -->

## テスト方法
<!-- 変更内容の検証手順 -->

## スクリーンショット（該当する場合）
<!-- UI 変更がある場合のみ -->
```

### マージ後のワークフロー

PRがマージされた後、以下の手順でブランチを整理し、関連Issueをクローズします。

#### 1. 関連Issueのクローズ確認

PRのコミットメッセージに `closes #<issue番号>` が含まれている場合、GitHubは自動的にIssueをクローズします。

手動でクローズが必要な場合：

```bash
# Issueの状態を確認
gh issue view <issue番号>

# Issueをクローズ
gh issue close <issue番号>
```

#### 2. ローカルブランチの削除

```bash
# 作業ブランチを削除（mainに戻ってから）
git checkout main
git branch -d feature/your-feature-name

# 強制削除（マージされていないブランチ）
git branch -D feature/your-feature-name
```

#### 3. リモートブランチの削除

```bash
# リモートブランチを削除
git push origin --delete feature/your-feature-name

# または
git push origin :feature/your-feature-name
```

#### 4. mainブランチの最新化

```bash
git pull origin main
```

#### 5. ブランチ整理の一括コマンド

```bash
# マージ済みブランチを一括削除（ローカル）
git branch --merged | grep -v "main\|master" | xargs git branch -d

# リモートの古いブランチを一括削除
git remote prune origin
```

### マージ後チェックリスト

- [ ] PRがmainブランチにマージされている
- [ ] 関連するIssueがクローズされている（`gh issue list` で確認）
- [ ] ローカルブランチが削除されている
- [ ] リモートブランチが削除されている
- [ ] mainブランチが最新化されている
