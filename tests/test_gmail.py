import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# .env 파일 로드
load_dotenv()

def test_gmail():
    """Gmail 앱 비밀번호 테스트"""
    print("=" * 50)
    print("📧 Gmail 설정 테스트 시작...")
    print("=" * 50)
    
    # 환경변수에서 가져오기
    sender_email = os.getenv("MAIN_AGENT_EMAIL")
    sender_password = os.getenv("MAIN_AGENT_PASSWORD")
    receiver_email = os.getenv("RECEIVER_EMAIL")
    
    # 설정 확인
    print(f"✓ 발신 이메일: {sender_email}")
    print(f"✓ 비밀번호 길이: {len(sender_password) if sender_password else 0}자")
    print(f"✓ 수신 이메일: {receiver_email}")
    
    if not all([sender_email, sender_password, receiver_email]):
        print("\n❌ 오류: .env 파일에 이메일 정보를 입력하세요!")
        print("\n필요한 환경변수:")
        print("  MAIN_AGENT_EMAIL=your_email@gmail.com")
        print("  MAIN_AGENT_PASSWORD=your_16_char_app_password")
        print("  RECEIVER_EMAIL=receiver@gmail.com")
        return False
    
    # 테스트 이메일 생성
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "🎉 테스트 성공! - WebDev Trends Agent"
    
    body = """
    <html>
      <body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 30px; border-radius: 10px;">
          <h1>✅ Gmail 설정 테스트 성공!</h1>
          <p>앱 비밀번호가 올바르게 설정되었습니다.</p>
        </div>
        
        <div style="margin-top: 20px; padding: 20px; background: #f8f9fa; border-radius: 10px;">
          <h2>🎯 다음 단계:</h2>
          <ol>
            <li>3개의 추가 Gmail 계정 생성 (서브 에이전트용)</li>
            <li>각 계정마다 앱 비밀번호 설정</li>
            <li>Gemini API 키 4개 발급</li>
            <li>Reddit API 설정</li>
          </ol>
        </div>
        
        <p style="text-align: center; color: #666; margin-top: 30px;">
          이제 매주 월요일 오전 10시에 트렌드 리포트를 받을 수 있습니다! 🚀
        </p>
      </body>
    </html>
    """
    msg.attach(MIMEText(body, 'html'))
    
    # 이메일 전송
    try:
        print("\n📤 이메일 전송 중...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        print("✅ 이메일 전송 성공! 받은편지함을 확인하세요.")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ 인증 실패!")
        print("   확인사항:")
        print("   1. 앱 비밀번호가 맞는지 확인 (일반 비밀번호 X)")
        print("   2. 2단계 인증이 활성화되어 있는지 확인")
        print("   3. 앱 비밀번호를 다시 생성해보세요")
        return False
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

if __name__ == "__main__":
    test_gmail()