"""性格生成モジュール

このモジュールでは、チームメンバーの性格パラメータを生成する機能を提供します。
"""

from typing import Any

from orchestrator.web.team_models import Personality


class PersonalityPreset:
    """性格プリセット

    各アーチタイプに対応するステレオタイプな性格を定義します。
    """

    @staticmethod
    def team_lead() -> Personality:
        """チームリード型: バランス良く、社交的で頼りになる存在"""
        return Personality(
            socialibility=75,  # チームをまとめるリーダーシップ
            cautiousness=65,   # 決断は慎重に、でも大胆に
            humor=60,         # チームの雰囲気を和ませる
            curiosity=70,     # 新しいアイデアに積極的
            friendliness=70,   # メンバーに親身
        )

    @staticmethod
    def researcher() -> Personality:
        """研究専家型: 深く考え慎重に、少し堅物"""
        return Personality(
            socialibility=25,  # 一人で没頭したい
            cautiousness=90,   # 徹底的に検証したい
            humor=20,         # 真面目でユーモア少なめ
            curiosity=95,     # 知りたい欲が強い
            friendliness=35,   # 少し距離を置く
        )

    @staticmethod
    def coder() -> Personality:
        """コーダー型: 創造的で少し変わり者、ユーモラス"""
        return Personality(
            socialibility=45,  # コードに集中したい
            cautiousness=40,   # バグは恐いでも挑戦したい
            humor=75,         # 開発者の冗談やネタが好き
            curiosity=85,     # 新しい技術に食いつく
            friendliness=50,   # チーム内では友好的
        )

    @staticmethod
    def tester() -> Personality:
        """テスター型: 厳格で細部までこだわり、完璧主義"""
        return Personality(
            socialibility=40,  # テストに集中したい
            cautiousness=95,   # バグを見逃さないように
            humor=30,         # 真面目に仕事したい
            curiosity=50,     # バグの原因を探求
            friendliness=45,   # 建設的フィードバック
        )


class PersonalityGenerator:
    """性格生成クラス

    アーチタイプまたはプリセットベースで性格パラメータを生成します。
    """

    @staticmethod
    def from_preset(preset_name: str) -> Personality:
        """プリセットから性格を生成します。

        Args:
            preset_name: プリセット名（team_lead, researcher, coder, tester）

        Returns:
            プリセットに基づく性格パラメータ

        Raises:
            ValueError: 不明なプリセット名の場合
        """
        presets = {
            "team_lead": PersonalityPreset.team_lead,
            "researcher": PersonalityPreset.researcher,
            "coder": PersonalityPreset.coder,
            "tester": PersonalityPreset.tester,
        }

        preset_func = presets.get(preset_name)
        if not preset_func:
            raise ValueError(
                f"不明なプリセット名: {preset_name}. "
                f"有効なプリセット: {list(presets.keys())}"
            )

        return preset_func()

    @staticmethod
    def from_archetype(archetype: str) -> Personality:
        """アーチタイプから性格を生成します。

        Args:
            archetype: アーチタイプ名（team-lead, researcher, coder, tester）

        Returns:
            アーチタイプに対応する性格パラメータ

        Raises:
            ValueError: 不明なアーチタイプの場合
        """
        archetype_mapping = {
            "team-lead": "team_lead",     # チームリーダー
            "researcher": "researcher",     # 研究者
            "coder": "coder",              # コーダー
            "tester": "tester",            # テスター
            # エイリアス（互換性維持）
            "general-purpose": "team_lead",
            "coding": "coder",
            "testing": "tester",
        }

        preset_name = archetype_mapping.get(archetype)
        if not preset_name:
            raise ValueError(
                f"不明なアーチタイプ: {archetype}. "
                f"有効なアーチタイプ: {list(archetype_mapping.keys())}"
            )

        return PersonalityGenerator.from_preset(preset_name)
