"""
웹개발 & AI 트렌드 멀티 에이전트 시스템
자동으로 최신 트렌드를 수집, 분석, 전달합니다.
"""

__version__ = "3.0.0"
__author__ = "ChanwooChae"

from .collectors import DataCollector
from .x_embed_collector import XEmbedCollector
from .ai_quota_manager import AIQuotaManager
# 새로운 에이전트 클래스들을 가져오도록 수정합니다.
from .multi_agent_system import (
    CollectorAgent,
    AnalyzerAgent,
    EmailerAgent,
    CodeReviewerAgent,
    NewMultiAgentOrchestrator
)
from .email_reporter import EmailReporter
from .main import WebDevTrendsAgent

# 외부에서 사용할 수 있는 클래스 목록을 새로운 이름으로 업데이트합니다.
__all__ = [
    "DataCollector",
    "XEmbedCollector",
    "AIQuotaManager",
    "CollectorAgent",
    "AnalyzerAgent",
    "EmailerAgent",
    "CodeReviewerAgent",
    "NewMultiAgentOrchestrator",
    "EmailReporter",
    "WebDevTrendsAgent"
]