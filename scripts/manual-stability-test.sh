#!/bin/bash
# 手動安定性テストスクリプト（簡易版）

set -e

MAX_ITERATIONS=5
SUCCESS_COUNT=0
FAILURE_COUNT=0

echo "クラスタ安定性テスト（手動実行）"
echo "======================================"

for i in $(seq 1 $MAX_ITERATIONS); do
    echo ""
    echo "[$i/$MAX_ITERATIONS] テスト開始..."

    # クリーンアップ
    pkill -f "orchestrator.cli start" 2>/dev/null || true
    tmux kill-server 2>/dev/null || true
    sleep 2

    # クラスタを起動
    echo "  クラスタ起動中..."
    python3 -m orchestrator.cli start > /tmp/start_${i}.log 2>&1 &
    START_PID=$!

    # 起動完了を待つ（最大400秒 = 約6.7分）
    CHECK_COUNT=0
    MAX_CHECK=80
    while [ $CHECK_COUNT -lt $MAX_CHECK ]; do
        sleep 5
        CHECK_COUNT=$((CHECK_COUNT + 1))

        SESSION_EXISTS=$(tmux list-sessions 2>&1 | grep -c orchestrator-cc || true)
        SESSION_EXISTS=${SESSION_EXISTS:-0}
        if [ "$SESSION_EXISTS" -gt 0 ]; then
            # 各エージェントの応答を確認（履歴全体を取得）
            PANE_0_CNT=$(tmux capture-pane -t orchestrator-cc:0.0 -p -S - 2>/dev/null | grep -c "GRAND BOSS OK" || true)
            PANE_1_CNT=$(tmux capture-pane -t orchestrator-cc:0.1 -p -S - 2>/dev/null | grep -c "MIDDLE MANAGER OK" || true)
            PANE_2_CNT=$(tmux capture-pane -t orchestrator-cc:0.2 -p -S - 2>/dev/null | grep -c "CODING OK" || true)
            PANE_3_CNT=$(tmux capture-pane -t orchestrator-cc:0.3 -p -S - 2>/dev/null | grep -c "RESEARCH OK" || true)
            PANE_4_CNT=$(tmux capture-pane -t orchestrator-cc:0.4 -p -S - 2>/dev/null | grep -c "TESTING OK" || true)

            PANE_0_OK=${PANE_0_CNT:-0}
            PANE_1_OK=${PANE_1_CNT:-0}
            PANE_2_OK=${PANE_2_CNT:-0}
            PANE_3_OK=${PANE_3_CNT:-0}
            PANE_4_OK=${PANE_4_CNT:-0}

            TOTAL_OK=0
            TOTAL_OK=$((TOTAL_OK + PANE_0_OK))
            TOTAL_OK=$((TOTAL_OK + PANE_1_OK))
            TOTAL_OK=$((TOTAL_OK + PANE_2_OK))
            TOTAL_OK=$((TOTAL_OK + PANE_3_OK))
            TOTAL_OK=$((TOTAL_OK + PANE_4_OK))

            if [ "$TOTAL_OK" -ge 5 ]; then
                # 全5つのエージェントが応答すれば成功とみなす
                echo "  ✓ 起動成功（$TOTAL_OK/5 エージェントが応答）"
                echo "[$i] SUCCESS: $TOTAL_OK/5 agents responded" >> test_results.txt
                SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
                break
            fi
        fi

        if [ $CHECK_COUNT -eq $MAX_CHECK ]; then
            echo "  ✗ 起動タイムアウト"
            echo "[$i] FAILURE: Timeout" >> test_results.txt
            FAILURE_COUNT=$((FAILURE_COUNT + 1))
        fi
    done

    # クラスタを停止
    echo "  クラスタ停止中..."
    kill $START_PID 2>/dev/null || true
    python3 -m orchestrator.cli stop > /dev/null 2>&1 || true
    tmux kill-server 2>/dev/null || true
    sleep 2
done

echo ""
echo "======================================"
echo "テスト結果"
echo "======================================"
echo "総実行回数: $MAX_ITERATIONS"
echo "成功: $SUCCESS_COUNT"
echo "失敗: $FAILURE_COUNT"
echo "成功率: $(echo "scale=1; $SUCCESS_COUNT * 100 / $MAX_ITERATIONS" | bc)%"
