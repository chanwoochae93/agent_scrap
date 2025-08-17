import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_gmail import test_gmail
from tests.test_reddit import test_reddit
from tests.test_gemini import test_gemini
from dotenv import load_dotenv

# .env 파일 로드
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
        "MAIN_AGENT_GEMINI_KEY",
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
    
    return missing

def test_all():
    """모든 API 테스트"""
    print("\n" + "🚀 " * 20)
    print("FE Trends Agent - 전체 시스템 테스트")
    print("🚀 " * 20 + "\n")
    
    results = {
        "환경변수": False,
        "Gmail": False,
        "Reddit": False,
        "Gemini": False
    }
    
    # 1. 환경변수 체크
    print("\n[1/4] 환경변수 체크")
    missing = check_env_variables()
    results["환경변수"] = len(missing) == 0
    
    if missing:
        print(f"\n⚠️ 누락된 환경변수: {', '.join(missing)}")
    
    # 2. Gmail 테스트
    print("\n[2/4] Gmail 테스트")
    if os.getenv("MAIN_AGENT_EMAIL") and os.getenv("MAIN_AGENT_PASSWORD"):
        results["Gmail"] = test_gmail()
    else:
        print("⚠️ Gmail 설정이 없어 건너뜁니다.")
    
    # 3. Reddit 테스트
    print("\n[3/4] Reddit 테스트")
    if os.getenv("REDDIT_CLIENT_ID") and os.getenv("REDDIT_CLIENT_SECRET"):
        results["Reddit"] = test_reddit()
    else:
        print("⚠️ Reddit 설정이 없어 건너뜁니다.")
    
    # 4. Gemini 테스트
    print("\n[4/4] Gemini 테스트")
    if os.getenv("MAIN_AGENT_GEMINI_KEY"):
        results["Gemini"] = test_gemini()
    else:
        print("⚠️ Gemini 설정이 없어 건너뜁니다.")
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    for service, result in results.items():
        status = "✅ 성공" if result else "❌ 실패"
        print(f"{service:15} : {status}")
    
    all_ready = all(results.values())
    
    if all_ready:
        print("\n🎉 축하합니다! 에이전트 시스템을 실행할 준비가 완료되었습니다!")
        print("   실행 명령: python run.py")
    else:
        print("\n❌ 시스템 실행 전 .env 설정을 완료해주세요.")

if __name__ == "__main__":
    test_all()