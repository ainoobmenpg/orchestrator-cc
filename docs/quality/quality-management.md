# コード品質管理

このドキュメントでは、コード品質を管理するためのツールとチェック方法について詳しく説明します。

---

## 品質チェックツール

| ツール | 役割 | 対象 |
|--------|------|------|
| **mypy** | 静的型チェック | プロジェクトルート |
| **ruff check** | リント（インポート順序・未使用変数等） | 全ファイル |
| **ruff format** | コードフォーマット | 全ファイル |
| **pytest** | テスト実行（単体テストは高速、統合テストは並列） | `tests/` |

---

## Makefileコマンド（推奨）

**※ Makefileを使用すると、コマンド入力が大幅に簡素化されます。**

```bash
# ヘルプ表示（全コマンド確認）
make help

# 全品質チェック（型チェック+リント+フォーマット+単体テスト）
make check

# 全チェック+統合テスト（並列実行）
make check-all

# 自動フォーマットとリント修正
make fmt

# 個別チェック
make lint        # リントチェックのみ
make type-check  # 型チェックのみ
make test        # 単体テストのみ
make test-all    # 全テスト（統合テスト含む）
make coverage    # カバレッジレポート

# キャッシュ削除
make clean

# 開発依存関係インストール
make install-dev
```

---

## 品質チェックコマンド（直接実行）

Makefileを使用しない場合、以下のコマンドを直接実行できます。

### 個別チェック

```bash
# 型チェック
mypy .

# リントチェック
ruff check .

# フォーマットチェック
ruff format --check .

# テスト実行（単体テストのみ、高速）
pytest tests/ -v -m "not integration"

# テスト実行（統合テスト含む、並列）
pytest tests/ -v -n 4
```

---

## テストカバレッジ

**目標値**: 80%以上

### カバレッジレポートの確認方法

```bash
# Makefile使用
make coverage

# 直接実行
pytest --cov=. --cov-report=term-missing --cov-report=html
# HTMLレポート: htmlcov/index.html
```

---

## 問題の自動修正

```bash
# Makefile使用
make fmt

# 直接実行
ruff check . --fix
ruff format .
```

---

## コミット前の品質チェック

**重要**: このチェックはコミット・プッシュ前に行いますが、**「開発完了」の定義はPR作成まで**です。
プッシュのみで完了とせず、必ずPRを作成してください。

コミット・プッシュ前に以下のコマンドで全チェックを実行：

```bash
# Makefile使用（推奨）
make check

# 直接実行
mypy . && ruff check . && ruff format --check . && pytest tests/ -v -m "not integration"
```

---

## 関連ドキュメント

- [../workflows/review-process.md](../workflows/review-process.md) - レビュー運用フロー
- [../workflows/development-process.md](../workflows/development-process.md) - 開発ワークフロー
- [../../pyproject.toml](../../pyproject.toml) - ツール設定ファイル
- [../../ruff.toml](../../ruff.toml) - リント・フォーマット設定

