# 技術的決定事項

このドキュメントでは、orchestrator-cc プロジェクトで行った技術的決定事項とその背景を記録します。

---

## 決定1: tmux方式の採用

### 日付
2026-02-01

### 背景

Phase 0でClaude CodeのMCPサーバーモードの基本動作は確認できましたが、以下の課題が判明しました：

1. **`--system-prompt` オプションが利用できない**
   - MCPサーバーモードでは `--system-prompt` オプションが存在しない
   - エラー: `error: unknown option '--system-prompt'`
   - 各エージェントに異なる性格設定ができない

2. **設定ファイル方式でも機能しない**
   - `.claude/settings.json` での `systemPrompt` 設定は機能しない
   - 各エージェント専用のホームディレクトリを作成するアプローチでも解決せず

### 検証結果

| 検証項目 | MCPサーバーモード | 通常モード（tmux方式） |
|---------|------------------|---------------------|
| `--system-prompt` | ❌ 利用不可 | ✅ 利用可能 |
| 設定ファイルでの性格設定 | ❌ 機能しない | - |
| 複数プロセス起動 | ⚠️ 検証未完了 | ✅ tmuxペインで可能 |
| プログラム制御 | ✅ stdin/stdoutで可能 | ✅ tmuxコマンドで可能 |
| 出力取得 | ✅ stdoutから取得 | ✅ capture-paneで取得 |

### 検証詳細（Phase 0.5）

#### V-101: tmuxで複数のClaude Codeプロセスを別ペインで起動できるか

**結果**: ✅ PASS

- tmuxセッションの作成に成功
- ペインの分割（水平分割）に成功
- 各ペインで異なる`--system-prompt`を指定してClaude Codeを起動できることを確認
- Grand Boss: 「GRAND BOSS OK」を含む応答
- Middle Manager: 「MIDDLE MANAGER OK」を含む応答

#### V-102: orchestrator-ccからtmuxペインにコマンドを送信できるか

**結果**: ✅ PASS

- Pythonから`tmux send-keys`コマンドを実行できる
- Pythonから`tmux capture-pane`コマンドを実行できる
- 複数のペインに個別にコマンドを送信できる
- 各ペインの出力を個別にキャプチャできる

#### V-103: tmux capture-paneでペインの出力を適切にパースできるか

**結果**: ✅ PASS（条件付き）

- tmux capture-paneでペインの完全な出力を取得できる
- プロンプトパターン（`ユーザー名@ホスト名`）でパースして応答を抽出できる
- **課題**: パース処理の改善が必要
- **改善案**: 正規表現でプロンプト行をより厳密に検出、または応答開始マーカーを使用

### 決定内容

**tmux方式（通常モード + ターミナルマルチプレクサー）を採用**

各エージェントをtmuxセッションの別ペインで起動し、プログラムから制御します。

```
tmuxセッション (orchestrator-cc)
├── ペイン0: Grand Boss (claude --system-prompt "...")
├── ペイン1: Middle Manager (claude --system-prompt "...")
└── ペイン2: Coding Specialist (claude --system-prompt "...")
```

### メリット

| メリット | 説明 |
|---------|------|
| **性格設定が可能** | `--system-prompt`で各エージェントに異なる役割を設定できる |
| **独立性が高い** | 各ペインが独立したClaude Codeプロセスとして動作 |
| **可視性** | tmux attachで各エージェントの状態を直接確認できる |
| **デバッグ容易** | 各ペインの出力を直接見られるのでデバッグが容易 |
| **追従性が高い** | Claude Codeの通常モードの機能をそのまま使える |

### デメリットと対策

| デメリット | 対策 |
|-----------|------|
| tmuxへの依存 | tmuxは広く普及しており、インストールは容易 |
| 出力パースの複雑さ | 合言葉（マーカー）検出方式で対応 |
| プロセス管理の複雑さ | CCProcessLauncherで監視・再起動を実装 |

### 捨てたアプローチとの比較

#### MCPサーバーモード方式

| 項目 | 評価 | 理由 |
|------|------|------|
| 性格設定 | ❌ | `--system-prompt`が使えない |
| 通信方式 | ✅ | JSON-RPC over stdioはクリーン |
| プロセス管理 | ⚠️ | 複数プロセスの管理は自前で実装必要 |
| 追従性 | ⚠️ | MCPサーバーモード固有の機能に依存 |

**結論**: 性格設定ができないため断念。

#### 設定ファイル分離アプローチ

| 項目 | 評価 | 理由 |
|------|------|------|
| 性格設定 | ❌ | settings.jsonでも機能しない |
| 永続性 | ✅ | 設定がファイルに保存される |
| 追従性 | ✅ | Claude Codeがネイティブに読み込む |
| 分離 | ✅ | 各エージェントが独立した設定を持てる |

**結論**: 検証の結果、settings.jsonでの性格設定が機能しないため断念。

### 今後の予定

tmux方式でPhase 1以降を設計・実装します。

- **Phase 1**: tmuxプロセス管理機能の実装
- **Phase 2**: エージェント間通信（tmux方式）の実装
- **Phase 3**: Webダッシュボードの実装

---

## 決定2: エージェント間通信方式（直接通信）

### 日付
2026-02-01

### 背景

エージェント間の通信方式として、以下の候補が検討されました：

1. **直接通信**: エージェント同士が直接tmuxペインにメッセージを送信
2. **メッセージバス方式**: 中央のメッセージバスを経由して通信
3. **pub/sub方式**: パブリッシュ/サブスクライブパターンでの通信

### 決定内容

**直接通信方式を採用**

```
Grand Boss ─────直接────→ Middle Manager
                           │
                           ├────直接────→ Coding & Writing Specialist
                           ├────直接────→ Research & Analysis Specialist
                           └────直接────→ Testing Specialist
```

### メリット

| メリット | 説明 |
|---------|------|
| **シンプルな実装** | 宛先のペインに直接メッセージを送るだけ |
| **通常のClaude Codeに近い** | ユーザーがClaude Codeを使うときの直接対話に近い |
| **追従性が高い** | Claude Codeに新機能が追加されたとき、そのまま使える |
| **エージェントの独立性** | 各エージェントが自律的に動作できる |
| **ログは共通クラスで対応** | MessageLoggerクラスを全エージェントが使い回せる |

### 実装イメージ

```python
class CCAgentBase:
    async def send_to(self, to_agent: str, content: str) -> str:
        """他エージェントに直接メッセージを送信"""
        # ログ記録
        self._logger.log(self._agent_id, to_agent, content)

        # 宛先のペインを取得して直接送信
        target_pane = self._cluster.get_pane(to_agent)
        self._pane_io.send_message(target_pane, content)

        # 合言葉を使って応答を取得
        expected_marker = self._cluster.get_marker(to_agent)
        response = await self._pane_io.get_response(target_pane, expected_marker)

        return response
```

### 捨てたアプローチ

#### メッセージバス方式

- デメリット: 中央コンポーネントが必要、スケーラビリティの問題
- 結論: 小規模なクラスタではオーバーエンジニアリング

#### pub/sub方式

- デメリット: 実装複雑度が高い、直接通信と比べてメリットが少ない
- 結論: 現状のエージェント構成では不必要

---

## 決定3: 非同期通信の方式（合言葉検出）

### 日付
2026-02-01

### 背景

tmux方式での非同期通信において、応答の完了をどのように検出するかが課題でした。

### 検討した方式

1. **タイムアウトのみ**: 固定時間待機してから出力を取得
2. **出力変化検出**: 出力が変化しなくなったら完了とみなす
3. **合言葉（マーカー）検出**: 特定のキーワードを検出したら完了とみなす

### 決定内容

**合言葉（マーカー）検出方式を採用**

各エージェントの応答キーワードを「合言葉」として使用し、それが検出された時点で応答完了と判定します。

### 合言葉一覧

| エージェント | 合言葉 |
|-------------|--------|
| Grand Boss | `GRAND BOSS OK` |
| Middle Manager | `MIDDLE MANAGER OK` |
| Coding & Writing Specialist | `CODING OK` |
| Research & Analysis Specialist | `RESEARCH OK` |
| Testing Specialist | `TESTING OK` |

### メリット

| メリット | 説明 |
|---------|------|
| **正確な検出** | 応答の完了を確実に判定できる |
| **無駄のない待機** | 応答が完了した時点で即座に取得 |
| **柔軟性** | 合言葉は各エージェントの性格プロンプトで定義済み |
| **タイムアウト付き** | 無限に待たずにタイムアウトでエラー処理 |

### 実装イメージ

```python
async def get_response(self, pane_index: int,
                      expected_marker: str,
                      timeout: float = 30.0) -> str:
    start_time = time.time()
    previous_output = ""

    while time.time() - start_time < timeout:
        current_output = self._tmux.capture_pane(pane_index)

        if current_output != previous_output:
            previous_output = current_output
            if expected_marker in current_output:
                return self._extract_response(current_output, expected_marker)

        await asyncio.sleep(0.5)

    raise TimeoutError(f"合言葉 '{expected_marker}' がタイムアウト")
```

### 合言葉のルール

- 各エージェントの性格プロンプトに「返信には必ず「XXX OK」を含めてください」と記載
- 合言葉は応答のどこに含まれていても良い（先頭、途中、末尾）
- 合言葉が複数回含まれる場合、最初の検出で完了とみなす
- タイムアウトデフォルト値は30秒（状況に応じて調整可能）

---

## 今後の検討事項

以下の事項は、実装の進捗に応じて再検討する可能性があります：

1. **スケーラビリティ**: エージェント数が増えた場合のアーキテクチャ変更
2. **パフォーマンス**: 通信遅延の計測と最適化
3. **エラーハンドリング**: タイムアウトや異常終了時のリカバリー戦略
4. **ログ管理**: 通信ログの保存期間・フォーマット

---

## 関連ドキュメント

- [validation.md](validation.md) - 検証結果の詳細
- [architecture.md](architecture.md) - アーキテクチャ詳細
- [specs/communication.md](specs/communication.md) - 通信方式の仕様
