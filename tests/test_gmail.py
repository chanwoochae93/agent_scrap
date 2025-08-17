import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

def test_gmail():
    """Gmail 앱 비밀번호 설정을 테스트합니다."""
    print("=" * 50)
    print("📧 Gmail 설정 테스트 시작...")
    print("=" * 50)
    
    sender_email = os.getenv("MAIN_AGENT_EMAIL")
    sender_password = os.getenv("MAIN_AGENT_PASSWORD")
    receiver_email = os.getenv("RECEIVER_EMAIL")
    
    print(f"✓ 발신 이메일: {sender_email}")
    
    if not all([sender_email, sender_password, receiver_email]):
        assert False, ".env 파일에 이메일 정보(MAIN_AGENT_EMAIL, MAIN_AGENT_PASSWORD, RECEIVER_EMAIL)를 모두 입력하세요!"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "🎉 테스트 성공! - WebDev Trends Agent"
    body = "<html><body><h1>✅ Gmail 설정 테스트 성공!</h1><p>앱 비밀번호가 올바르게 설정되었습니다.</p></body></html>"
    msg.attach(MIMEText(body, 'html'))
    
    try:
        print("\n📤 이메일 전송 중...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print("✅ 이메일 전송 성공! 받은편지함을 확인하세요.")
        
    except smtplib.SMTPAuthenticationError:
        assert False, "인증 실패: 앱 비밀번호가 정확한지, 2단계 인증이 활성화되었는지 확인하세요."
        
    except Exception as e:
        assert False, f"이메일 전송 중 오류 발생: {e}"