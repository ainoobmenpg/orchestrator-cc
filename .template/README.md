# Claude Code ワークフローテンプレート

Claude Code で開発する際の汎用的なワークフローテンプレートです。

## 特徴

- **開発完了の定義が明確**: PR作成までが「完了」
- **レビュー運用が体系的**: 厳格さレベル別チェックリスト
- **品質管理が標準化**: mypy, ruff, pytest の統合運用
- **再レビュー運用の最適化**: 無限ループ防止

## 対象プロジェクト

- Python プロジェクト
- 小〜中規模チーム
- GitHub を使用するプロジェクト

## 導入方法

### 1. テンプレートのコピー

```bash
# プロジェクトルートにコピー
cp -r .template/* .
```

### 2. プロジェクト固有の設定

以下のファイルをプロジェクトに合わせて編集してください：

| ファイル | 設定内容 |
|----------|----------|
| `CLAUDE.md` | プロジェクト概要、技術スタック |
| `Makefile` | ビルドコマンド、品質チェックコマンド |
| `pyproject.toml` | プロジェクト名、依存パッケージ |
| `ruff.toml` | リント・フォーマット設定 |

### 3. パラメータの置換

テンプレートファイル内の以下のプレースホルダーを置換してください：

| プレースホルダー | 説明 | 例 |
|-----------------|------|-----|
| `{{PROJECT_NAME}}` | プロジェクト名 | `my-project` |
| `{{DEFAULT_BRANCH}}` | デフォルトブランチ名 | `main` |
| `{{TEST_DIR}}` | テストディレクトリ | `tests/` |
| `{{COVERAGE_TARGET}}` | カバレッジ目標値 | `80` |

## ディレクトリ構造

```
.template/
├── CLAUDE.md.template              # メインドキュメント
├── docs/
│   ├── workflows/
│   │   ├── development-process.md.template
│   │   ├── review-process.md.template
│   │   └── post-merge-workflow.md.template
│   ├── quality/
│   │   └── quality-management.md.template
│   └── documentation/
│       └── documentation-update-process.md.template
├── .claude/
│   └── skills/
│       └── pr-review/
│           └── SKILL.md.template
├── Makefile.template
├── pyproject.toml.template
└── ruff.toml.template
```

## カスタマイズ

### ツールの変更

使用するツールを変更する場合は、以下のファイルを編集してください：

- `docs/quality/quality-management.md.template`
- `Makefile.template`

### ワークフローの変更

ワークフローをカスタマイズする場合は、以下のファイルを編集してください：

- `docs/workflows/development-process.md.template`
- `docs/workflows/review-process.md.template`

## ライセンス

CC0 1.0 Universal（パブリックドメイン）

## 貢献

改善提案は Welcome です。
