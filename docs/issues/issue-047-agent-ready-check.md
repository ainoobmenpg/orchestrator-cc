# Issue #47: エージェント起動完了の個別確認

**作成日**: 2026-02-04
**優先度**: P0
**ステータス**: Open
**関連Issue**: #43, #46

---

## 概要

現在、クラスタ起動時に5エージェント中3エージェントしか応答していません。各エージェントの起動完了を個別に確認することで、すべてのエージェントの応答を保証します。

---

## 現象

### 安定性テスト結果

| 回数 | 応答エージェント数 |
|------|------------------:|
| 3-8 | 3/5 |

- **平均応答エージェント数**: 3/5
- **応答率**: 60% (3/5)

### 原因

エージェントは順番に起動されるため、後のエージェントほど起動完了までに時間がかかります。現在の実装では、クラスタ全体の起動完了を待機しているため、後のエージェントが応答する前にテストが終了してしまいます。

---

## 修正内容

### 各エージェントの起動完了を個別に確認

**ファイル**: `orchestrator/core/cc_cluster_manager.py`

現在の実装：
```python
# 全エージェントを起動
for agent_config in self._config.agents:
    launcher = CCProcessLauncher(...)
    await launcher.start()
```

修正後の実装：
```python
# 全エージェントを起動
for agent_config in self._config.agents:
    launcher = CCProcessLauncher(...)
    await launcher.start()

    # エージェントごとに起動完了を確認
    if not await self._wait_for_agent_ready(
        agent_config.name,
        timeout=30.0
    ):
        logger.warning(f"エージェント {agent_config.name} の起動完了を確認できませんでした")
```

---

## 期待される効果

- すべてのエージェント（5/5）が応答するようになる
- 応答率が60%から100%に向上する

---

## テスト計画

1. 修正実施後、再度10回の起動・停止サイクルを実施
2. すべての起動で5/5エージェントが応答することを確認
3. 応答率が100%であることを確認

---

## 関連ファイル

- `orchestrator/core/cc_cluster_manager.py` - クラスタ管理
- `orchestrator/core/cc_process_launcher.py` - 起動プロセス管理
