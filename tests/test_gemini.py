import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def test_gemini():
    """Gemini API 테스트"""
    print("=" * 50)
    print("🌟 Gemini API 테스트 시작...")
    print("=" * 50)
    
    api_key = os.getenv("MAIN_AGENT_GEMINI_KEY")
    
    if not api_key:
        print("\n❌ 오류: .env 파일에 MAIN_AGENT_GEMINI_KEY 를 입력하세요!")
        return False
    
    print(f"✓ API Key: {api_key[:10]}...")
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = "웹개발에서 가장 인기 있는 CSS 프레임워크 3개를 알려주세요. 한 줄씩만 간단히."
        response = model.generate_content(prompt)
        
        print("\n📥 Gemini 응답:")
        print("-" * 50)
        print(response.text)
        print("-" * 50)
        print("\n✅ Gemini API 연결 성공!")
        return True
        
    except Exception as e:
        print(f"\n❌ Gemini API 오류: {e}")
        return False

if __name__ == "__main__":
    test_gemini()