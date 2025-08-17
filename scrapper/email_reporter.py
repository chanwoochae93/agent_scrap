# scrapper/email_reporter.py

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import Dict, Any

class EmailReporter:
    """이메일 리포트 생성 및 전송"""
    
    def __init__(self, config):
        self.config = config
        self.email_config = config["EMAIL_CONFIG"]
        
    def send_custom_html(self, html_content: str, subject: str) -> bool:
        """커스텀 HTML 이메일 전송"""
        
        try:
            if not self.email_config["enabled"]:
                print("📧 이메일 전송이 비활성화되어 있습니다.")
                return False

            sender_email = self.email_config["sender_email"]
            sender_password = self.email_config["sender_password"]
            receiver_email = self.email_config["receiver_email"]

            if not all([sender_email, sender_password, receiver_email]):
                print("⚠️ 이메일 설정이 완료되지 않았습니다.")
                return False

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = sender_email
            msg["To"] = receiver_email
            
            html_part = MIMEText(html_content, "html", "utf-8")
            msg.attach(html_part)
            
            with smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"]) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"❌ 이메일 전송 실패: {e}")
            return False