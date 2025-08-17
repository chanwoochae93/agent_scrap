import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    # 기본 설정
    "APP_NAME": "WebDev AI Trends Multi-Agent",
    "TIMEZONE": "Asia/Seoul",
    "OUTPUT_DIR": "outputs",
    
    # 이메일 설정
    "EMAIL_CONFIG": {
        "enabled": True,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "sender_email": os.getenv("MAIN_AGENT_EMAIL"),
        "sender_password": os.getenv("MAIN_AGENT_PASSWORD"),
        "receiver_email": os.getenv("RECEIVER_EMAIL"),
        "subject_template": "🚀 주간 웹개발 & AI 트렌드 리포트 - {date}"
    },
    
    # 스케줄 설정 (한국 시간 월요일 오전 10시)
    "SCHEDULE": {
        "type": "weekly",
        "day": "monday",
        "time": "10:00",
        "timezone": "Asia/Seoul"
    },
    
    # RSS 피드
    "RSS_FEEDS": [
        # CSS & HTML
        "https://css-tricks.com/feed/",
        "https://www.smashingmagazine.com/feed/",
        "https://developer.mozilla.org/en-US/blog/rss.xml",
        
        # AI & 웹개발
        "https://openai.com/blog/rss.xml",
        "https://www.anthropic.com/rss.xml",
        "https://web.dev/feed.xml",
        "https://dev.to/feed",
        "https://hackernoon.com/feed",
    ],
    
    # Reddit 설정
    "REDDIT_CONFIG": {
        "enabled": True,
        "client_id": os.getenv("REDDIT_CLIENT_ID"),
        "client_secret": os.getenv("REDDIT_CLIENT_SECRET"),
        "user_agent": "WebDevTrendsAgent/1.0",
        "subreddits": [
            "webdev", "css", "html5", "Frontend",
            "web accessibility", "web performance", "html", "scss",
            "web development", "web design", "css-tricks", "css-frameworks",
            "css animation", "iOS issue", "iOS mobile issue"
        ],
        "post_limit": 10,
        "time_filter": "week"
    },
    
    # X (Twitter) Embed API 설정
    "X_CONFIG": {
        "enabled": True,
        "method": "embed_api",
        "url_sources": {
            "reddit": True,
            "websites": True,
            "github": True,
            "rss": True
        },
        "monitor_sites": [
            "https://css-tricks.com",
            "https://smashingmagazine.com",
            "https://dev.to",
            "https://hashnode.dev"
        ]
    },
    
    # Hacker News 설정
    "HN_CONFIG": {
        "enabled": True,
        "keywords": [
            "webdev", "css", "html5", "Frontend",
            "web accessibility", "web performance", "html", "scss",
            "web development", "web design", "css-tricks", "css-frameworks",
            "css animation", "iOS issue", "iOS mobile issue"
        ],
        "min_score": 50,
        "story_limit": 30
    },
    
    # GitHub 설정
    "GITHUB_CONFIG": {
        "enabled": True,
        "languages": ["CSS", "HTML", "JavaScript", "TypeScript"],
        "topics": ["webdev", "css", "html5", "Frontend",
            "web accessibility", "web performance", "html", "scss",
            "web development", "web design", "css-tricks", "css-frameworks",
            "css animation", "iOS issue", "iOS mobile issue"],
        "time_range": "weekly"
    },
    

    # AI 설정
    "AI_CONFIG": {
        "enabled": True,
        
        # Gemini (1순위)
        "gemini": {
            "enabled": True,
            "api_key": os.getenv("MAIN_AGENT_GEMINI_KEY"),
            "model": "gemini-2.5-flash",
            "daily_limit": 1500,
            "features": ["summarize", "analyze", "translate", "predict"]
        },
        
        # Claude (2순위)
        "claude": {
            "enabled": bool(os.getenv("ANTHROPIC_API_KEY")),
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
            "model": "claude-3-haiku-20240307",
            "monthly_limit": 1000,
            "features": ["deep_analysis", "complex_reasoning"]
        },
        
        # Hugging Face (3순위 - 폴백)
        "huggingface": {
            "enabled": True,
            "use_local": True,
            "models": {
                "summarization": "sshleifer/distilbart-cnn-12-6",
                "classification": "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli",
                "sentiment": "cardiffnlp/twitter-roberta-base-sentiment-latest"
            }
        },
        
        # 우선순위
        "priority": ["gemini", "claude", "huggingface"],
        
        # 사용량 관리
        "usage_management": {
            "track_usage": True,
            "auto_fallback": True,
            "save_stats": True
        }
    },
    
    # 콘텐츠 필터링 키워드
    "FILTER_KEYWORDS": {
        "must_have_any": [
            # AI 관련
            "AI", "LLM",
            
            # 웹개발 관련
            "webdev", "css", "html5", "Frontend",
            "web accessibility", "web performance", "html", "scss",
            "web development", "web design", "css-tricks", "css-frameworks",
            "css animation", "iOS issue", "iOS mobile issue"
            
            # 트렌드
            "trend"
        ],
        "exclude": ["spam", "advertisement", "promoted", "sponsored"]
    },
    
    # 리포트 설정
    "REPORT_CONFIG": {
        "formats": ["html", "markdown", "json"],
        "include_summary": True,
        "include_charts": True,
        "translate_to_korean": True,
        "max_items_per_source": 15,
        "categorize_by_topic": True
    }
}