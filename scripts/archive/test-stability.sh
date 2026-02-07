#!/bin/bash
# クラスタの起動・停止を10回繰り返して、安定性を確認するテストスクリプト

set -e

MAX_ITERATIONS=10
SUCCESS_COUNT=0
FAILURE_COUNT=0
LOG_FILE="test_stability_results.txt"

# 結果ファイルを初期化
echo "クラスタ安定性テスト結果" > "$LOG_FILE"
echo "実行日時: $(date)" >> "$LOG_FILE"
echo "----------------------------------------" >> "$LOG_FILE"

for i in $(seq 1 $MAX_ITERATIONS); do
    echo "[$i/$MAX_ITERATIONS] テスト開始..."

    # tmuxセッションが残っていたら削除
    tmux kill-session -t orchestrator-cc 2>/dev/null || true
    sleep 1

    # クラスタを起動
    echo "  クラスタ起動中..."
    if python3 -m orchestrator.cli start > /tmp/start_${i}.log 2>&1; then
        START_SUCCESS=true
    else
        START_SUCCESS=false
    fi

    # 起動後の状態を確認
    sleep 5
    SESSION_EXISTS=$(tmux list-sessions 2>&1 | grep -c orchestrator-cc || echo "0")

    if [ "$SESSION_EXISTS" -gt 0 ]; then
        # 各ペインの状態を確認
        PANE_0_OK=$(tmux capture-pane -t orchestrator-cc:0.0 -p | grep -c "GRAND BOSS OK" || echo "0")
        PANE_1_OK=$(tmux capture-pane -t orchestrator-cc:0.1 -p | grep -c "MIDDLE MANAGER OK" || echo "0")
        PANE_2_OK=$(tmux capture-pane -t orchestrator-cc:0.2 -p | grep -c "CODING OK" || echo "0")
        PANE_3_OK=$(tmux capture-pane -t orchestrator-cc:0.3 -p | grep -c "RESEARCH OK" || echo "0")
        PANE_4_OK=$(tmux capture-pane -t orchestrator-cc:0.4 -p | grep -c "TESTING OK" || echo "0")

        TOTAL_OK=$((PANE_0_OK + PANE_1_OK + PANE_2_OK + PANE_3_OK + PANE_4_OK))

        if [ "$TOTAL_OK" -eq 5 ]; then
            echo "  ✓ 起動成功（すべてのエージェントがOK）"
            echo "[$i] SUCCESS: All agents started successfully" >> "$LOG_FILE"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        else
            echo "  ✗ 起動失敗（エージェントの応答なし: $TOTAL_OK/5）"
            echo "[$i] FAILURE: Not all agents responded ($TOTAL_OK/5)" >> "$LOG_FILE"
            FAILURE_COUNT=$((FAILURE_COUNT + 1))
        fi
    else
        echo "  ✗ 起動失敗（tmuxセッションなし）"
        echo "[$i] FAILURE: No tmux session created" >> "$LOG_FILE"
        FAILURE_COUNT=$((FAILURE_COUNT + 1))
    fi

    # クラスタを停止
    echo "  クラスタ停止中..."
    python3 -m orchestrator.cli stop > /dev/null 2>&1 || true
    tmux kill-session -t orchestrator-cc 2>/dev/null || true
    sleep 2

    echo ""
done

# 結果を表示
echo "----------------------------------------"
echo "テスト結果"
echo "----------------------------------------"
echo "総実行回数: $MAX_ITERATIONS"
echo "成功: $SUCCESS_COUNT"
echo "失敗: $FAILURE_COUNT"
echo "成功率: $(echo "scale=1; $SUCCESS_COUNT * 100 / $MAX_ITERATIONS" | bc)%"

echo "" >> "$LOG_FILE"
echo "----------------------------------------" >> "$LOG_FILE"
echo "テスト結果サマリ" >> "$LOG_FILE"
echo "総実行回数: $MAX_ITERATIONS" >> "$LOG_FILE"
echo "成功: $SUCCESS_COUNT" >> "$LOG_FILE"
echo "失敗: $FAILURE_COUNT" >> "$LOG_FILE"
echo "成功率: $(echo "scale=1; $SUCCESS_COUNT * 100 / $MAX_ITERATIONS" | bc)%" >> "$LOG_FILE"

if [ "$SUCCESS_COUNT" -eq "$MAX_ITERATIONS" ]; then
    echo "✓ すべてのテストが成功しました！"
    exit 0
else
    echo "✗ 一部のテストが失敗しました。詳細は $LOG_FILE を確認してください。"
    exit 1
fi
