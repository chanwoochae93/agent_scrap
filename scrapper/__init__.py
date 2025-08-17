"""
웹개발 & AI 트렌드 멀티 에이전트 시스템
자동으로 최신 트렌드를 수집, 분석, 전달합니다.
"""

__version__ = "2.0.0"
__author__ = "Your Name"

from .collectors import DataCollector
from .x_embed_collector import XEmbedCollector
from .ai_agent_advanced import SmartAIAgent
from .ai_quota_manager import AIQuotaManager
from .multi_agent_system import (
    SubAgent,
    MainAgent,
    MultiAgentOrchestrator
)
from .email_reporter import EmailReporter
from .schedulers import SchedulerManager, DaemonScheduler
from .main import WebDevTrendsAgent

__all__ = [
    "DataCollector",
    "XEmbedCollector",
    "SmartAIAgent",
    "AIQuotaManager",
    "SubAgent",
    "MainAgent",
    "MultiAgentOrchestrator",
    "EmailReporter",
    "SchedulerManager",
    "DaemonScheduler",
    "WebDevTrendsAgent"
]