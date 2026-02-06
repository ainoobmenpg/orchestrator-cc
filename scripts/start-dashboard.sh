#!/bin/bash
# Webダッシュボード起動スクリプト
#
# orchestrator-cc Webダッシュボードを起動します。
#
# 使用方法:
#   ./scripts/start-dashboard.sh [オプション]
#
# オプション:
#   --config PATH    設定ファイルのパス（デフォルト: config/cc-cluster.yaml）
#   --host HOST      バインドするホスト（デフォルト: 127.0.0.1）
#   --port PORT      バインドするポート（デフォルト: 8000）
#   --log-level LVL  ログレベル（デフォルト: info）

set -euo pipefail

# プロジェクトルート
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 色付き出力
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== orchestrator-cc Webダッシュボード ===${NC}"
echo

# CLIコマンドでダッシュボードを起動
python3 -m orchestrator.cli dashboard "$@"
