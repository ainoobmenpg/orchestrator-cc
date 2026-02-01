.PHONY: help check fmt lint test test-all coverage clean install-dev

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

check-all: check ## 全チェック+統合テスト（並列実行）
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

pre-commit: fmt check ## プリコミットチェック（フォーマット+全チェック）
