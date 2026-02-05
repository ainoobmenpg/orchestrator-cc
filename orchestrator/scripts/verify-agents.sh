#!/bin/bash
# preSessionフック: 各エージェントの検証を行います

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Running pre-session verification..."
echo "Project root: $PROJECT_ROOT"

# ここで各エージェントの検証を行う
# 必要に応じて検証ロジックを追加

exit 0
