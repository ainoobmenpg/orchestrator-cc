"""メッセージフォーマットモジュール

このモジュールでは、性格パラメータに応じたメッセージフォーマット機能を提供します。
"""

import random
from typing import Any

from orchestrator.web.team_models import Personality, TeamMessage


class MessageFormatter:
    """メッセージフォーマットクラス

    性格パラメータに応じてメッセージのトーンやスタイルを調整します。
    """

    # 絵文字リスト
    EMOJIS = {
        "thinking": ["🤔", "💭", "🧠", "🔍"],
        "success": ["✅", "🎉", "👍", "✨", "🚀"],
        "confusion": ["😕", "🤷", "❓", "🤔"],
        "concern": ["⚠️", "🤨", "😰", "🔧"],
        "greeting": ["👋", "😊", "🙌", "✨"],
        "gratitude": ["🙏", "😊", "💖", "🌟"],
        "agreement": ["👍", "✅", "💪", "🤝"],
        "suggestion": ["💡", "🔥", "⚡", "🌟"],
    }

    # 言い遣いの接頭辞・接尾辞
    PREFIXES_CASUAL = ["ね", "だね", "かな", "だよね"]
    PREFIXES_FORMAL = ["です", "でしょうか", "と思われます"]

    SUFFIXES_CASUAL = ["！", "〜", "ね", "だ"]
    SUFFIXES_FORMAL = ["。", "ます。", "でしょう。"]

    @staticmethod
    def format_message(message: TeamMessage, personality: Personality | None) -> str:
        """メッセージを性格に合わせてフォーマットします。

        Args:
            message: 元のメッセージ
            personality: 性格パラメータ（Noneの場合は元のメッセージを返す）

        Returns:
            フォーマットされたメッセージ
        """
        if not personality:
            return message.content

        formatted = message.content

        # ユーモアに応じて絵文字を追加
        if personality.humor > 70:
            formatted = MessageFormatter._add_emoji(formatted)

        # 親しさやすさに応じて言葉遣いを調整
        if personality.friendliness > 60:
            formatted = MessageFormatter._make_casual(formatted)
        elif personality.friendliness < 40:
            formatted = MessageFormatter._make_formal(formatted)

        # 社交性に応じて挨拶を追加
        if personality.socialibility > 70 and MessageFormatter._is_first_message():
            formatted = f"こんにちは！{formatted}"

        return formatted

    @staticmethod
    def _add_emoji(text: str) -> str:
        """テキストに絵文字を追加します。

        Args:
            text: 元のテキスト

        Returns:
            絵文字付きテキスト
        """
        # 絵文字をまだ含んでいない場合のみ追加
        if not any(emoji in text for emojis in MessageFormatter.EMOJIS.values() for emoji in emojis):
            emoji_list = []
            if "？" in text or "?" in text:
                emoji_list.extend(MessageFormatter.EMOJIS["thinking"])
            if "成功" in text or "完了" in text or "OK" in text:
                emoji_list.extend(MessageFormatter.EMOJIS["success"])
            if "わからない" in text or "不明" in text:
                emoji_list.extend(MessageFormatter.EMOJIS["confusion"])
            if "問題" in text or "エラー" in text:
                emoji_list.extend(MessageFormatter.EMOJIS["concern"])

            if emoji_list:
                emoji = random.choice(emoji_list)
                return f"{text} {emoji}"

        return text

    @staticmethod
    def _make_casual(text: str) -> str:
        """テキストをカジュアルにします。

        Args:
            text: 元のテキスト

        Returns:
            カジュアルなテキスト
        """
        # 文末の調整
        if text.endswith("。"):
            text = text[:-1] + random.choice(MessageFormatter.SUFFIXES_CASUAL)
        elif not text.endswith(("", "！", "？")):
            text += random.choice(MessageFormatter.SUFFIXES_CASUAL)

        return text

    @staticmethod
    def _make_formal(text: str) -> str:
        """テキストをフォーマルにします。

        Args:
            text: 元のテキスト

        Returns:
            フォーマルなテキスト
        """
        # 「だ」を「です」に変換
        text = text.replace("だ。", "です。")
        text = text.replace("だ！", "です！")

        # 絵文字の削除
        for emojis in MessageFormatter.EMOJIS.values():
            for emoji in emojis:
                text = text.replace(emoji, "")

        return text

    @staticmethod
    def _is_first_message() -> bool:
        """最初のメッセージかどうかを判定します。

        Returns:
            最初のメッセージの場合はTrue
        """
        # 簡易実装：常にTrueを返す（実際には会話のコンテキストを考慮する必要あり）
        return True


class ThinkingLogFormatter:
    """思考ログフォーマットクラス

    性格パラメータに応じて思考ログの表現を調整します。
    """

    @staticmethod
    def format_thinking(log: dict[str, Any], personality: Personality | None) -> dict[str, Any]:
        """思考ログを性格に合わせてフォーマットします。

        Args:
            log: 元の思考ログ
            personality: 性格パラメータ（Noneの場合は元のログを返す）

        Returns:
            フォーマットされた思考ログ
        """
        if not personality:
            return log

        formatted = log.copy()

        # 慎重さに応じて不確実性の表現を追加
        if personality.cautiousness > 70:
            formatted["content"] = ThinkingLogFormatter._add_uncertainty(formatted.get("content", ""))

        # 好奇心に応じて探索的な表現を追加
        if personality.curiosity > 70:
            formatted["content"] = ThinkingLogFormatter._add_exploration(formatted.get("content", ""))

        # ユーモアに応じて軽い表現を追加
        if personality.humor > 70:
            formatted["content"] = ThinkingLogFormatter._add_humor(formatted.get("content", ""))

        return formatted

    @staticmethod
    def _add_uncertainty(text: str) -> str:
        """不確実性の表現を追加します。

        Args:
            text: 元のテキスト

        Returns:
            不確実性を含むテキスト
        """
        uncertainty_phrases = [
            "かもしれません",
            "可能性があります",
            "検討してみましょう",
            "もう少し確認が必要です",
        ]

        if len(text) > 20 and not any(phrase in text for phrase in uncertainty_phrases):
            phrase = random.choice(uncertainty_phrases)
            return f"{text}{phrase} "

        return text

    @staticmethod
    def _add_exploration(text: str) -> str:
        """探索的な表現を追加します。

        Args:
            text: 元のテキスト

        Returns:
            探索的なテキスト
        """
        exploration_phrases = [
            "別のアプローチも試してみよう",
            "新しいアイデアを考えてみます",
            "もっと効率的な方法があるかも",
            "クリエイティブに考えてみましょう",
        ]

        if len(text) > 30 and not any(phrase in text for phrase in exploration_phrases):
            phrase = random.choice(exploration_phrases)
            return f"{text}。{phrase}！"

        return text

    @staticmethod
    def _add_humor(text: str) -> str:
        """ユーモアを追加します。

        Args:
            text: 元のテキスト

        Returns:
            ユーモラスなテキスト
        """
        if random.random() < 0.3:  # 30%の確率でユーモアを追加
            humorous_additions = [
                "（ちょっとわざとらしいけど）",
                "（ま、こういう時もあるよね）",
                "（笑）",
                "（失敗したらごめんね）",
            ]
            addition = random.choice(humorous_additions)
            return f"{text} {addition}"

        return text
