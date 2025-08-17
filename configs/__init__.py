"""
설정 모듈 - 프로젝트의 모든 설정을 관리합니다.
"""

from .config import CONFIG
from .multi_agent_config import MULTI_AGENT_CONFIG

__all__ = [
    "CONFIG",
    "MULTI_AGENT_CONFIG"
]

def get_config(use_multi_agent=True):
    """설정 가져오기"""
    if use_multi_agent:
        return MULTI_AGENT_CONFIG
    return CONFIG