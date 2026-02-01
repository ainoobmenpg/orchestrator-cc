# PR #36: プロセス起動改善の設計書

**作成日**: 2026-02-02
**作成者**: eng1
**タスクID**: task-20260202080440-wu8w
**関連PR**: #36

---

## 1. 概要

orchestrator-ccのClaude Codeプロセス起動機能の改善を実装する。

### 1.1 背景

現在の実装では、プロセス起動時の待機時間がハードコードされており、環境に応じた調整ができない。また、起動完了判定はマーカー文字列の検出に依存しており、より確実な判定方法が求められている。

### 1.2 目標

1. **待機時間の可変化**: 設定ファイルで待機時間を調整可能にする
2. **起動完了判定の改善**: より確実な起動完了検知方法を実装する

---

## 2. 現状の実装

### 2.1 CCProcessConfig (cc_process_models.py)

```python
@dataclass
class CCProcessConfig:
    name: str
    role: CCProcessRole
    personality_prompt_path: str
    marker: str
    pane_index: int
    work_dir: str = "/tmp/orchestrator-cc"
    claude_path: str = "claude"
    auto_restart: bool = True
    max_restarts: int = 3
```

### 2.2 CCProcessLauncher.start() (cc_process_launcher.py)

```python
async def start(self) -> None:
    # ...
    await self._pane_io.get_response(
        self._pane_index,
        self._config.marker,
        timeout=INITIAL_TIMEOUT,  # 60.0秒固定
    )
```

### 2.3 PaneIO.get_response() (pane_io.py)

```python
async def get_response(
    self,
    pane_index: int,
    expected_marker: str,
    timeout: float = DEFAULT_TIMEOUT,  # 30.0秒固定
    poll_interval: float = DEFAULT_POLL_INTERVAL,  # 0.5秒固定
) -> str:
    # ...
    while time.time() - start_time < timeout:
        # ...
        await asyncio.sleep(poll_interval)  # 固定のポーリング間隔
```

---

## 3. 改善内容

### 3.1 待機時間の可変化（優先度: 中）

**目的**: 環境や要件に応じて待機時間を調整可能にする

#### 変更点

| ファイル | 変更内容 |
|---------|---------|
| `cc_process_models.py` | `CCProcessConfig` に `wait_time`, `poll_interval` フィールドを追加 |
| `cc_process_launcher.py` | `start()` で `self._config.wait_time` を使用 |
| `pane_io.py` | `get_response()` の `poll_interval` を呼び出し元から指定可能にする |

#### 実装詳細

##### a) CCProcessConfig にフィールド追加

```python
@dataclass
class CCProcessConfig:
    # 既存フィールド...
    name: str
    role: CCProcessRole
    personality_prompt_path: str
    marker: str
    pane_index: int
    work_dir: str = "/tmp/orchestrator-cc"
    claude_path: str = "claude"
    auto_restart: bool = True
    max_restarts: int = 3

    # 新規フィールド
    wait_time: float = 5.0  # 初期起動時の追加待機時間（秒）
    poll_interval: float = 0.5  # ポーリング間隔（秒）
```

**セキュリティ考慮事項**:
- 値範囲のバリデーションを追加（負の値を禁止）
- 過剰に大きな値によるリソース枯渇を防ぐため上限を設定

##### b) CCProcessLauncher.start() の変更

```python
async def start(self) -> None:
    # ...既存処理...

    # 初期化完了マーカーを待機
    try:
        # poll_interval を設定可能に
        await self._pane_io.get_response(
            self._pane_index,
            self._config.marker,
            timeout=INITIAL_TIMEOUT,
            poll_interval=self._config.poll_interval,
        )

        # 起動後の追加待機（Claude Codeの完全な初期化を待つ）
        await asyncio.sleep(self._config.wait_time)
    except PaneTimeoutError as e:
        # ...既存エラーハンドリング...
```

**トレードオフ**:
- メリット: 環境に応じた最適な待機時間設定が可能
- デメリット: 設定値が不適切な場合、起動失敗または無駄な待機時間が増加

### 3.2 起動完了判定の改善（優先度: 低）

**目的**: Claude Codeの起動完了をより確実に検知する

#### 現状の課題

- マーカー文字列の検出のみに依存
- プロンプトパターンが変更された場合に検知できない可能性

#### 改善案

##### a) プロンプトパターン検出の強化

Claude Codeのプロンプトパターン（`> ` など）を検出し、確実に対話モードに入っていることを確認する。

```python
async def _wait_for_prompt_ready(self, timeout: float = 10.0) -> bool:
    """Claude Codeのプロンプトが表示されていることを確認する

    Args:
        timeout: タイムアウト時間（秒）

    Returns:
        プロンプト検出に成功した場合True
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        raw_output = self._tmux.capture_pane(
            self._pane_index,
            start_line=CAPTURE_HISTORY_LINES,
        )

        # Claude Codeのプロンプトパターンを検出
        lines = raw_output.split("\n")
        for line in reversed(lines[-10:]):  # 直近10行を確認
            if line.strip().endswith("> "):
                return True

        await asyncio.sleep(self._config.poll_interval)

    return False
```

##### b) start() メソッドへの統合

```python
async def start(self) -> None:
    # ...既存処理...

    # 初期化完了マーカーを待機
    await self._pane_io.get_response(
        self._pane_index,
        self._config.marker,
        timeout=INITIAL_TIMEOUT,
        poll_interval=self._config.poll_interval,
    )

    # プロンプト準備完了を確認
    if not await self._wait_for_prompt_ready(timeout=10.0):
        raise CCProcessLaunchError(
            f"プロセス '{self._config.name}' のプロンプト起動を確認できませんでした"
        )

    # 起動後の追加待機
    await asyncio.sleep(self._config.wait_time)

    self._running = True
```

---

## 4. 設定ファイル変更

### 4.1 cc-cluster.yaml への追加フィールド

```yaml
agents:
  - name: grand_boss
    role: grand_boss
    personality_prompt_path: config/personalities/grand_boss.txt
    marker: "GRAND BOSS OK"
    pane_index: 0
    wait_time: 5.0  # 追加: 初期起動待機時間（秒）
    poll_interval: 0.5  # 追加: ポーリング間隔（秒）
```

---

## 5. テスト計画

### 5.1 ユニットテスト

| テスト項目 | 説明 |
|-----------|------|
| `test_ccprocessconfig_wait_time_validation` | 負の値、過大な値のバリデーション |
| `test_ccprocessconfig_poll_interval_validation` | poll_intervalのバリデーション |
| `test_wait_for_prompt_ready_success` | プロンプト検出成功時の動作 |
| `test_wait_for_prompt_ready_timeout` | プロンプト検出タイムアウト時の動作 |

### 5.2 統合テスト

| テスト項目 | 説明 |
|-----------|------|
| `test_process_start_with_custom_wait_time` | カスタム待機時間での起動 |
| `test_process_start_with_fast_poll_interval` | 高速ポーリングでの起動 |

---

## 6. バックワード互換性

- 新規フィールドにはデフォルト値を設定するため、既存の設定ファイルは変更なしで動作する
- デフォルト値: `wait_time=5.0`, `poll_interval=0.5`

---

## 7. リスク評価

| リスク | 影響 | 緩和策 |
|--------|------|--------|
| 不適切な設定値による起動失敗 | 中 | バリデーションとデフォルト値で保護 |
| プロンプトパターン変更による検知失敗 | 低 | 複数のパターンをサポート、フォールバック用意 |

---

## 8. 実装順序

1. **Phase 1**: 待機時間の可変化（優先度: 中）
   - CCProcessConfig へのフィールド追加
   - バリデーション実装
   - CCProcessLauncher.start() の変更
   - テスト実装

2. **Phase 2**: 起動完了判定の改善（優先度: 低）
   - _wait_for_prompt_ready() メソッド実装
   - start() への統合
   - テスト実装

---

## 9. 参考資料

- PR #36 レビューコメント
- `orchestrator/core/cc_process_models.py`
- `orchestrator/core/cc_process_launcher.py`
- `orchestrator/core/pane_io.py`
