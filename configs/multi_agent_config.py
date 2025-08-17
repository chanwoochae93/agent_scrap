import os
from dotenv import load_dotenv
from .config import CONFIG

load_dotenv()

MULTI_AGENT_CONFIG = {
    # 메인 에이전트 (종합 분석)
    "MAIN_AGENT_EMAIL": os.getenv("MAIN_AGENT_EMAIL"),
    "MAIN_AGENT_PASSWORD": os.getenv("MAIN_AGENT_PASSWORD"),
    "MAIN_AGENT_GEMINI_KEY": os.getenv("MAIN_AGENT_GEMINI_KEY"),
    
    # 서브 에이전트 A (AI/ML 전문)
    "AGENT_A_EMAIL": os.getenv("AGENT_A_EMAIL"),
    "AGENT_A_PASSWORD": os.getenv("AGENT_A_PASSWORD"),
    "AGENT_A_GEMINI_KEY": os.getenv("AGENT_A_GEMINI_KEY"),
    
    # 서브 에이전트 B (Frontend 전문)
    "AGENT_B_EMAIL": os.getenv("AGENT_B_EMAIL"),
    "AGENT_B_PASSWORD": os.getenv("AGENT_B_PASSWORD"),
    "AGENT_B_GEMINI_KEY": os.getenv("AGENT_B_GEMINI_KEY"),
    
    # 서브 에이전트 C (Backend 전문)
    "AGENT_C_EMAIL": os.getenv("AGENT_C_EMAIL"),
    "AGENT_C_PASSWORD": os.getenv("AGENT_C_PASSWORD"),
    "AGENT_C_GEMINI_KEY": os.getenv("AGENT_C_GEMINI_KEY"),
    
    # Gmail 라벨 설정
    "GMAIL_LABEL": "AI-TREND-AGENT",
    
    # 에이전트 전문 분야
    "AGENT_SPECIALTIES": {
        "A": {
            "focus": "AI",
            "sources": ["reddit", "hackernews"],
            "keywords": ["webdev", "css", "html5", "Frontend",
            "web accessibility", "web performance", "html", "scss",
            "web development", "web design", "css-tricks", "css-frameworks",
            "css animation", "iOS issue", "iOS mobile issue"]
        },
        "B": {
            "focus": "CSS & HTML",
            "sources": ["css-tricks", "smashing", "dev.to"],
            "keywords": ["webdev", "css", "html5", "Frontend",
            "web accessibility", "web performance", "html", "scss",
            "web development", "web design", "css-tricks", "css-frameworks",
            "css animation", "iOS issue", "iOS mobile issue"]
        },
        "C": {
            "focus": "Frontend",
            "sources": ["github", "producthunt"],
            "keywords": ["webdev", "css", "html5", "Frontend",
            "web accessibility", "web performance", "html", "scss",
            "web development", "web design", "css-tricks", "css-frameworks",
            "css animation", "iOS issue", "iOS mobile issue"]
        }
    },
    
    # 병렬 처리 설정
    "PARALLEL_CONFIG": {
        "max_workers": 3,
        "timeout": 300,  # 5분
        "retry_attempts": 2
    },
    
    # 히스토리 관리
    "HISTORY_CONFIG": {
        "enabled": True,
        "retention_days": 90,
        "deduplication": True,
        "trend_analysis": True
    },
    
    # 기존 설정 상속
    **CONFIG
}