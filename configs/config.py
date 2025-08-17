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
        "subject_template": "🚀 주간 웹 퍼블리싱 리포트: 새로운 CSS 속성 & HTML 태그 분석 - {date}"
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
        # CSS & HTML 전문
        "https://css-tricks.com/feed/",
        "https://www.smashingmagazine.com/feed/",
        "https://developer.mozilla.org/en-US/blog/rss.xml",
        "https://web.dev/feed.xml",
        "https://ishadeed.com/feed.xml",
        "https://www.joshwcomeau.com/rss.xml/",

        # 주요 기술 블로그
        "https://vercel.com/blog/rss.xml",
        "https://dev.to/feed",
        
        # --- AI 관련 블로그 추가 ---
        "https://openai.com/blog/rss.xml",
        "https://blogs.nvidia.com/feed/",
        "https://aws.amazon.com/blogs/machine-learning/feed/",
        "https://ai.google/research/blog/rss/",
        "https://huggingface.co/blog/feed.xml"
    ],
    
    # Reddit 설정
    "REDDIT_CONFIG": {
        "enabled": True,
        "client_id": os.getenv("REDDIT_CLIENT_ID"),
        "client_secret": os.getenv("REDDIT_CLIENT_SECRET"),
        "user_agent": "WebDevTrendsAgent/2.0",
        "subreddits": [
            # 웹개발
            "webdev", "css", "html5", "Frontend", "javascript",
            "reactjs", "vuejs",
            # --- AI 관련 서브레딧 추가 ---
            "artificial", "singularity", "LocalLLaMA", "MachineLearning",
            "webdev_ai" # 웹개발 + AI 혼합
        ],
        "post_limit": 15,
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

    "API_KEYS": {
        "collector": os.getenv("COLLECTOR_AGENT_GEMINI_KEY"),
        "analyzer": os.getenv("ANALYZER_AGENT_GEMINI_KEY"),
        "emailer": os.getenv("EMAILER_AGENT_GEMINI_KEY"),
        "code_reviewer": os.getenv("CODE_REVIEWER_AGENT_GEMINI_KEY"),
    },
    
    # 콘텐츠 필터링 키워드
    "FILTER_KEYWORDS": {
        "must_have_any": [
            # --- AI 및 AI 기반 개발 도구 키워드 추가 ---
            "ai",
            # 기존 웹/프론트엔드 키워드
            "html",
            "a11y",
            "ai agent",
            "ai tool",
            "artificial intelligence",
            "claude 3",
            "code generation",
            "core web vitals",
            "css",
            "css base units",
            "css-in-js",
            "cursor ide",
            "design system automation",
            "devin",
            "fine-tuning",
            "frontend",
            "gemini",
            "generative ui",
            "github copilot",
            "gpt-4",
            "gpt-5",
            "intl api",
            "javascript",
            "langchain",
            "llama",
            "llm",
            "next.js",
            "prompt engineering",
            "rag",
            "react",
            "scroll-driven css animations",
            "sora",
            "svelte",
            "tailwind",
            "transformer",
            "typescript",
            "v0.dev",
            "vue",
            "web accessibility",
            "web performance"
        ],
        "exclude": ["spam", "advertisement", "promoted", "sponsored", "job", "hiring", "crypto", "blockchain"]
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