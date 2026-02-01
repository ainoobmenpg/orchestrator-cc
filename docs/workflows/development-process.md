# 開発ワークフロー

このドキュメントでは、開発の基本的な手順と規約について詳しく説明します。

---

## 基本フロー

**推奨**: 作業ブランチ（feature/*, fix/* 等）を作成してから実装を開始してください。

### 1. mainブランチの最新化

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

### 4. コミット・プッシュ

```bash
git add .
git commit -m "feat: 実装内容の説明"
git push -u origin feature/your-feature-name
```

### 5. PR作成

- GitHub で Pull Request を作成
- PRテンプレートに従って記入

### 6. レビュー・修正

- レビューコメントに対応
- 指摘事項を修正

### 7. マージ

- レビュー承認後、main ブランチにマージ
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

- **mainブランチ保護**: mainブランチでの実装作業は避けてください

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

- [ ] main ブランチを最新化している
- [ ] 作業ブランチ（feature/*, fix/* 等）を作成している
- [ ] テストがパスすることを確認（`pytest tests/ -v`）
- [ ] リントが通ることを確認（`ruff check .`）
- [ ] 実装内容の概要を理解している

---

## 開発完了時チェックリスト

- [ ] 新しい機能にはテストがある
- [ ] すべてのテストがパスする
- [ ] リントが通る
- [ ] コミットメッセージが規約に従っている
- [ ] PR に必要な情報を記入している
  - 変更内容の概要
  - 関連する Issue 番号
  - テスト方法
  - スクリーンショット（該当する場合）
- [ ] ドキュメントの更新が必要な変更か確認
- [ ] 必要に応じてドキュメントを更新している

---

## PR テンプレート推奨項目

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

---

## 関連ドキュメント

- [review-process.md](review-process.md) - レビュー運用フロー
- [../quality/quality-management.md](../quality/quality-management.md) - コード品質管理
- [post-merge-workflow.md](post-merge-workflow.md) - マージ後のワークフロー
