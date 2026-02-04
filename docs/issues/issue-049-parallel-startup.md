# Issue #49: 並列起動の検討

**作成日**: 2026-02-04
**優先度**: P1
**ステータス**: Open
**関連Issue**: #43, #46, #47, #48

---

## 概要

現在、エージェントは順番に起動されています（直列起動）。並列起動を導入することで、起動時間を短縮することを検討します。

---

## 現象

### 現在の起動順序（直列起動）

1. Grand Boss（ペイン0）起動
2. Grand Bossの起動完了を確認
3. Middle Manager（ペイン1）起動
4. Middle Managerの起動完了を確認
5. Coding Specialist（ペイン2）起動
6. Coding Specialistの起動完了を確認
7. Research Specialist（ペイン3）起動
8. Research Specialistの起動完了を確認
9. Testing Specialist（ペイン4）起動
10. Testing Specialistの起動完了を確認

**推定起動時間**: 最大97秒 × 5エージェント = 最大485秒（約8分）

### 問題点

- 直列起動のため、後のエージェントほど起動完了までに時間がかかる
- 全体の起動時間が長くなる

---

## 検討内容

### 並列起動の導入

1. **すべてのエージェントを同時に起動**
   - メリット: 起動時間が大幅に短縮
   - デメリット: リソース消費が増加

2. **バッチ起動**
   - メリット: リソース消費を抑えつつ起動時間を短縮
   - デメリット: 実装が複雑になる

3. **優先順位起動**
   - メリット: 重要なエージェントから順に起動
   - デメリット: 起動順序の管理が必要

---

## 実装方針（案）

### 案1: asyncio.gather を使用した並列起動

```python
# すべてのエージェントを並列起動
async def start_cluster_parallel(self) -> None:
    tasks = []
    for agent_config in self._config.agents:
        launcher = CCProcessLauncher(...)
        tasks.append(launcher.start())

    # すべてのエージェントを並列起動
    await asyncio.gather(*tasks)

    # すべてのエージェントの起動完了を確認
    for agent_config in self._config.agents:
        if not await self._wait_for_agent_ready(
            agent_config.name,
            timeout=30.0
        ):
            raise CCProcessLaunchError(...)
```

### 案2: バッチ起動

```python
# エージェントをバッチ単位で起動
async def start_cluster_batch(self) -> None:
    # Grand Boss と Middle Manager を先に起動
    for agent_config in self._config.agents[:2]:
        launcher = CCProcessLauncher(...)
        await launcher.start()

    # 残りのエージェントを並列起動
    tasks = []
    for agent_config in self._config.agents[2:]:
        launcher = CCProcessLauncher(...)
        tasks.append(launcher.start())

    await asyncio.gather(*tasks)
```

---

## 期待される効果

- 起動時間が大幅に短縮（最大485秒から最大97秒へ、80%短縮）
- ユーザー体験の向上

---

## 懸念事項

- リソース消費が増加する可能性があります
- エージェント間の依存関係がある場合は、並列起動ができない可能性があります

---

## テスト計画

1. 並列起動の実装
2. 10回の起動・停止サイクルを実施
3. すべてのエージェントが正常に起動することを確認
4. 起動時間が短縮していることを確認

---

## 関連ファイル

- `orchestrator/core/cc_cluster_manager.py` - クラスタ管理
- `orchestrator/core/cc_process_launcher.py` - 起動プロセス管理
