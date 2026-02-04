# Issue #45: Rustへの移行可能性調査

**優先度**: P2（検討）
**ステータス**: Open
**作成日**: 2026-02-04

---

## 概要

orchestrator-cc を Python から Rust に移行する実現可能性を調査します。

Rust のメモリ安全性、データ競合の防止、高いパフォーマンスは魅力的ですが、現在のアーキテクチャ（tmux 制御、プロセス管理、ファイル監視、Web ダッシュボード）が Rust で実現可能かどうかを検証します。

---

## 背景

### Python 版の現状

| 項目 | 現行実装 |
|------|----------|
| **言語** | Python 3.10+ |
| **tmux 制御** | サブプロセス + tmux コマンド |
| **プロセス管理** | subprocess, asyncio |
| **ファイル監視** | watchdog |
| **Web フレームワーク** | FastAPI |
| **WebSocket** | FastAPI WebSocket |
| **設定ファイル** | PyYAML |

### 移行を検討する理由

1. **メモリ安全性**: Rust の所有権システムによるコンパイル時の安全性チェック
2. **データ競合防止**: 並行処理の安全性が保証される
3. **パフォーマンス**: C++ に匹敵する実行速度
4. **デプロイ簡易性**: 単一のバイナリで配布可能（Python 依存なし）
5. **型安全性**: 強力な型システムで実行時エラーを削減

---

## 機能別実現可能性調査結果

| 機能 | Python 現行 | Rust 実装 | ライブラリ/ツール | 評価 |
|------|-------------|-----------|-------------------|------|
| **tmux 制御** | サブプロセス + tmux コマンド | ライブラリまたは CLI 制御 | [tmux-rs](https://richardscollin.github.io/tmux-rs/), [tmux-interface-rs](https://github.com/AntonGepting/tmux-interface-rs), [rusmux](https://github.com/MeirKriheli/rusmux) | ✅ **2025年7月に tmux 完全 Rust ポートがリリース** |
| **プロセス管理** | subprocess, asyncio | std::process, tokio::process | [std::process::Command](https://doc.rust-lang.org/std/process/struct.Command.html), [tokio::process](https://danielmschmidt.de/posts/2023-03-23-managing-processes-in-rust/), [google/rust-shell](https://github.com/google/rust-shell) | ✅ 標準ライブラリで十分 |
| **ファイル監視** | watchdog | notify クレート | [notify](https://docs.rs/notify/), [notify-rs/notify](https://github.com/notify-rs/notify) | ✅ alacritty, deno, rust-analyzer 等で実績 |
| **YAML 処理** | PyYAML | serde 系 | [serde-saphyr](https://users.rust-lang.org/t/new-serde-deserialization-framework-for-yaml-data-that-parses-yaml-into-rust-structures-without-building-syntax-tree/134306) (2025年9月リリース) | ✅ 新しいライブラリが利用可能 |
| **Web ダッシュボード** | FastAPI | Axum/Actix-web | [Axum](https://medium.com/rustaceans/beyond-rest-building-real-time-websockets-with-rust-and-axum-in-2025-91af7c45b5df), [Actix-web](https://www.reddit.com/r/rust/comments/1ozt50s/actixweb_vs_axum_in_20252026/) | ✅ 2025年では Axum 推奨 |
| **WebSocket** | FastAPI WebSocket | Axum WS/tokio-tungstenite | [Rust & Axum: Real-time WebSockets (2025)](https://medium.com/rustaceans/beyond-rest-building-real-time-websockets-with-rust-and-axum-in-2025-91af7c45b5df) | ✅ 10,000+ throughput 達成可能 |

### 結論

**全機能が Rust で実現可能**

2025年時点で、主要なライブラリが成熟しており、実現可能性は高いと判断されます。

---

## 技術スタック提案

### 推奨 Cargo.toml

```toml
[package]
name = "orchestrator-cc"
version = "0.1.0"
edition = "2021"

[dependencies]
# 非同期ランタイム
tokio = { version = "1.40", features = ["full"] }

# tmux 制御
tmux-rs = "0.1"  # 2025年7月リリースの完全ポート

# ファイル監視
notify = "6.1"

# YAML 処理
serde = { version = "1.0", features = ["derive"] }
serde-saphyr = "0.1"  # 2025年9月リリース

# Web フレームワーク（2025年推奨）
axum = "0.7"
tower = "0.5"
tower-http = { version = "0.5", features = ["cors", "trace", "compression"] }

# WebSocket
tokio-tungstenite = "0.24"

# プロセス管理（標準ライブラリ使用）
# std::process

# ロギング
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }

# エラーハンドリング
anyhow = "1.0"
thiserror = "1.0"

# クローン
clap = { version = "4.5", features = ["derive"] }

# 設定管理
config = "0.14"
```

---

## 推奨されるアプローチ

### オプション1: 漸進的移行（推奨）

リスクを分散させ、段階的に検証しながら移行します。

```
Phase 1: コア機能を Rust で実装（Python から呼び出し）
  ├─ tmux セッション管理モジュール
  ├─ プロセス制御モジュール
  └─ ファイル監視モジュール
  実装方式: PyO3 で Python から Rust モジュールを呼び出し

Phase 2: Web ダッシュボードを Rust に移行
  ├─ Axum による API サーバー
  ├─ WebSocket エンドポイント
  └─ フロントエンドとの統合
  実装方式: Rust サーバーを別プロセスで起動

Phase 3: 完全移行
  ├─ Python 依存の完全削除
  ├─ エージェントロジックの Rust 化
  └─ 単一バイナリでのデプロイ
```

**メリット**:
- リスク分散
- 段階的な検証が可能
- 移行中もシステムを稼働可能

**デメリット**:
- 移行期間が長い
- 一時的に 2 言語が混在

---

### オプション2: 新規プロジェクトとして並行開発

- 現行の Python 版はメンテナンスモード
- 新機能は Rust 版で開発
- 並行して運用し、成熟したら切り替え

**メリット**:
- 移行リスクが低い
- 両方の選択肢を維持

**デメリット**:
- 開発リソースが分散される

---

### オプション3: 完全書き直し

- 一から Rust で書き直す
- Python 版はアーカイブ

**メリット**:
- アーキテクチャの最適化が可能
- 技術的負債の解消

**デメリット**:
- 工数が大きい
- 検証コストが高い

---

## メリット・デメリット分析

### Rust 移行のメリット

| 項目 | 説明 |
|------|------|
| **メモリ安全性** | コンパイル時の所有権チェックでバグを防止 |
| **データ競合防止** | 並行処理の安全性が保証される |
| **パフォーマンス** | C++ に匹敵する実行速度、ゼロコスト抽象化 |
| **デプロイ簡易性** | 単一のバイナリで配布可能（Python 依存なし） |
| **型安全性** | 強力な型システムで実行時エラーを削減 |
| **スレッド安全性** | コンパイル時にデータ競合を検出 |

### Rust 移行のデメリット・課題

| 項目 | 説明 |
|------|------|
| **開発工数** | Python の約 2-3 倍の工数（学習コスト含む） |
| **LLM 統合** | Anthropic API 等は Python SDK が公式サポート |
| **tmux 依存** | 外部プロセス制御のアーキテクチャは変わらない |
| **開発速度** | コンパイル時間、厳格な型チェックによる開発サイクルの増加 |
| **エコシステム** | 一部ライブラリは Python 版より成熟度が低い |

---

## 工数見積もり

### 漸進的移行（推奨）の場合

| フェーズ | 作業内容 | 見積もり |
|---------|----------|----------|
| Phase 1 | コア機能の Rust 実装 | 2-3 週間 |
| Phase 2 | Web ダッシュボードの移行 | 2-3 週間 |
| Phase 3 | 完全移行とテスト | 3-4 週間 |
| **合計** | | **7-10 週間** |

### 完全書き直しの場合

| 作業内容 | 見積もり |
|----------|----------|
| アーキテクチャ設計 | 1 週間 |
| コア機能実装 | 3-4 週間 |
| Web ダッシュボード実装 | 2-3 週間 |
| テストと検証 | 2-3 週間 |
| **合計** | **8-11 週間** |

---

## アーキテクチャ提案

### プロジェクト構造

```
orchestrator-cc-rs/
├── Cargo.toml
├── src/
│   ├── main.rs              # エントリーポイント
│   ├── lib.rs               # ライブラリルート
│   ├── tmux/                # tmux 制御モジュール
│   │   ├── mod.rs
│   │   ├── session.rs       # セッション管理
│   │   └── pane.rs          # ペイン操作
│   ├── process/             # プロセス管理モジュール
│   │   ├── mod.rs
│   │   ├── launcher.rs      # Claude Code 起動
│   │   └── monitor.rs       # プロセス監視
│   ├── watch/               # ファイル監視モジュール
│   │   ├── mod.rs
│   │   └── yaml_monitor.rs  # YAML ファイル監視
│   ├── protocol/            # 通信プロトコル
│   │   ├── mod.rs
│   │   └── yaml.rs          # YAML プロトコル
│   ├── web/                 # Web ダッシュボード
│   │   ├── mod.rs
│   │   ├── api.rs           # REST API
│   │   └── websocket.rs     # WebSocket
│   └── config/              # 設定管理
│       ├── mod.rs
│       └── cluster.rs       # クラスタ設定
├── config/                  # 設定ファイル
│   └── cc-cluster.yaml
└── tests/                   # 統合テスト
```

---

## 技術的懸念点と対策

### 懸念1: tmux との統合

**懸念**: 外部プロセス制御のアーキテクチャは変わらないため、Rust 化のメリットが制限される

**対策**:
- tmux-rs を使用して、CLI 制御のオーバーヘッドを削減
- 将来的には tmux の代わりに独自のターミナル multiplexer を検討

### 懸念2: LLM 統合

**懸念**: Anthropic API の Python SDK が公式サポート

**対策**:
- HTTP クライアント（reqwest 等）で直接 API を呼び出し
- SDK がない場合でも REST API で十分対応可能

### 懸念3: 開発生産性

**懸念**: Rust の学習コストと厳格な型チェックによる開発速度低下

**対策**:
- 漸進的移行でリスクを分散
- 開発チームの Rust 研修時間を確保

---

## 関連 Issue

- #43: クラスタ起動プロセスの複数の致命的問題の修正
- #44: Webダッシュボードからクラスタの再起動・シャットダウン機能を追加

---

## 関連ファイル

- `orchestrator/core/` (Python 版コアモジュール)
- `orchestrator/web/` (Python 版 Web モジュール)
- `config/cc-cluster.yaml` (設定ファイル)

---

## 次のステップ

この調査の結果、以下のいずれかの判断が必要です：

1. **移行実行**: 漸進的移転プランの策定と開始
2. **並行開発**: Rust 版の新規プロジェクト立ち上げ
3. **現状維持**: Python 版の継続的な改善
4. **一部移行**: パフォーマンスクリティカルな部分のみ Rust 化

---

## 参考ソース

- **tmux-rs**: [Introducing tmux-rs](https://richardscollin.github.io/tmux-rs/) (2025年7月)
- **プロセス管理**: [Managing Processes in Rust](https://danielmschmidt.de/posts/2023-03-23-managing-processes-in-rust/)
- **ファイル監視**: [notify - Rust](https://docs.rs/notify/)
- **YAML**: [serde-saphyr](https://users.rust-lang.org/t/new-serde-deserialization-framework-for-yaml-data-that-parses-yaml-into-rust-structures-without-building-syntax-tree/134306) (2025年9月)
- **Web フレームワーク**: [Axum vs Actix-web: The 2025 Rust Web Framework War](https://medium.com/@indrajit7448/axum-vs-actix-web-the-2025-rust-web-framework-war-performance-vs-dx-17d0ccadd75e)
- **WebSocket**: [Rust & Axum: Real-time WebSockets (2025 Guide)](https://medium.com/rustaceans/beyond-rest-building-real-time-websockets-with-rust-and-axum-in-2025-91af7c45b5df)
