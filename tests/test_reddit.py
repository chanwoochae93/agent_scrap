import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import praw

# .env 파일 로드
load_dotenv()

def test_reddit():
    """Reddit API 테스트"""
    print("=" * 50)
    print("🔥 Reddit API 테스트 시작...")
    print("=" * 50)
    
    # 환경변수에서 가져오기
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    
    # 설정 확인
    print(f"✓ Client ID: {client_id[:5]}..." if client_id else "✗ Client ID 없음")
    print(f"✓ Client Secret: {client_secret[:5]}..." if client_secret else "✗ Secret 없음")
    
    if not all([client_id, client_secret]):
        print("\n❌ 오류: .env 파일에 Reddit API 정보를 입력하세요!")
        print("\n설정 방법:")
        print("  1. https://www.reddit.com/prefs/apps 접속")
        print("  2. 'Create App' 클릭")
        print("  3. Type: 'script' 선택")
        print("  4. Redirect URI: http://localhost:8080")
        print("  5. Client ID와 Secret을 .env에 저장")
        return False
    
    try:
        print("\n🔍 Reddit 연결 중...")
        
        # Reddit 인스턴스 생성
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent="WebDev Trends Test v1.0"
        )
        
        # r/webdev에서 인기 포스트 가져오기
        subreddit = reddit.subreddit("webdev")
        
        print("\n📊 r/webdev 인기 포스트 TOP 3:")
        print("-" * 50)
        
        for i, post in enumerate(subreddit.hot(limit=3), 1):
            print(f"\n{i}. {post.title}")
            print(f"   👍 점수: {post.score}")
            print(f"   💬 댓글: {post.num_comments}")
            print(f"   🔗 링크: https://reddit.com{post.permalink[:50]}...")
        
        print("\n✅ Reddit API 연결 성공!")
        return True
        
    except praw.exceptions.ResponseException as e:
        print(f"❌ Reddit API 오류: {e}")
        print("   확인사항:")
        print("   - Client ID와 Secret이 맞는지 확인")
        print("   - App type이 'script'인지 확인")
        print("   - Redirect URI가 http://localhost:8080 인지 확인")
        return False
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

if __name__ == "__main__":
    test_reddit()