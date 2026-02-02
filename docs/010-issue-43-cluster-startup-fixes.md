# Issue #43: クラスタ起動プロセスの複数の致命的問題の修正

**作成日**: 2026-02-02
**優先度**: P0（Critical）
**担当**: eng1

---

## 概要

クラスタ起動プロセスに存在する複数の致命的な問題を修正する。

---

## 修正項目

### 1. [P0] 起動直後の初期化完了待ちが成立していない

**問題**: `launch_cc_in_pane()` はメッセージを送らずに marker を待っているが、personality prompt は起動直後に自発出力しない。

**修正**:
- 起動確認 ping を送って marker を回収する
- `orchestrator/core/cc_process_launcher.py`

### 2. [P0] プロンプト検出が `>` 前提で、Claude Code の実プロンプト（`❯`）と不一致

**問題**: `_wait_for_prompt_ready()` が `line.rstrip().endswith(">")` で判定している。

**修正**:
- `❯` にも対応
- `orchestrator/core/cc_process_launcher.py`

### 3. [P0] Ctrl+C の送り方が誤り（`"C-c"` を文字として送っている）

**問題**: `terminate_process()` / `_attempt_restart()` が `send_keys(..., "C-c")` としている。

**修正**:
- `send_tmux_key()` API を追加
- `orchestrator/core/tmux_session_manager.py`
- `orchestrator/core/cc_process_launcher.py`

### 4. [P0] 性格プロンプトの相対パス解決が cwd 基準で危険

**問題**: `_load_personality_prompt()` で `Path.cwd() / self._config.personality_prompt_path` としている。

**修正**:
- config ファイル基準で絶対パス化
- `orchestrator/core/cc_cluster_manager.py`

### 5. [P1] Web ダッシュボードが fastapi 依存なのに pyproject.toml に依存が無い

**問題**: `pyproject.toml` の dependencies に fastapi/uvicorn が含まれていない。

**修正**:
- pyproject.toml に依存を追加
- `pyproject.toml`

---

## 影響ファイル

- `orchestrator/core/cc_process_launcher.py`
- `orchestrator/core/tmux_session_manager.py`
- `orchestrator/core/cc_cluster_manager.py`
- `pyproject.toml`

---

## テスト計画

- [ ] クラスタ起動時に全5ペインで Claude Code が起動すること
- [ ] 各エージェントが marker 応答を返すこと
- [ ] stop コマンドでプロセスが正しく停止すること
- [ ] どのディレクトリから CLI 実行しても prompt 読み込みが成功すること

---

## 完了基準

- すべてのP0問題が修正され、テストがパスすること
- P1問題（fastapi依存）が追加されていること
