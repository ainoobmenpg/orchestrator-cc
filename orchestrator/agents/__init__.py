"""orchestrator.agents パッケージ"""

from orchestrator.agents.cc_agent_base import (
    CCAgentBase,
    CCAgentError,
    CCAgentSendError,
    CCAgentTimeoutError,
)
from orchestrator.agents.grand_boss import GrandBossAgent
from orchestrator.agents.middle_manager import MiddleManagerAgent
from orchestrator.agents.specialists import (
    CODING_MARKER,
    CODING_SPECIALIST_NAME,
    DEFAULT_TASK_TIMEOUT,
    RESEARCH_MARKER,
    RESEARCH_SPECIALIST_NAME,
    TESTING_MARKER,
    TESTING_SPECIALIST_NAME,
    CodingWritingSpecialist,
    ResearchAnalysisSpecialist,
    TestingSpecialist,
)

__all__ = [
    "CCAgentBase",
    "CCAgentError",
    "CCAgentSendError",
    "CCAgentTimeoutError",
    "GrandBossAgent",
    "MiddleManagerAgent",
    # Specialists
    "CodingWritingSpecialist",
    "ResearchAnalysisSpecialist",
    "TestingSpecialist",
    "CODING_SPECIALIST_NAME",
    "RESEARCH_SPECIALIST_NAME",
    "TESTING_SPECIALIST_NAME",
    "CODING_MARKER",
    "RESEARCH_MARKER",
    "TESTING_MARKER",
    "DEFAULT_TASK_TIMEOUT",
]
