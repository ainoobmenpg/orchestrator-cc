# マージ後のワークフロー

このドキュメントでは、Pull Requestがマージされた後の手続きについて詳しく説明します。

---

## 🔴 最重要: ローカル完結型

**⚠️ 重要**: このプロジェクトでは**ローカル完結型**の開発フローを採用します。**GitHubへのプッシュ・プルは不要です。**

### 方式の概要

| 項目 | 従来の方式 | 本プロジェクトの方式 |
|------|----------|-------------------|
| リモート同期 | `git pull/push` | **不要** |
| Issue管理 | GitHub Issue | ローカルIssue管理 |
| ブランチ削除 | リモート・ローカル両方 | **ローカルのみ** |

---

## 概要

PRがマージされた後、以下の手順でブランチを整理します。

---

## 1. ローカルブランチの削除

```bash
# mainブランチに戻る
git checkout main

# マージ済みブランチを削除
git branch -d feature/your-feature-name

# 強制削除（マージされていないブランチ）
git branch -D feature/your-feature-name
```

---

## 2. 作業完了の記録

ローカルのレビュードキュメントにマージ完了を記録します。

```bash
# レビュードキュメントに完了を記録
echo "## マージ完了

- マージ日: $(date '+%Y-%m-%d')
- mainブランチにマージ済み
" >> PullRequests/issue-XX-review.md
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

**ローカル完結型のチェックリスト**:

- [ ] PRがmainブランチにマージされている（ローカルで確認）
- [ ] レビュードキュメントにマージ完了を記録
- [ ] ローカルブランチが削除されている
- [ ] **リモート操作は不要であることを確認**

---

## GitHubは使用しない

このプロジェクトでは以下の操作は**不要**です：

- ❌ `git push`
- ❌ `git pull`
- ❌ `git push origin --delete`
- ❌ `gh issue close`
- ❌ `gh pr merge`

---

## 関連ドキュメント

- [review-process.md](review-process.md) - レビュー運用フロー
- [development-process.md](development-process.md) - 開発ワークフロー
