import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    # --- 기본 설정 ---
    "APP_NAME": "WebDev AI Trends Multi-Agent",
    "TIMEZONE": "Asia/Seoul",
    "OUTPUT_DIR": "outputs",
    
    # --- 이메일 설정 ---
    "EMAIL_CONFIG": {
        "enabled": True,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "sender_email": os.getenv("MAIN_AGENT_EMAIL"),
        "sender_password": os.getenv("MAIN_AGENT_PASSWORD"),
        "receiver_email": os.getenv("RECEIVER_EMAIL"),
        "subject_template": "🚀 주간 FE 트렌드 리포트: {date}"
    },
    
    # --- 스케줄 설정 ---
    "SCHEDULE": {
        "type": "weekly",
        "day": "monday",
        "time": "10:00",
        "timezone": "Asia/Seoul"
    },
    
    # --- 데이터 수집 소스 ---
    "RSS_FEEDS": [
        "https://www.smashingmagazine.com/feed/",
        "https://developer.mozilla.org/en-US/blog/rss.xml",
        "https://web.dev/feed.xml",
        "https://ishadeed.com/feed.xml",
        "https://www.joshwcomeau.com/rss.xml/",
        "https://dev.to/feed",
        "https://openai.com/blog/rss.xml",
    ],
    
    "REDDIT_CONFIG": {
        "enabled": True,
        "client_id": os.getenv("REDDIT_CLIENT_ID"),
        "client_secret": os.getenv("REDDIT_CLIENT_SECRET"),
        "user_agent": "WebDevTrendsAgent/2.0",
        "subreddits": [
            "webdev", "css", "html5", "Frontend", "javascript", "reactjs", "vuejs",
            "artificial", "singularity", "LocalLLaMA", "MachineLearning"
        ],
        "post_limit": 15,
        "time_filter": "week"
    },
    
    # --- AI 에이전트 API 키 ---
    "API_KEYS": {
        "collector": os.getenv("COLLECTOR_AGENT_GEMINI_KEY"),
        "analyzer": os.getenv("ANALYZER_AGENT_GEMINI_KEY"),
        "emailer": os.getenv("EMAILER_AGENT_GEMINI_KEY"),
        "code_reviewer": os.getenv("CODE_REVIEWER_AGENT_GEMINI_KEY"),
    },
    
    # --- 콘텐츠 필터링 키워드 ---
    "FILTER_KEYWORDS": {
        "must_have_any": [
            "a11y",
            "ai",
            "ai agent",
            "ai tool",
            "ai 기반 디자인",
            "artificial intelligence",
            "auto in css",
            "baseline css properties",
            "code generation",
            "core web vitals",
            "css",
            "css baseline",
            "cursor ide",
            "devin",
            "fine-tuning",
            "frontend",
            "gemini",
            "generative ui",
            "github copilot",
            "gpt-4",
            "gpt-5",
            "html",
            "intl api",
            "javascript",
            "json module",
            "largest contentful paint",
            "lazy loading",
            "lcp",
            "lcp 최적화",
            "llama",
            "llm",
            "next.js",
            "prompt engineering",
            "rag",
            "react",
            "shadow dom",
            "svelte",
            "tailwind",
            "transformer",
            "typescript",
            "v0.dev",
            "vue",
            "web accessibility",
            "web components",
            "web performance",
            "webp",
            "웹 성능 최적화",
        ],
        "exclude": [
            "spam", "advertisement", "promoted", "sponsored", "job", "hiring", 
            "crypto", "blockchain",
        ]
    },
    
    # --- 리포트 설정 ---
    "REPORT_CONFIG": {
        "max_items_per_source": 15,
    }
}