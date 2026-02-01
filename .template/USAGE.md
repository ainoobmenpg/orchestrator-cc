# 汎用ワークフローテンプレートの使用方法

このテンプレートを新しいプロジェクトで使用する手順を説明します。

---

## ステップ1: テンプレートのコピー

```bash
# プロジェクトルートにコピー
cp -r .template/* .
```

---

## ステップ2: パラメータの置換

以下のプレースホルダーをプロジェクトに合わせて置換してください：

### 必須パラメータ

| プレースホルダー | 説明 | 例 |
|-----------------|------|-----|
| `{{PROJECT_NAME}}` | プロジェクト名（小文字、ハイフン区切り） | `my-project` |
| `{{PROJECT_PACKAGE}}` | Pythonパッケージ名 | `my_project` |
| `{{PROJECT_DESCRIPTION}}` | プロジェクトの説明 | `My awesome project` |

### ワークフロー関連

| プレースホルダー | 説明 | デフォルト値 |
|-----------------|------|-------------|
| `{{DEFAULT_BRANCH}}` | デフォルトブランチ名 | `main` |
| `{{REMOTE_NAME}}` | リモート名 | `origin` |

### ディレクトリ関連

| プレースホルダー | 説明 | デフォルト値 |
|-----------------|------|-------------|
| `{{TEST_DIR}}` | テストディレクトリ | `tests/` |
| `{{REVIEW_DIR}}` | レビュードキュメント格納先 | `reviews/` |
| `{{MAIN_DOCS_FILE}}` | メインドキュメントファイル名 | `CLAUDE.md` |

### ツール関連

| プレースホルダー | 説明 | デフォルト値 |
|-----------------|------|-------------|
| `{{TYPE_CHECK_TOOL}}` | 型チェックツール | `mypy` |
| `{{LINT_TOOL}}` | リントツール | `ruff` |
| `{{TEST_TOOL}}` | テストツール | `pytest` |
| `{{COVERAGE_TARGET}}` | カバレッジ目標値 | `80` |

### コマンド関連

| プレースホルダー | 説明 | デフォルト値 |
|-----------------|------|-------------|
| `{{TYPE_CHECK_COMMAND}}` | 型チェックコマンド | `mypy .` |
| `{{LINT_COMMAND}}` | リントコマンド | `ruff check .` |
| `{{FORMAT_CHECK_COMMAND}}` | フォーマットチェックコマンド | `ruff format --check .` |
| `{{FORMAT_COMMAND}}` | フォーマットコマンド | `ruff format .` |
| `{{LINT_FIX_COMMAND}}` | リント修正コマンド | `ruff check . --fix` |
| `{{TEST_COMMAND_UNIT}}` | 単体テストコマンド | `pytest tests/ -v -m "not integration"` |
| `{{TEST_COMMAND_ALL}}` | 全テストコマンド | `pytest tests/ -v -n 4` |
| `{{COVERAGE_COMMAND}}` | カバレッジコマンド | `pytest --cov=. --cov-report=term-missing --cov-report=html` |
| `{{COVERAGE_HTML_REPORT}}` | カバレッジHTMLレポートパス | `htmlcov/index.html` |
| `{{QUALITY_CHECK_COMMAND}}` | 品質チェックコマンド | `make check` |
| `{{INSTALL_DEV_COMMAND}}` | 開発依存関係インストールコマンド | `pip install -r requirements-dev.txt` |

---

## ステップ3: 置換の実行

### 方法A: エディタの置換機能を使用

```bash
# VS Codeの場合
# 1. ファイル全体を置換（Cmd+Shift+H）
# 2. 正規表現で一括置換
```

### 方法B: sed コマンドを使用

```bash
# macOS
sed -i '' 's/{{PROJECT_NAME}}/your-project-name/g' **/*.md **/*.toml **/.template

# Linux
sed -i 's/{{PROJECT_NAME}}/your-project-name/g' **/*.md **/*.toml **/.template
```

### 方法C: スクリプトを使用

```bash
#!/bin/bash
# setup.sh

PROJECT_NAME="your-project-name"
PROJECT_PACKAGE="your_package"
PROJECT_DESCRIPTION="Your project description"

# 全てのテンプレートファイルで置換
find . -type f \( -name "*.template" -o -name "*.md" -o -name "*.toml" -o -name "Makefile" \) -exec sed -i '' \
  -e "s/{{PROJECT_NAME}}/$PROJECT_NAME/g" \
  -e "s/{{PROJECT_PACKAGE}}/$PROJECT_PACKAGE/g" \
  -e "s/{{PROJECT_DESCRIPTION}}/$PROJECT_DESCRIPTION/g" \
  {} +
```

---

## ステップ4: プロジェクト固有の設定

### CLAUDE.md の編集

プロジェクト固有の情報を記載してください：

```markdown
## {{PROJECT_NAME}}

<!--
ここにプロジェクト概要を記述してください

- プロジェクトの目的
- 主な特徴
- 技術スタック
- 現在の開発状況
-->
```

### Makefile の編集

プロジェクトに合わせてコマンドを調整してください。

---

## ステップ5: 動作確認

```bash
# ヘルプを表示
make help

# 品質チェックを実行
make check

# テストを実行
make test
```

---

## カスタマイズ

### ツールの変更

使用するツールを変更する場合は、以下のファイルを編集してください：

- `docs/quality/quality-management.md`
- `Makefile`
- `pyproject.toml`

### ワークフローの変更

ワークフローをカスタマイズする場合は、以下のファイルを編集してください：

- `docs/workflows/development-process.md`
- `docs/workflows/review-process.md`

---

## トラブルシューティング

### テンプレートの拡張子が残っている

```bash
# .template 拡張子を削除
find . -name "*.template" -exec sh -c 'mv "$1" "${1%.template}"' _ {} \;
```

### プレースホルダーが残っている

```bash
# 残っているプレースホルダーを確認
grep -r "{{" . --exclude-dir=.git --exclude-dir=node_modules
```

---

## ライセンス

CC0 1.0 Universal（パブリックドメイン）
