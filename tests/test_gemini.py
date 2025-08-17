import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import google.generativeai as genai

# .env 파일 로드
load_dotenv()

def test_gemini():
    """Gemini API 테스트"""
    print("=" * 50)
    print("🌟 Gemini API 테스트 시작...")
    print("=" * 50)
    
    # 환경변수에서 가져오기
    api_key = os.getenv("MAIN_AGENT_GEMINI_KEY")
    
    # 설정 확인
    print(f"✓ API Key: {api_key[:10]}..." if api_key else "✗ API Key 없음")
    
    if not api_key:
        print("\n❌ 오류: .env 파일에 Gemini API 키를 입력하세요!")
        print("\n설정 방법:")
        print("  1. https://makersuite.google.com/app/apikey 접속")
        print("  2. 'Create API Key' 클릭")
        print("  3. 생성된 키를 .env에 저장")
        print("     MAIN_AGENT_GEMINI_KEY=your_api_key_here")
        return False
    
    try:
        print("\n🔍 Gemini 연결 중...")
        
        # Gemini 설정
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # 테스트 요청
        prompt = "웹개발에서 가장 인기 있는 CSS 프레임워크 3개를 알려주세요. 한 줄씩만 간단히."
        
        print(f"\n📤 테스트 질문: {prompt}")
        print("\n📥 Gemini 응답:")
        print("-" * 50)
        
        response = model.generate_content(prompt)
        print(response.text)
        
        print("-" * 50)
        print("\n✅ Gemini API 연결 성공!")
        print("   일일 한도: 1,500회 (무료)")
        
        return True
        
    except Exception as e:
        print(f"❌ Gemini API 오류: {e}")
        print("\n확인사항:")
        print("   - API 키가 올바른지 확인")
        print("   - API가 활성화되어 있는지 확인")
        return False

if __name__ == "__main__":
    test_gemini()
