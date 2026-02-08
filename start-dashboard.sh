#!/bin/bash
# orchestrator-cc Webダッシュボード起動スクリプト

cd "$(dirname "$0")"

# Pythonコマンドを検出（python3 → pythonの順）
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Pythonが見つかりません。Pythonをインストールしてください。" >&2
    exit 1
fi

# ポート8000が使われているか確認
PORT=8000
LsofOutput=$(lsof -i :$PORT 2>/dev/null)

if [ -n "$LsofOutput" ]; then
    # LISTEN状態のプロセスを探す
    ListenLine=$(echo "$LsofOutput" | grep "LISTEN" || echo "")

    if [ -n "$ListenLine" ]; then
        PID=$(echo "$ListenLine" | awk '{print $2}')
        CMD=$(echo "$ListenLine" | awk '{print $1}')

        # Pythonプロセスの場合はダッシュボードとみなす
        if [ "$CMD" = "Python" ] || [ "$CMD" = "python" ] || [ "$CMD" = "python3" ]; then
            echo "ダッシュボードは既に実行中です（PID: $PID）"
            echo "http://localhost:$PORT"
            exit 0
        else
            echo "Error: ポート$PORTは他のプロセスによって使われています（PID: $PID, Command: $CMD）" >&2
            exit 1
        fi
    else
        # LISTEN状態がない場合は接続のみ（クライアント側）
        echo "Warning: ポート$PORTにアクティブな接続がありますが、サーバーは見つかりません" >&2
    fi
fi

$PYTHON_CMD -m orchestrator.web.dashboard "$@"
