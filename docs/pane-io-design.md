# PaneIO Design Document

## 概要

tmuxペインとの入出力を管理する `PaneIO` クラスの設計文書です。

## 既存実装の分析

### 現在の実装 (`orchestrator/core/pane_io.py`)

既存の `PaneIO` クラスには以下の機能が実装されています：

| 既存メソッド | 機能 |
|-------------|------|
| `send_message()` | ペインへのコマンド送信 |
| `get_response()` | 合言葉検出による応答取得（非同期） |
| `_parse_response()` | プロンプト行除去・パース処理 |
| `_is_prompt_line()` | シェルプロンプト行判定 |

### PjM指定の要件

| 要件メソッド | 対応既存メソッド | ステータス |
|-------------|-----------------|----------|
| `send_input` | `send_message` | ⚠️ 名前不一致 |
| `get_output` | `get_response` | ⚠️ 名前不一致 |
| `wait_for_response` | `get_response` | ⚠️ 名前不一致 |
| `clear_pane` | ❌ 未実装 | ❌ 新規追加 |
| `is_ready` | ❌ 未実装 | ❌ 新規追加 |

## 設計方針

### 方針1: メソッド名の統一

PjM指定のメソッド名に合わせ、以下のエイリアス/拡張を実装します：

```python
# 既存メソッドは残しつつ、PjM指定のメソッド名を追加
def send_input(self, pane_index: int, message: str) -> None:
    """send_messageのエイリアス（PjM指定名）"""
    return self.send_message(pane_index, message)

def get_output(self, pane_index: int, expected_marker: str, ...) -> str:
    """get_responseのエイリアス（PjM指定名）"""
    return await self.get_response(pane_index, expected_marker, ...)

def wait_for_response(self, pane_index: int, expected_marker: str, ...) -> str:
    """get_outputのエイリアス（待機を強調）"""
    return await self.get_output(pane_index, expected_marker, ...)
```

### 方針2: バイナリデータ対応

現状の `tmux_session_manager.py` では `subprocess.run(text=True)` が使用されており、テキストのみを扱います。

**決定**: Phase 1ではテキストのみをサポートします。

**理由**:
- Claude Codeとの通信はテキストベースで十分
- tmuxのキャプチャは基本的にテキスト
- バイナリ対応は将来的な拡張として考慮

### 方針3: 新規メソッドの実装

#### `clear_pane()` メソッド

ペインの内容をクリアする機能です。

```python
def clear_pane(self, pane_index: int) -> None:
    """ペインの画面をクリアします。

    tmuxの send-keys -t {pane} 'clear' Enter を使用します。
    """
```

#### `is_ready()` メソッド

ペインがコマンドを受信可能な状態か確認します。

```python
def is_ready(self, pane_index: int) -> bool:
    """ペインがコマンド受信可能か確認します。

    プロンプトが表示されているかを判定します。
    """
```

## 実装仕様

### クラス図

```
┌─────────────────────────────────────────────────────────┐
│                      PaneIO                              │
├─────────────────────────────────────────────────────────┤
│ - _tmux: TmuxSessionManager                             │
│                                                         │
│ + send_input(pane_index, message): None                 │
│ + send_message(pane_index, message): None               │
│                                                         │
│ + get_output(pane_index, marker, timeout, ...): str     │
│ + get_response(pane_index, marker, timeout, ...): str   │
│ + wait_for_response(pane_index, marker, ...): str       │
│                                                         │
│ + clear_pane(pane_index): None                          │
│ + is_ready(pane_index): bool                            │
│                                                         │
│ - _parse_response(raw_output, marker): str              │
│ - _is_prompt_line(line): bool                           │
└─────────────────────────────────────────────────────────┘
```

### 型ヒント

全メソッドに適切な型ヒントを付与します。

```python
from typing import Final

DEFAULT_TIMEOUT: Final[float] = 30.0
DEFAULT_POLL_INTERVAL: Final[float] = 0.5

async def get_output(
    self,
    pane_index: int,
    expected_marker: str,
    timeout: float = DEFAULT_TIMEOUT,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
) -> str:
    ...
```

## セキュリティ考慮事項

### 1. コマンドインジェクション対策

`tmux send-keys -l` (リテラルモード) を使用するため、シェルインジェクションのリスクはありません。

### 2. bypass permissions (--dangerously-skip-permissions) 対応

このフラグは `cc_process_launcher.py` で既に使用されています。`PaneIO` クラスでは、起動済みのプロセスとの通信を行うため、直接の関与はありません。

## テスト計画

### 単体テスト

1. `send_input()` - 各種文字列、特殊文字、Unicode
2. `get_output()` - 合言葉検出、タイムアウト、プロンプト除去
3. `wait_for_response()` - 非同期待機、ポーリング
4. `clear_pane()` - コマンド送信確認
5. `is_ready()` - プロンプト検出

### 統合テスト

- `TmuxSessionManager` との連携
- 実際の tmux セッションでの動作確認

## トレードオフ

| 項目 | 選択 | 理由 |
|------|------|------|
| メソッド名 | 両方サポート | 既存コード互換性 + PjM要件 |
| バイナリ対応 | Phase 1では未実装 | Claude Code通信はテキストで十分 |
| プロンプト検出 | 正規表現パターン | 柔軟性 vs シンプルさ |
| ポーリング方式 | asyncio.sleep | シンプルで信頼性が高い |

## マイルストーン

1. **Design Doc 承認** ← 現在
2. 新規メソッド実装 (`clear_pane`, `is_ready`)
3. エイリアスメソッド実装 (`send_input`, `get_output`, `wait_for_response`)
4. テスト実装
5. ドキュメント更新
6. コミット & レビュー依頼

## 参考

- 既存実装: `orchestrator/core/pane_io.py`
- テスト: `tests/test_core/test_pane_io.py`
- tmuxマニュアル: `man tmux` (send-keys, capture-pane)
