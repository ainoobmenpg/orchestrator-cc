# マージ後のワークフロー

このドキュメントでは、Pull Requestがマージされた後の手続きについて詳しく説明します。

---

## 概要

PRがマージされた後、以下の手順でブランチを整理します。

---

## 1. ローカルブランチの削除

```bash
# mainブランチに戻る
git checkout main

# リモートの最新を取得
git pull origin main

# マージ済みブランチを削除
git branch -d feature/your-feature-name

# 強制削除（マージされていないブランチ）
git branch -D feature/your-feature-name
```

---

## 2. リモートブランチの削除

GitHub でプルリクエストをマージした場合、自動的にブランチは削除されます。

手動で削除する場合：

```bash
# リモートブランチの削除
git push origin --delete feature/your-feature-name
```

---

## 3. ブランチ整理の一括コマンド

```bash
# マージ済みブランチを一括削除（ローカル）
git branch --merged | grep -v "main\|master" | xargs git branch -d

# 未マージブランチを確認
git branch --no-merged
```

---

## マージ後チェックリスト

- [ ] PRが main ブランチにマージされている
- [ ] ローカルの main ブランチが最新になっている
- [ ] ローカルブランチが削除されている
- [ ] （必要に応じて）リモートブランチが削除されている

---

## 関連ドキュメント

- [review-process.md](review-process.md) - レビュー運用フロー
- [development-process.md](development-process.md) - 開発ワークフロー
