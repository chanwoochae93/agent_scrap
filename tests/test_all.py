import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_gmail import test_gmail
from test_reddit import test_reddit
from test_gemini import test_gemini
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def check_env_variables():
    """환경변수 체크"""
    print("=" * 50)
    print("🔍 환경변수 체크")
    print("=" * 50)
    
    required_vars = {
        "메인 에이전트": [
            "MAIN_AGENT_EMAIL",
            "MAIN_AGENT_PASSWORD",
            "MAIN_AGENT_GEMINI_KEY"
        ],
        "서브 에이전트 A": [
            "AGENT_A_EMAIL",
            "AGENT_A_PASSWORD",
            "AGENT_A_GEMINI_KEY"
        ],
        "서브 에이전트 B": [
            "AGENT_B_EMAIL",
            "AGENT_B_PASSWORD",
            "AGENT_B_GEMINI_KEY"
        ],
        "서브 에이전트 C": [
            "AGENT_C_EMAIL",
            "AGENT_C_PASSWORD",
            "AGENT_C_GEMINI_KEY"
        ],
        "기타": [
            "RECEIVER_EMAIL",
            "REDDIT_CLIENT_ID",
            "REDDIT_CLIENT_SECRET"
        ]
    }
    
    missing = []
    
    for category, vars in required_vars.items():
        print(f"\n{category}:")
        for var in vars:
            value = os.getenv(var)
            if value:
                if "PASSWORD" in var or "SECRET" in var or "KEY" in var:
                    print(f"  ✅ {var}: {'*' * 10}")
                else:
                    print(f"  ✅ {var}: {value[:20]}...")
            else:
                print(f"  ❌ {var}: 설정 안 됨")
                missing.append(var)
    
    return missing

def test_all():
    """모든 API 테스트"""
    print("\n" + "🚀 " * 20)
    print("WebDev Trends Agent - 전체 시스템 테스트")
    print("🚀 " * 20 + "\n")
    
    results = {
        "환경변수": False,
        "Gmail": False,
        "Reddit": False,
        "Gemini": False
    }
    
    # 환경변수 체크
    print("\n[1/4] 환경변수 체크")
    missing = check_env_variables()
    results["환경변수"] = len(missing) == 0
    
    if missing:
        print(f"\n⚠️ 누락된 환경변수: {', '.join(missing)}")
    
    # Gmail 테스트
    print("\n[2/4] Gmail 테스트")
    if os.getenv("MAIN_AGENT_EMAIL") and os.getenv("MAIN_AGENT_PASSWORD"):
        results["Gmail"] = test_gmail()
    else:
        print("⚠️ Gmail 설정이 없어 건너뜁니다.")
    
    # Reddit 테스트
    print("\n[3/4] Reddit 테스트")
    if os.getenv("REDDIT_CLIENT_ID") and os.getenv("REDDIT_CLIENT_SECRET"):
        results["Reddit"] = test_reddit()
    else:
        print("⚠️ Reddit 설정이 없어 건너뜁니다.")
    
    # Gemini 테스트
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
        if result is True:
            status = "✅ 성공"
        elif result is False:
            status = "❌ 실패"
        else:
            status = "⚠️  건너뜀"
        
        print(f"{service:15} : {status}")
    
    # 멀티 에이전트 준비 상태
    print("\n" + "=" * 60)
    print("🎭 멀티 에이전트 시스템 준비 상태")
    print("=" * 60)
    
    agents_ready = {
        "메인": all([
            os.getenv("MAIN_AGENT_EMAIL"),
            os.getenv("MAIN_AGENT_PASSWORD"),
            os.getenv("MAIN_AGENT_GEMINI_KEY")
        ]),
        "서브A": all([
            os.getenv("AGENT_A_EMAIL"),
            os.getenv("AGENT_A_PASSWORD"),
            os.getenv("AGENT_A_GEMINI_KEY")
        ]),
        "서브B": all([
            os.getenv("AGENT_B_EMAIL"),
            os.getenv("AGENT_B_PASSWORD"),
            os.getenv("AGENT_B_GEMINI_KEY")
        ]),
        "서브C": all([
            os.getenv("AGENT_C_EMAIL"),
            os.getenv("AGENT_C_PASSWORD"),
            os.getenv("AGENT_C_GEMINI_KEY")
        ])
    }
    
    for agent, ready in agents_ready.items():
        print(f"{agent} 에이전트: {'✅ 준비됨' if ready else '❌ 설정 필요'}")
    
    # 최종 판정
    all_ready = all(agents_ready.values()) and results["환경변수"]
    
    if all_ready:
        print("\n🎉 축하합니다! 멀티 에이전트 시스템을 실행할 준비가 완료되었습니다!")
        print("실행 명령: python run.py")
    elif agents_ready["메인"]:
        print("\n⚠️ 메인 에이전트만 준비됨. 단일 에이전트 모드로 실행 가능합니다.")
        print("실행 명령: python run.py --single-agent")
    else:
        print("\n❌ 시스템 실행 전 설정을 완료해주세요.")
        print("\n📚 설정 가이드:")
        print("  1. .env 파일에 필요한 API 키 입력")
        print("  2. Gmail 앱 비밀번호 설정 (2단계 인증 필수)")
        print("  3. Gemini API 키 발급 (무료)")
        print("  4. Reddit API 설정 (선택사항)")
    
    return all_ready

if __name__ == "__main__":
    test_all()