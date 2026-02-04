# 開発ワークフロー

このドキュメントでは、開発の基本的な手順と規約について詳しく説明します。

---

## 基本フロー

**推奨**: 作業ブランチ（feature/*, fix/* 等）を作成してから実装を開始してください。

### 1. main ブランチの最新化

```bash
git checkout main
git pull origin main
```

### 2. ブランチの作成

```bash
git checkout -b feature/<task-name>
```

### 3. 開発・テスト

- コードの実装
- テストの作成・実行（`pytest tests/ -v`）
- リントチェック（`ruff check .`）

### 4. コミット

```bash
git add .
git commit -m "feat: 実装内容の説明"
```

### 5. プッシュ

```bash
git push -u origin feature/<task-name>
```

### 6. プルリクエストの作成

GitHub でプルリクエストを作成します。

**⚠️ 重要**: プルリクエストを作成した時点を「開発完了」とします。

### 7. レビュー・修正

- レビューコメントに対応
- 指摘事項を修正
- 必要に応じて再レビュー

### 8. マージ

- レビュー承認後、GitHub でマージ
- マージ後は作業ブランチを削除

---

## ブランチ命名規則

| プレフィックス | 用途 | 例 |
|--------------|------|-----|
| `feature/` | 新機能の追加 | `feature/add-new-component` |
| `fix/` | バグ修正 | `fix/timeout-handling-error` |
| `docs/` | ドキュメント変更 | `docs/update-readme` |
| `refactor/` | リファクタリング | `refactor/simplify-architecture` |
| `test/` | テスト関連 | `test/add-integration-tests` |

---

## 推奨されるプラクティス

- **main ブランチ保護**: main ブランチでの実装作業は避けてください
- **小まめなコミット**: 1つのコミットで1つの機能に集中してください
- **コミットメッセージ規約**: Conventional Commets 形式に従ってください

---

## コミットメッセージ規約（Conventional Commits）

```
<type>: <subject>

<body>

<footer>
```

### タイプ（type）

- `feat:` - 新機能の追加
- `fix:` - バグ修正
- `docs:` - ドキュメントのみの変更
- `refactor:` - リファクタリング（機能追加やバグ修正を含まない）
- `test:` - テストの追加・修正
- `chore:` - その他の変更（ビルドプロセス、ツール設定等）

### 例

```
feat: 新機能の追加

- 機能の説明
- テストを追加

Closes #3
```

---

## 開発前チェックリスト

**⚠️ 最重要**: 作業を開始する前に、必ず以下を確認してください。

- [ ] **現在のブランチが main ではないこと**
  ```bash
  # 確認コマンド
  git branch --show-current

  # main だった場合、即座に作業ブランチを作成してください
  git checkout -b feature/<task-name>
  ```
- [ ] **作業ブランチ（feature/*, fix/* 等）を作成している**
- [ ] テストがパスすることを確認（`pytest tests/ -v`）
- [ ] リントが通ることを確認（`ruff check .`）
- [ ] 実装内容の概要を理解している

---

## 開発完了チェックリスト（プルリクエスト作成時）

**開発完了の定義**: プルリクエストを作成してレビュー依頼を出した時点を「開発完了」とします。

- [ ] 新しい機能にはテストがある
- [ ] すべてのテストがパスする
- [ ] リントが通る
- [ ] コミットメッセージが規約に従っている
- [ ] GitHub PR を作成している
- [ ] PR の説明に変更内容を記載している
- [ ] ドキュメントの更新が必要な場合は更新している

---

## 関連ドキュメント

- [review-process.md](review-process.md) - レビュー運用フロー
- [../quality/quality-management.md](../quality/quality-management.md) - コード品質管理
- [post-merge-workflow.md](post-merge-workflow.md) - マージ後のワークフロー
