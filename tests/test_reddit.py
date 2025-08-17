import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import praw

load_dotenv()

def test_reddit():
    """Reddit API 설정을 테스트합니다."""
    print("=" * 50)
    print("🔥 Reddit API 테스트 시작...")
    print("=" * 50)
    
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    
    if not all([client_id, client_secret]):
        assert False, ".env 파일에 Reddit API 정보(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)를 입력하세요!"
    
    try:
        print("\n🔍 Reddit 연결 중...")
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent="WebDev Trends Test v1.0"
        )
        subreddit = reddit.subreddit("webdev")
        
        print("\n📊 r/webdev 인기 포스트 TOP 1:")
        for post in subreddit.hot(limit=1):
            print(f"  - {post.title}")
        
        print("\n✅ Reddit API 연결 성공!")
        
    except Exception as e:
        assert False, f"Reddit API 테스트 중 오류 발생: {e}"