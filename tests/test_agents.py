"""agentsモジュールのテスト

agents/__init__.py のテストです。
"""

import pytest

from agents import AGENT_PROMPTS, get_agent_prompt


class TestGetAgentPrompt:
    """get_agent_prompt関数のテスト"""

    def test_get_agent_prompt_team_lead(self):
        """team-leadプロンプトが取得できること"""
        prompt = get_agent_prompt("team-lead")
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_agent_prompt_researcher(self):
        """researcherプロンプトが取得できること"""
        prompt = get_agent_prompt("researcher")
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_agent_prompt_coder(self):
        """coderプロンプトが取得できること"""
        prompt = get_agent_prompt("coder")
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_agent_prompt_tester(self):
        """testerプロンプトが取得できること"""
        prompt = get_agent_prompt("tester")
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_agent_prompt_unknown_type(self):
        """不明なエージェントタイプでValueErrorが発生すること"""
        with pytest.raises(ValueError, match="Unknown agent type"):
            get_agent_prompt("unknown_type")


class TestAgentPromptsMapping:
    """AGENT_PROMPTSマッピングのテスト"""

    def test_agent_prompts_has_all_types(self):
        """AGENT_PROMPTSに全てのエージェントタイプが含まれること"""
        expected_types = {"team-lead", "researcher", "coder", "tester"}
        actual_types = set(AGENT_PROMPTS.keys())
        assert actual_types == expected_types

    def test_agent_prompts_values_are_callables(self):
        """AGENT_PROMPTSの値が呼び出し可能であること"""
        for agent_type, prompt_func in AGENT_PROMPTS.items():
            assert callable(prompt_func), f"{agent_type} の値が呼び出し可能ではありません"
