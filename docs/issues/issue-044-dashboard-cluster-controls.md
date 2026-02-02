# Issue #44: Webダッシュボードからクラスタの再起動・シャットダウン機能を追加

**優先度**: P1（Feature）
**ステータス**: Open
**作成日**: 2026-02-02

---

## 概要

Webダッシュボードからクラスタの再起動（restart）とシャットダウン（shutdown）ができるようにします。

現在、ダッシュボードはクラスタの状態を監視・表示するのみで、クラスタの制御機能がありません。

---

## 機能要件

### 1. クラスタ再起動機能

- **エンドポイント**: `POST /api/cluster/restart`
- **動作**:
  - 全てのエージェントプロセスを停止
  - tmuxセッションを再作成
  - 全エージェントを再起動
  - ダッシュボードの監視を再開

### 2. クラスタシャットダウン機能

- **エンドポイント**: `POST /api/cluster/shutdown`
- **動作**:
  - 全てのエージェントプロセスを停止
  - tmuxセッションを削除
  - ダッシュボードの監視を停止
  - ダッシュボード自体は動作し続ける（再起動可能）

### 3. UI/UX

- ダッシュボードのトップに制御ボタンを追加
  - "🔄 クラスタ再起動" ボタン
  - "⏹ クラスタ停止" ボタン
- ボタンクリック時に確認ダイアログを表示
- 実行中はスピナーを表示
- WebSocketでリアルタイムに状態変化を通知

---

## 実装仕様

### バックエンド (FastAPI)

```python
# orchestrator/web/dashboard.py

@app.post("/api/cluster/restart")
async def restart_cluster():
    """クラスタを再起動します。"""
    global _cluster_manager, _cluster_monitor, _dashboard_monitor

    if _cluster_manager is None:
        raise HTTPException(status_code=400, detail="Cluster not initialized")

    try:
        # 監視を停止
        if _dashboard_monitor:
            await _dashboard_monitor.stop_monitoring()
        if _cluster_monitor:
            _cluster_monitor.stop()

        # 既存のクラスタを停止
        # TODO: クラスタ停止処理の実装

        # クラスタを再起動
        await _cluster_manager.start()

        # 監視を再開
        if _cluster_monitor:
            _cluster_monitor.start()
        if _dashboard_monitor:
            await _dashboard_monitor.start_monitoring()

        return {"message": "Cluster restarted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cluster/shutdown")
async def shutdown_cluster():
    """クラスタをシャットダウンします。"""
    global _cluster_manager, _cluster_monitor, _dashboard_monitor

    if _cluster_manager is None:
        raise HTTPException(status_code=400, detail="Cluster not initialized")

    try:
        # 監視を停止
        if _dashboard_monitor:
            await _dashboard_monitor.stop_monitoring()
        if _cluster_monitor:
            _cluster_monitor.stop()

        # クラスタを停止
        # TODO: クラスタ停止処理の実装
        # - 全エージェントプロセスを停止
        # - tmuxセッションを削除

        return {"message": "Cluster shut down successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### フロントエンド (JavaScript)

```javascript
// orchestrator/web/static/main.js

// クラスタ制御ボタン
async function restartCluster() {
    if (!confirm('クラスタを再起動します。よろしいですか？')) return;

    const btn = document.getElementById('restart-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> 再起動中...';

    try {
        const response = await fetch('/api/cluster/restart', { method: 'POST' });
        const data = await response.json();
        showNotification('success', data.message);
    } catch (error) {
        showNotification('error', '再起動に失敗しました: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '🔄 クラスタ再起動';
    }
}

async function shutdownCluster() {
    if (!confirm('クラスタを停止します。よろしいですか？\n\n停止後は再起動が必要です。')) return;

    const btn = document.getElementById('shutdown-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> 停止中...';

    try {
        const response = await fetch('/api/cluster/shutdown', { method: 'POST' });
        const data = await response.json();
        showNotification('success', data.message);

        // エージェント状態をクリア
        updateAgentsList([]);
    } catch (error) {
        showNotification('error', '停止に失敗しました: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '⏹ クラスタ停止';
    }
}
```

### HTML

```html
<!-- orchestrator/web/templates/index.html -->

<div class="cluster-controls">
    <button id="restart-btn" class="btn btn-primary" onclick="restartCluster()">
        🔄 クラスタ再起動
    </button>
    <button id="shutdown-btn" class="btn btn-danger" onclick="shutdownCluster()">
        ⏹ クラスタ停止
    </button>
</div>
```

---

## 依存関係

この機能を実装するには、以下の前提条件があります：

1. **Issue #43** の修正が完了していること
   - 特にクラスタ停止処理の実装
   - `CCProcessLauncher.terminate_process()` の修正

2. **CCClusterManager** に停止・再起動メソッドが必要
   - `async def stop()`: 全エージェントを停止
   - `async def restart()`: 停止→起動

---

## 実装順序

1. **バックエンド実装**
   - [ ] `CCClusterManager` に `stop()` メソッドを実装
   - [ ] `/api/cluster/restart` エンドポイント実装
   - [ ] `/api/cluster/shutdown` エンドポイント実装

2. **フロントエンド実装**
   - [ ] クラスタ制御ボタンを追加
   - [ ] 再起動・停止関数を実装
   - [ ] 確認ダイアログ実装
   - [ ] スピナー実装

3. **テスト**
   - [ ] 再起動が正常に動作すること
   - [ ] 停止が正常に動作すること
   - [ ] WebSocket接続が維持されること
   - [ ] エラーハンドリングが正しく動作すること

---

## 関連Issue

- #43: クラスタ起動プロセスの複数の致命的問題の修正

---

## 関連ファイル

- `orchestrator/web/dashboard.py`
- `orchestrator/web/static/main.js`
- `orchestrator/web/templates/index.html`
- `orchestrator/core/cc_cluster_manager.py`
- `orchestrator/core/cc_process_launcher.py`
