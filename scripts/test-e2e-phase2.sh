#!/usr/bin/env bash
# E2Eテストスクリプト - Phase2 YAML通信
#
# このスクリプトでは、実際のtmuxセッションでPhase2のYAML通信をテストします。

set -euo pipefail

# カレントディレクトリをプロジェクトルートに移動
# Git worktree環境にも対応
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && git rev-parse --show-toplevel 2>/dev/null || echo "$SCRIPT_DIR/..")"
cd "$PROJECT_ROOT"

# 色の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# セッション名（config/cc-cluster.yamlと一致させる）
SESSION_NAME="orchestrator-cc"

# クリーンアップ関数
cleanup() {
    log_info "クリーンアップ中..."

    # tmuxセッションを停止
    if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        log_info "tmuxセッションを停止します: $SESSION_NAME"
        tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true
    fi

    log_info "クリーンアップ完了"
}

# エラー時のクリーンアップ
trap cleanup EXIT INT TERM

# ========================================
# テスト開始
# ========================================

log_info "============================================"
log_info "Phase2 E2Eテスト - YAML通信"
log_info "============================================"
echo ""

# ========================================
# Step 1: 前準備
# ========================================
log_info "Step 1: 前準備"

# Pythonモジュールがインポートできるか確認
if ! python3 -c "import orchestrator" 2>/dev/null; then
    log_error "orchestratorモジュールがインポートできません"
    log_info "PYTHONPATHを設定するか、pip install -e . を実行してください"
    exit 1
fi
log_success "✓ Pythonモジュールのインポート確認"

# watchdogがインストールされているか確認
if ! python3 -c "import watchdog" 2>/dev/null; then
    log_error "watchdogモジュールがインストールされていません"
    log_info "pip3 install watchdog を実行してください"
    exit 1
fi
log_success "✓ watchdogモジュールのインストール確認"

# tmuxがインストールされているか確認
if ! command -v tmux &> /dev/null; then
    log_error "tmuxがインストールされていません"
    exit 1
fi
log_success "✓ tmuxのインストール確認"

echo ""

# ========================================
# Step 2: 既存セッションのクリーンアップ
# ========================================
log_info "Step 2: 既存セッションのクリーンアップ"

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    log_warn "既存のtmuxセッションを停止します: $SESSION_NAME"
    tmux kill-session -t "$SESSION_NAME"
fi
log_success "✓ 既存セッションのクリーンアップ完了"

echo ""

# ========================================
# Step 3: クラスタ起動
# ========================================
log_info "Step 3: クラスタ起動"

# Pythonでクラスタを起動（バックグラウンド）
log_info "クラスタを起動します..."

# CLIのstartコマンドを実行（バックグラウンドで実行）
python3 -m orchestrator.cli start --config config/cc-cluster.yaml &
CLI_PID=$!

# クラスタが起動するのを待つ
sleep 5

# tmuxセッションが作成されたか確認
if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    log_error "tmuxセッションの作成に失敗しました"
    cat /tmp/orchestrator-cc-*.log 2>/dev/null || true
    exit 1
fi
log_success "✓ tmuxセッションが作成されました: $SESSION_NAME"

# ペインの数を確認
PANE_COUNT=$(tmux list-panes -t "$SESSION_NAME" | wc -l | tr -d ' ')
log_info "ペイン数: $PANE_COUNT"

if [ "$PANE_COUNT" -lt 5 ]; then
    log_error "ペイン数が不足しています（期待: 5, 実際: $PANE_COUNT）"
    exit 1
fi
log_success "✓ 全ペインが作成されました"

echo ""

# ========================================
# Step 4: YAMLファイルの確認
# ========================================
log_info "Step 4: YAMLファイルの確認"

# queue/ディレクトリが作成されているか確認
if [ ! -d "queue" ]; then
    log_error "queue/ディレクトリが作成されていません"
    exit 1
fi
log_success "✓ queue/ディレクトリが作成されました"

# status/agents/ディレクトリが作成されているか確認
if [ ! -d "status/agents" ]; then
    log_error "status/agents/ディレクトリが作成されていません"
    exit 1
fi
log_success "✓ status/agents/ディレクトリが作成されました"

# YAMLファイルが作成されているか確認
YAML_FILES=(
    "queue/grand_boss_to_middle_manager.yaml"
    "queue/middle_manager_to_grand_boss.yaml"
    "queue/middle_manager_to_specialist_coding_writing.yaml"
    "queue/middle_manager_to_specialist_research_analysis.yaml"
    "queue/middle_manager_to_specialist_testing.yaml"
    "queue/specialist_coding_writing_to_middle_manager.yaml"
    "queue/specialist_research_analysis_to_middle_manager.yaml"
    "queue/specialist_testing_to_middle_manager.yaml"
    "status/agents/grand_boss.yaml"
    "status/agents/middle_manager.yaml"
    "status/agents/specialist_coding_writing.yaml"
    "status/agents/specialist_research_analysis.yaml"
    "status/agents/specialist_testing.yaml"
)

for yaml_file in "${YAML_FILES[@]}"; do
    if [ -f "$yaml_file" ]; then
        log_success "✓ $yaml_file が存在します"
    else
        log_warn "$yaml_file が存在しません（まだ作成されていない可能性があります）"
    fi
done

echo ""

# ========================================
# Step 5: エージェントステータスの確認
# ========================================
log_info "Step 5: エージェントステータスの確認"

for status_file in status/agents/*.yaml; do
    if [ -f "$status_file" ]; then
        log_info "📄 $status_file"
        cat "$status_file"
        echo ""
    fi
done

# ========================================
# Step 6: tmuxペインの出力確認
# ========================================
log_info "Step 6: tmuxペインの出力確認"

for i in {0..4}; do
    log_info "ペイン $i の出力:"
    tmux capture-pane -t "$SESSION_NAME:$i" -p | tail -10
    echo ""
done

# ========================================
# テスト完了
# ========================================

log_success "============================================"
log_success "E2Eテスト完了！"
log_success "============================================"
log_info ""
log_info "tmuxセッションが実行中です:"
log_info "  tmux attach -t $SESSION_NAME"
log_info ""
log_info "後始末をするには、このスクリプトをCtrl+Cで終了してください"

# ユーザーが終了するのを待つ
log_info "終了するには Ctrl+C を押してください..."
wait $CLI_PID
