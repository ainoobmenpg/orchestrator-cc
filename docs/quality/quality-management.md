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

## 品質チェックコマンド

### 個別チェック

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

---

## テストカバレッジ

**目標値**: 80%以上

### カバレッジレポートの確認方法

```bash
# 単体テストのみ（高速）
pytest --cov=. --cov-report=term-missing -m "not integration"

# 全テスト
pytest --cov=. --override-ini="addopts=" --cov-report=term-missing

# HTMLレポート生成
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

---

## 問題の自動修正

```bash
# ruff の自動修正（インポート順序等）
ruff check . --fix

# ruff のフォーマット実行
ruff format .

# unsafe fix を含む自動修正
ruff check . --fix --unsafe-fixes
```

---

## プッシュ前の品質チェック

コミット・プッシュ前に以下のコマンドで全チェックを実行：

```bash
# 全チェック一括実行（単体テストのみ）
mypy . && ruff check . && ruff format --check . && pytest tests/ -v

# 全チェック一括実行（統合テスト含む、並列）
mypy . && ruff check . && ruff format --check . && pytest tests/ -v -n 4
```

---

## 関連ドキュメント

- [../workflows/review-process.md](../workflows/review-process.md) - レビュー運用フロー
- [../workflows/development-process.md](../workflows/development-process.md) - 開発ワークフロー
