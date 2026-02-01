# マージ後のワークフロー

このドキュメントでは、Pull Requestがマージされた後の手続きについて詳しく説明します。

---

## 概要

PRがマージされた後、以下の手順でブランチを整理し、関連Issueをクローズします。

---

## 1. 関連Issueのクローズ確認

PRのコミットメッセージに `closes #<issue番号>` が含まれている場合、GitHubは自動的にIssueをクローズします。

### 手動でクローズが必要な場合

```bash
# Issueの状態を確認
gh issue view <issue番号>

# Issueをクローズ
gh issue close <issue番号>
```

---

## 2. ローカルブランチの削除

```bash
# 作業ブランチを削除（mainに戻ってから）
git checkout main
git branch -d feature/your-feature-name

# 強制削除（マージされていないブランチ）
git branch -D feature/your-feature-name
```

---

## 3. リモートブランチの削除

```bash
# リモートブランチを削除
git push origin --delete feature/your-feature-name

# または
git push origin :feature/your-feature-name
```

---

## 4. mainブランチの最新化

```bash
git pull origin main
```

---

## 5. ブランチ整理の一括コマンド

```bash
# マージ済みブランチを一括削除（ローカル）
git branch --merged | grep -v "main\|master" | xargs git branch -d

# リモートの古いブランチを一括削除
git remote prune origin
```

---

## マージ後チェックリスト

- [ ] PRがmainブランチにマージされている
- [ ] 関連するIssueがクローズされている（`gh issue list` で確認）
- [ ] ローカルブランチが削除されている
- [ ] リモートブランチが削除されている
- [ ] mainブランチが最新化されている

---

## 関連ドキュメント

- [review-process.md](review-process.md) - レビュー運用フロー
- [development-process.md](development-process.md) - 開発ワークフロー
