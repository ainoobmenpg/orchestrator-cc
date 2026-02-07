# orchestrator-cc Dashboard

Agent Teams機能を使用したマルチエージェント協調システムをリアルタイム監視するためのWebダッシュボードです。

## 技術スタック

| ライブラリ | バージョン | 用途 |
|-----------|----------|------|
| React | 19.2 | UIフレームワーク |
| Vite | 7.3 | ビルドツール |
| TypeScript | 5.9 | 型安全な開発 |
| Tailwind CSS | 4.x | スタイリング |
| Zustand | 5.0 | 状態管理 |
| TanStack Query | 5.90 | サーバー状態管理 |
| React Router | 7.13 | ルーティング |
| @dnd-kit | Modern | ドラッグ&ドロップ |
| Framer Motion | 12.33 | アニメーション |
| lucide-react | 0.563 | アイコン |
| Vitest | 4.0 | テスト |

## 開発

```bash
# 依存パッケージのインストール
npm install

# 開発サーバー起動
npm run dev

# 型チェック
npm run type-check

# リント
npm run lint

# テスト
npm run test

# テストUI
npm run test:ui

# カバレッジ
npm run test:coverage

# 本番ビルド
npm run build

# バンドル分析
npm run analyze
```

## ディレクトリ構造

```
src/
├── components/
│   ├── ui/              # 基本UIコンポーネント
│   ├── layout/          # レイアウトコンポーネント
│   ├── dashboard/       # ダッシュボードコンポーネント
│   ├── common/          # 共通コンポーネント
│   ├── onboarding/      # オンボーディング
│   └── error/           # エラー処理
├── pages/               # ページコンポーネント
├── hooks/               # カスタムフック
├── stores/              # Zustandストア
├── services/            # API・WebSocket
├── lib/                 # ユーティリティ
└── App.tsx              # エントリーポイント
```

## 環境変数

`.env.example` をコピーして `.env` を作成してください：

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

## 機能

- ✅ リアルタイム監視（WebSocket）
- ✅ チーム管理
- ✅ タスクボード（ドラッグ&ドロップ）
- ✅ メッセージログ
- ✅ 思考ログ
- ✅ タイムライン
- ✅ システムログ
- ✅ アニメーション（Framer Motion）
- ✅ 通知システム
- ✅ アクセシビリティ対応
- ✅ エラーハンドリング
- ✅ モバイル対応
- ✅ オンボーディング

## テスト

39のテストが実装されており、以下をカバーしています：

- コンポーネントテスト（Button, Badge, SummaryCards, ConnectionStatus）
- フックテスト（useAgents, useTasks, useMessages）
- ストアテスト（teamStore, notificationStore）

```bash
npm run test
```

## バンドルサイズ

- JavaScript合計: 451 kB（gzip: 142 kB）
- 全体合計: 493 kB（gzip: 150 kB）

## ライセンス

MIT License
