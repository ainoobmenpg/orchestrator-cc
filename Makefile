.PHONY: help check fmt lint test test-all coverage clean install-dev check-fe fmt-fe lint-fe test-fe install-fe

help: ## ヘルプを表示
	@echo "使用可能なコマンド:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

check: ## 全品質チェックを実行（型チェック+リント+フォーマットチェック+単体テスト）
	@echo "=== 型チェック ==="
	mypy .
	@echo ""
	@echo "=== リントチェック ==="
	ruff check .
	@echo ""
	@echo "=== フォーマットチェック ==="
	ruff format --check .
	@echo ""
	@echo "=== 単体テスト ==="
	pytest tests/ -v -m "not integration"

check-all: check check-fe ## 全チェック+統合テスト（並列実行）
	@echo ""
	@echo "=== 統合テスト（並列実行） ==="
	pytest tests/ -v -n 4

fmt: ## コードの自動フォーマットとリント修正
	@echo "=== リント自動修正 ==="
	ruff check . --fix
	@echo ""
	@echo "=== フォーマット実行 ==="
	ruff format .

lint: ## リントチェックのみ
	ruff check .

type-check: ## 型チェックのみ
	mypy .

test: ## 単体テストのみ
	pytest tests/ -v -m "not integration"

test-all: ## 全テスト（統合テスト含む、並列実行）
	pytest tests/ -v -n 4

coverage: ## カバレッジレポート生成
	pytest --cov=. --cov-report=term-missing --cov-report=html
	@echo "HTMLレポート: htmlcov/index.html"

clean: ## キャッシュファイルを削除
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".hypothesis" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/

install-dev: ## 開発依存関係をインストール
	pip install -r requirements-dev.txt

check-fe: ## フロントエンド品質チェック（ESLint + Stylelint + Prettier check）
	@echo "=== ESLintチェック ==="
	cd orchestrator/web && npm run lint
	@echo ""
	@echo "=== Stylelintチェック ==="
	cd orchestrator/web && npm run lint:css
	@echo ""
	@echo "=== Prettierフォーマットチェック ==="
	cd orchestrator/web && npm run format:check

fmt-fe: ## フロントエンド自動フォーマット（ESLint --fix + Prettier + Stylelint --fix）
	@echo "=== ESLint自動修正 ==="
	cd orchestrator/web && npm run lint:fix
	@echo ""
	@echo "=== Stylelint自動修正 ==="
	cd orchestrator/web && npm run lint:css:fix
	@echo ""
	@echo "=== Prettierフォーマット ==="
	cd orchestrator/web && npm run format

lint-fe: ## フロントエンドリントのみ（ESLint + Stylelint）
	@echo "=== ESLintチェック ==="
	cd orchestrator/web && npm run lint
	@echo ""
	@echo "=== Stylelintチェック ==="
	cd orchestrator/web && npm run lint:css

test-fe: ## フロントエンドテスト実行
	cd orchestrator/web && npm run test

install-fe: ## フロントエンド開発依存関係をインストール
	cd orchestrator/web && npm ci

pre-commit: fmt fmt-fe check check-fe ## プリコミットチェック（フォーマット+全チェック）
