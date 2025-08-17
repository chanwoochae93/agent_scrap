import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_gmail import test_gmail
from tests.test_reddit import test_reddit
from tests.test_gemini import test_gemini
from dotenv import load_dotenv

load_dotenv()

def check_env_variables():
    """환경변수 체크"""
    print("=" * 50)
    print("🔍 환경변수 체크")
    print("=" * 50)
    
    required_vars = [
        "MAIN_AGENT_EMAIL",
        "MAIN_AGENT_PASSWORD",
        "RECEIVER_EMAIL",
        "ANALYZER_AGENT_GEMINI_KEY",
        "COLLECTOR_AGENT_GEMINI_KEY",
        "EMAILER_AGENT_GEMINI_KEY",
        "CODE_REVIEWER_AGENT_GEMINI_KEY",
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET"
    ]
    
    missing = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if "PASSWORD" in var or "SECRET" in var or "KEY" in var:
                print(f"  ✅ {var}: {'*' * 10}")
            else:
                print(f"  ✅ {var}: {value[:30]}...")
        else:
            print(f"  ❌ {var}: 설정 안 됨")
            missing.append(var)
    
    if missing:
        assert False, f".env 파일에 누락된 환경변수가 있습니다: {', '.join(missing)}"

def test_all():
    """모든 API 설정을 테스트합니다."""
    print("\n" + "🚀 " * 20)
    print("FE Trends Agent - 전체 시스템 테스트")
    print("🚀 " * 20 + "\n")
    
    print("\n[1/4] 환경변수 체크")
    check_env_variables()
    
    print("\n[2/4] Gmail 테스트")
    test_gmail()
    
    print("\n[3/4] Reddit 테스트")
    test_reddit()
    
    print("\n[4/4] Gemini 테스트")
    test_gemini()
    
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    print("🎉 축하합니다! 모든 테스트가 성공적으로 완료되었습니다.")
    print("   실행 명령: python run.py")