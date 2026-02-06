"""Agent Prompts Module

Agent Teamsで使用するエージェントのプロンプト定義を提供します。
"""

from agents.specialist_code import get_coding_specialist_prompt
from agents.specialist_research import get_research_specialist_prompt
from agents.specialist_test import get_testing_specialist_prompt
from agents.team_lead import get_team_lead_prompt

__all__ = [
    "get_team_lead_prompt",
    "get_research_specialist_prompt",
    "get_coding_specialist_prompt",
    "get_testing_specialist_prompt",
]


# エージェントプロンプトのマッピング
AGENT_PROMPTS = {
    "team-lead": get_team_lead_prompt,
    "researcher": get_research_specialist_prompt,
    "coder": get_coding_specialist_prompt,
    "tester": get_testing_specialist_prompt,
}


def get_agent_prompt(agent_type: str) -> str:
    """エージェントタイプに対応するプロンプトを返します。

    Args:
        agent_type: エージェントタイプ（team-lead, researcher, coder, tester）

    Returns:
        エージェントのシステムプロンプト

    Raises:
        ValueError: 不明なエージェントタイプの場合
    """
    if agent_type not in AGENT_PROMPTS:
        raise ValueError(f"Unknown agent type: {agent_type}. Available: {list(AGENT_PROMPTS.keys())}")

    return AGENT_PROMPTS[agent_type]()
