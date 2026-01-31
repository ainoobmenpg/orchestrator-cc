# 思考ログ仕様

## 概要

思考ログ（Thinking Log）は、各Claude Codeインスタンスがタスクを処理する際の思考過程を記録・出力する機能です。ユーザーは思考ログを通じて、AIエージェントの意思決定プロセスを観察できます。

## 目的

1. **透明性の確保**: AIの意思決定プロセスを可視化
2. **デバッグ支援**: 意図しない動作の原因特定
3. **教育的価値**: AIの思考プロセスを学習
4. **信頼性向上**: 判断の根拠を示すことで信頼性を向上

## 思考ログの構造

### データモデル

```python
@dataclass
class ThinkingLog:
    """思考ログ"""
    content: str              # 思考の内容
    detail_level: DetailLevel # 詳細レベル
    timestamp: datetime       # タイムスタンプ
    metadata: dict[str, Any]  # メタデータ

class DetailLevel(str, Enum):
    """詳細レベル"""
    SIMPLE = "simple"       # 結果のみ
    DETAILED = "detailed"   # 詳細（デフォルト）
    VERBOSE = "verbose"     # 非常に詳細
```

### メッセージ内での表現

```json
{
  "from": "grand_boss",
  "to": "middle_manager",
  "type": "task_request",
  "content": "タスクの分解をお願い",
  "thinking": {
    "content": "これは複雑なタスクだな。Middle Managerに分解してもらおう。まずは全体の要件を整理して依頼する必要がある。",
    "detail_level": "detailed",
    "timestamp": "2026-02-01T14:32:10Z",
    "metadata": {
      "reasoning_steps": [
        "タスクの複雑さを評価",
        "適切な担当者を検討",
        "依頼内容を整理"
      ]
    }
  }
}
```

## 詳細レベル

### SIMPLE（シンプル）

```
[14:32:11] > Middle Managerへ送信: タスクの分解をお願い
```

思考ログは表示されません。結果のみを確認したい場合に使用します。

### DETAILED（詳細・デフォルト）

```
[14:32:10] > ユーザーからタスク受信: Webアプリを作って
[14:32:10] [思考] これは複雑なタスクだな。Middle Managerに分解してもらおう。
[14:32:10]         まずは全体の要件を整理して依頼する必要がある。
[14:32:10]         - フロントエンドが必要
[14:32:10]         - バックエンドが必要
[14:32:10]         - データベース設計が必要
[14:32:11] > Middle Managerへ送信: タスクの分解をお願い
```

思考の要点が表示されます。バランスの取れた表示です。

### VERBOSE（非常に詳細）

```
[14:32:10] > ユーザーからタスク受信: Webアプリを作って
[14:32:10] [思考] タスク受信: "Webアプリを作って"
[14:32:10] [思考] 分析を開始...
[14:32:10] [思考] タスクの種類: 開発タスク
[14:32:10] [思考] 複雑さの評価: 高
[14:32:10] [思考]   - 複数の技術スタックが必要
[14:32:10] [思考]   - フロントエンドとバックエンドの両方
[14:32:10] [思考]   - データベース設計が含まれる
[14:32:10] [思考] 担当者の検討...
[14:32:10] [思考]   - 自分で実装?: 可能だが効率が悪い
[14:32:10] [思考]   - Middle Manager?: 適任
[14:32:10] [思考]   - Specialistに直接?: タスク分解が必要
[14:32:10] [思考] 決定: Middle Managerに依頼
[14:32:10] [思考] 依頼内容の整理...
[14:32:10] [思考]   - タスクの概要: Webアプリ開発
[14:32:10] [思考]   - 期待する成果: タスク分解と担当者割り振り
[14:32:10] [思考]   - 優先順位: 通常
[14:32:11] > Middle Managerへ送信: タスクの分解をお願い
```

全ての思考プロセスが表示されます。デバッグ時に使用します。

## 思考ログの生成ルール

### 各役割の思考パターン

#### Grand Boss

```
1. タスク受信時の分析
   - タスクの内容を理解
   - 複雑さを評価
   - 適切な担当者を検討

2. 担当者への依頼時
   - 依頼の背景を説明
   - 期待する成果を明確化
   - 優先順位を考慮

3. 結果受信時
   - 成果を評価
   - 追加作業の必要性を検討
   - ユーザーへの報告内容を整理
```

#### Middle Manager

```
1. タスク受信時の分析
   - タスクをサブタスクに分解
   - 各サブタスクの要件を整理
   - 適切なSpecialistを選定

2. Specialistへの割り当て時
   - なぜそのSpecialistを選んだか
   - 期待する成果を明確化
   - タスク間の依存関係を考慮

3. 結果集約時
   - 各Specialistの成果を評価
   - 統合の方法を検討
   - 次のアクションを計画
```

#### Specialist

```
1. タスク受信時の分析
   - タスクの具体的な要件を確認
   - 必要なリソースを検討
   - 実装アプローチを検討

2. 実行中
   - 進捗の確認
   - 問題が発生した場合の対処
   - alternativesの検討

3. 結果報告時
   - 成果のまとめ
   - 懸念点があれば提示
   - 次のステップの提案
```

## 思考ログの出力形式

### ターミナル出力

```
[14:32:10] > Middle Managerから受信: タスクの分解が完了しました
[14:32:10] [思考] よし、これで各Specialistにタスクを割り振れるな。
[14:32:10]         - フロントエンド: Coding Specialist
[14:32:10]         - バックエンド: Coding Specialist
[14:32:10]         - DB設計: Analysis Specialist
[14:32:11] > Coding Specialistへ送信: フロントエンド実装をお願い
```

### ログファイル出力

```
2026-02-01 14:32:10 [INFO] [grand_boss] Message received from middle_manager
2026-02-01 14:32:10 [THINKING] [grand_boss] よし、これで各Specialistにタスクを割り振れるな。
2026-02-01 14:32:10 [THINKING] [grand_boss] - フロントエンド: Coding Specialist
2026-02-01 14:32:10 [THINKING] [grand_boss] - バックエンド: Coding Specialist
2026-02-01 14:32:10 [THINKING] [grand_boss] - DB設計: Analysis Specialist
2026-02-01 14:32:11 [INFO] [grand_boss] Message sent to coding_specialist
```

### Webダッシュボード表示

```
┌─────────────────────────────────────────────────────────┐
│ Grand Boss                                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ [14:32:10] ▼ Middle Managerから受信                     │
│ タスクの分解が完了しました                                │
│                                                         │
│ [14:32:10] 💭 思考                                      │
│ よし、これで各Specialistにタスクを割り振れるな。          │
│  • フロントエンド: Coding Specialist                    │
│  • バックエンド: Coding Specialist                      │
│  • DB設計: Analysis Specialist                          │
│                                                         │
│ [14:32:11] ▶ Coding Specialistへ送信                    │
│ フロントエンド実装をお願い                                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 思考ログの実装

### プロンプトによる指示

各インスタンスの性格プロンプトに思考ログの出力方法を指示します。

```
【思考ログ】
- 思考プロセスを常に詳細に出力してください
- なぜその判断をしたか、背景を説明してください
- タスクの優先順位付けの理由を示してください
- 複数の選択肢を検討した場合は、それぞれの理由を示してください
```

### メッセージ処理

```python
class CCAgentBase:
    def _extract_thinking(self, response: str) -> str | None:
        """レスポンスから思考ログを抽出"""
        # 思考ログを識別して抽出
        # フォーマットはプロンプトで指示
        pass

    def _format_thinking_log(self, thinking: str) -> str:
        """思考ログをフォーマット"""
        lines = thinking.split("\n")
        formatted = []
        for line in lines:
            formatted.append(f"         {line}")
        return "\n".join(formatted)
```

## 設定

### グローバル設定（cc-cluster.yaml）

```yaml
cc_cluster:
  thinking_log:
    enabled: true
    detail_level: "detailed"  # simple/detailed/verbose
    include_metadata: true
```

### 個別設定（各プロセス）

```yaml
processes:
  - name: "grand_boss"
    role: "grand_boss"
    thinking_log_enabled: true
    thinking_log_detail: "verbose"  # Grand Bossは詳細に

  - name: "coding_specialist"
    role: "specialist_coding"
    thinking_log_enabled: true
    thinking_log_detail: "detailed"  # Specialistは標準
```

## 思考ログのユースケース

### 1. タスク追跡

ユーザーが「なぜその担当者を選んだのか？」を理解できます。

```
[思考] フロントエンド実装なのでCoding Specialistが適任
[思考] 彼はReact/Vue.jsの経験が豊富だからだ
```

### 2. デバッグ

期待しない動作をした際、原因を特定できます。

```
[思考] エラーが発生したのでリトライする
[思考] 原因はネットワークの不安定さのようだ
[思考] タイムアウトを延長して再試行
```

### 3. 学習

AIの思考プロセスを学習できます。

```
[思考] まず要件を整理しよう
[思考] 次に依存関係を確認
[思考] 最後にスケジュールを立てる
```

## 注意点

1. **プライバシー**: 思考ログには機密情報が含まれる可能性があります
2. **コスト**: 思考ログはトークン消費量を増やします
3. **ノイズ**: VERBOSEレベルは情報が多すぎる場合があります
4. **一貫性**: 思考ログはプロンプトに依存するため、常に同じ形式とは限りません

## 今後の拡張

1. **思考ログの検索**: 過去の思考ログを検索可能にする
2. **思考ログの分析**: 思考パターンを分析・改善
3. **思考ログの要約**: 長い思考ログを要約して表示
4. **思考ログの可視化**: 思考のフローを図で表示
