# Issue #43: クラスタ起動プロセスの複数の致命的問題の修正

**優先度**: P0（Critical）
**ステータス**: Open
**作成日**: 2026-02-02

---

## 概要

現在のクラスタ起動プロセスには、Pane 2-4 が zsh のままになる等の複数の致命的な問題が存在します。

---

## 問題点

### A. [低優先] CCClusterManager と CCProcessLauncher の API 不整合

- **現状**: コードレビューでは `launcher.start()` 呼び出しが指摘されましたが、実際のコードでは `launch_cc_in_pane()` を直接呼んでいるため、この問題は実際には発生していません。
- **状態**: ✅ 問題なし

---

### B. [P0] 起動直後の初期化完了待ちが成立していない

- **問題**: `launch_cc_in_pane()` はメッセージを送らずに marker を待っている
- **原因**: personality prompt の指示は「返信には必ず CODING OK を含めて」等で、起動直後に自発出力しろとは書いていない
- **結果**: 待ちがタイムアウトして、以降のエージェント起動が中断し得る（Pane が zsh のまま残る）
- **修正**: 起動確認 ping を送って marker を回収する

---

### C. [P0] プロンプト検出が `>` 前提で、Claude Code の実プロンプト（`❯`）と不一致

- **問題**: `_wait_for_prompt_ready()` が `line.rstrip().endswith(">")` で判定
- **結果**: 起動していても「起動確認できない」と誤判定 → 起動失敗扱いで中断
- **修正**: プロンプト検出を `❯` 等に対応

---

### D. [P0] Ctrl+C の送り方が誤り（`"C-c"` を文字として送っている）

- **問題**: `terminate_process()` / `_attempt_restart()` が `send_keys(..., "C-c")`
- **結果**: "Control-C" にならず、プロセス停止や自動再起動が壊れる
- **修正**: tmux のキーとして送る API を追加

---

### E. [P0] 性格プロンプトの相対パス解決が cwd 基準で危険

- **問題**: `_load_personality_prompt()` で `Path.cwd() / self._config.personality_prompt_path` としている
- **結果**: python -m orchestrator.cli をどのディレクトリから実行したかで壊れる
- **修正**: config ファイル基準で絶対パス化

---

### F. [P1] Web ダッシュボードが fastapi 依存なのに pyproject.toml に依存が無い

- **問題**: `orchestrator/web/dashboard.py` が fastapi を import しているが、pyproject.toml の dependencies に含まれていない
- **結果**: インストール直後に動かない
- **修正**: fastapi/uvicorn を依存に追加

---

## 具体パッチ案（最小差分）

### 1) CCProcessLauncher.start()/stop() を追加（P0）

```python
# orchestrator/core/cc_process_launcher.py

class CCProcessLauncher:
    async def start(self) -> None:
        """CCClusterManager互換: プロセスを起動する。"""
        await self.launch_cc_in_pane()

    async def stop(self) -> None:
        """CCClusterManager互換: プロセスを停止する。"""
        await self.terminate_process()
```

---

### 2) 起動直後の marker 待ちを成立させる（P0）

```python
# orchestrator/core/cc_process_launcher.py の launch_cc_in_pane() 内：

# 初期化完了マーカーを待機
try:
    # 起動確認のため、短い ping を送って marker を含む応答を引き出す
    self._tmux.send_keys(self._pane_index, "起動確認。指示どおりマーカーを含めて一言返答してください。")
    await self._pane_io.get_response(
        self._pane_index,
        self._config.marker,
        timeout=INITIAL_TIMEOUT,
        poll_interval=self._config.poll_interval,
    )
except PaneTimeoutError as e:
    raise CCProcessLaunchError(
        f"プロセス '{self._config.name}' の初期化がタイムアウトしました "
        f"(marker={self._config.marker}, timeout={INITIAL_TIMEOUT}秒)"
    ) from e
```

---

### 3) プロンプト検出を `❯` 対応（P0）

```python
# _wait_for_prompt_ready() と _check_process_alive() の判定を変更

-                if line.rstrip().endswith(">"):
+                tail = line.rstrip()
+                if tail.endswith((">", "❯")):
                     return True
```

※ ただし、実運用は「marker基盤」に寄せた方が堅いので、プロンプト検出は "補助" 扱いに落とすのが無難です。

---

### 4) Ctrl+C を文字列送信しない（P0）

```python
# orchestrator/core/tmux_session_manager.py

class TmuxSessionManager:
    def send_tmux_key(self, pane_index: int, key: str) -> None:
        """tmux のキー（例: C-c）を送る。文字列入力ではない。"""
        target = f"{self._session_name}:0.{pane_index}"
        cmd = ["tmux", "send-keys", "-t", target, key]
        self._run_tmux_command(cmd)
```

```python
# orchestrator/core/cc_process_launcher.py

-        self._tmux.send_keys(self._pane_index, "C-c")
+        self._tmux.send_tmux_key(self._pane_index, "C-c")
```

---

### 5) personality prompt の相対パス解決を "config ファイル基準" にする（P0）

```python
# orchestrator/core/cc_cluster_manager.py

def _load_config(self, path: str) -> CCClusterConfig:
    config_file = Path(path)
    base_dir = config_file.parent

    # ...

    for agent_data in agents_data:
        # ...

        personality_path = agent_data[CONFIG_PATH_KEY]
        p = Path(personality_path)
        if not p.is_absolute():
            personality_path = str((base_dir / p).resolve())
```

---

### 6) FastAPI ダッシュボード依存を pyproject.toml に追加（P1）

```toml
# pyproject.toml

dependencies = [
    "pyyaml>=6.0",
    "watchdog>=4.0.0",
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.27.0",
]
```

---

## 設計レビュー（徹底版：壊れやすい点と改善方向）

### 1) tmux "pane index" 前提は壊れやすい → pane_id を採用した方が安定

- pane index は「作成順」「分割順」「attach した pane」などで想定とズレやすい
- tmux には永続的な %xx 形式の pane_id がある

**改善案**:
- `create_pane()` は pane_id を返す
- config は pane_index ではなく pane_id を保持（または起動時に割り当てて state.json に保存）

---

### 2) PaneIO.get_response() は "過去ログに marker が残っている" と誤爆する

現実に起きやすいです：
- 直近100行に CODING OK が残っている
- previous_output は最初 "" なので、初回取得で即一致 → 古い応答で return

**改善案（強い順）**:
1. 各リクエストに UUID を付け、応答にも UUID を含めさせる（最強）
2. send_message() 前に "ベースライン capture" を取り、以降は差分のみ走査（中）
3. marker をよりユニークにする（弱）

---

### 3) --system-prompt '...巨大1行...' は長文で壊れやすい

- shell の最大コマンド長、クォート崩れ、文字化けなどが起きる
- prompt の改行を潰しているので、読みやすさも落ちる

**改善案**:
- Claude Code が対応しているなら --system-prompt-file を使う（最優先）
- もしくは起動後に /system-prompt 的なコマンドで注入（対応可否次第）

---

### 4) ClusterManager/Agents/YAML まわりの責務が二重化しつつある

現状：
- tmux 経由の対話（PaneIO）
- YAML queue/status のファイルプロトコル（yaml_protocol）
- watchdog 監視（YAMLMonitor）

**改善の方向**:
- "制御経路" を 1 つに寄せる（おすすめは YAML を司令系統にして、tmux は観察/手動介入にする）
- あるいは "実行と観察" を分離：
  - 実行＝YAML
  - 観察＝tmux capture/ログ + Web

---

## 直近で切るべき Issue（そのまま GitHub に投げられる粒度）

1. [P0] CCClusterManager が呼ぶ start/stop API を実装（または呼び出し修正）
   - Done: python -m orchestrator.cli start が AttributeError 無しで起動フェーズを通過

2. [P0] 起動ハンドシェイク修正：ping→marker 回収、prompt 判定は補助へ
   - Done: 全 pane で Claude Code が立ち上がり、各 agent が marker 応答できる

3. [P0] tmux Ctrl+C 送信の正規化（send_tmux_key 追加）
   - Done: stop / restart が実際にプロセスを止められる

4. [P0] personality prompt のパス解決を config 基準へ
   - Done: どのディレクトリから CLI 実行しても prompt 読み込みが成功

5. [P1] PaneIO の marker 誤爆対策（UUID 相関 or baseline capture）
   - Done: 連続タスクでも "古い応答" を拾わないテストが追加される

6. [P1] Web dashboard 依存追加＆ initialize を lifespan 起動時に呼ぶ
   - Done: pip install -e . 後に dashboard が ImportError 無しで起動

---

## テスト計画

- [ ] クラスタ起動時に全5ペインで Claude Code が起動すること
- [ ] 各エージェントが marker 応答を返すこと
- [ ] stop コマンドでプロセスが正しく停止すること
- [ ] どのディレクトリから CLI 実行しても prompt 読み込みが成功すること
- [ ] 連続タスクで "古い応答" を誤検出しないこと

---

## 関連ファイル

- `orchestrator/core/cc_process_launcher.py`
- `orchestrator/core/tmux_session_manager.py`
- `orchestrator/core/cc_cluster_manager.py`
- `pyproject.toml`

---

## 関連Issue

- #44: Webダッシュボードからクラスタの再起動・シャットダウン機能を追加
