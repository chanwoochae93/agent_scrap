import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import json
import os
from typing import Dict, Any
from jinja2 import Template

class EmailReporter:
    """이메일 리포트 생성 및 전송"""
    
    def __init__(self, config):
        self.config = config
        self.email_config = config["EMAIL_CONFIG"]
        
    def send_email(self, data: Dict[str, Any]) -> bool:
        """이메일 전송 메인 함수"""
        
        try:
            if not self.email_config["enabled"]:
                print("📧 이메일 전송이 비활성화되어 있습니다.")
                return False
            
            # 이메일 설정
            sender_email = self.email_config["sender_email"]
            sender_password = self.email_config["sender_password"]
            receiver_email = self.email_config["receiver_email"]
            
            if not all([sender_email, sender_password, receiver_email]):
                print("⚠️ 이메일 설정이 완료되지 않았습니다.")
                return False
            
            # 메시지 생성
            msg = MIMEMultipart("alternative")
            msg["Subject"] = self.email_config["subject_template"].format(
                date=datetime.now().strftime("%Y년 %m월 %d일")
            )
            msg["From"] = sender_email
            msg["To"] = receiver_email
            
            # HTML 리포트 생성
            html_content = self.create_html_report(data)
            
            # HTML 파트 추가
            html_part = MIMEText(html_content, "html", "utf-8")
            msg.attach(html_part)
            
            # JSON 첨부파일
            self._attach_json_data(msg, data)
            
            # SMTP 서버 연결 및 전송
            print(f"📧 이메일 전송 중... ({receiver_email})")
            
            with smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"]) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            print("✅ 이메일 전송 완료!")
            return True
            
        except Exception as e:
            print(f"❌ 이메일 전송 실패: {e}")
            return False
    
    def create_html_report(self, data: Dict[str, Any]) -> str:
        """HTML 이메일 리포트 생성"""
        
        # 멀티 에이전트 시스템 결과인지 확인
        is_multi_agent = "synthesis" in data
        
        if is_multi_agent:
            return self._create_multi_agent_html(data)
        else:
            return self._create_single_agent_html(data)
    
    def _create_multi_agent_html(self, data: Dict) -> str:
        """멀티 에이전트 HTML 리포트"""
        
        html_template = """
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>주간 웹개발 & AI 트렌드 리포트</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: 'Noto Sans KR', -apple-system, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 20px;
                }
                .container {
                    max-width: 900px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 20px;
                    overflow: hidden;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                }
                .header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 40px;
                    text-align: center;
                }
                .header h1 {
                    font-size: 2.5em;
                    margin-bottom: 10px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }
                .agents-info {
                    background: rgba(255,255,255,0.1);
                    padding: 15px;
                    border-radius: 10px;
                    margin-top: 20px;
                }
                .agent-badge {
                    display: inline-block;
                    padding: 5px 15px;
                    margin: 5px;
                    border-radius: 20px;
                    font-size: 0.9em;
                    font-weight: 500;
                }
                .agent-a { background: #ffd93d; color: #333; }
                .agent-b { background: #6bcf7f; color: white; }
                .agent-c { background: #4ecdc4; color: white; }
                .agent-main { background: #ff6b6b; color: white; }
                
                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    padding: 30px;
                    background: #f8f9fa;
                }
                .stat-card {
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .stat-card .number {
                    font-size: 2em;
                    font-weight: bold;
                    color: #667eea;
                }
                .stat-card .label {
                    color: #666;
                    margin-top: 5px;
                }
                
                .synthesis {
                    padding: 30px;
                    background: white;
                }
                .synthesis h2 {
                    color: #667eea;
                    margin-bottom: 20px;
                    font-size: 1.8em;
                }
                .synthesis-content {
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 10px;
                    white-space: pre-wrap;
                    font-family: 'Noto Sans KR', sans-serif;
                    line-height: 1.8;
                }
                
                .trend-evolution {
                    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                    padding: 30px;
                    margin: 20px;
                    border-radius: 15px;
                }
                .trend-item {
                    background: white;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                }
                .trend-growing { border-left: 4px solid #6bcf7f; }
                .trend-stable { border-left: 4px solid #ffd93d; }
                .trend-declining { border-left: 4px solid #ff6b6b; }
                
                .footer {
                    background: #f8f9fa;
                    padding: 30px;
                    text-align: center;
                    color: #666;
                }
                .footer a {
                    color: #667eea;
                    text-decoration: none;
                }
                
                @media (max-width: 600px) {
                    .header h1 { font-size: 1.8em; }
                    .stats-grid { grid-template-columns: 1fr 1fr; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 주간 웹개발 & AI 트렌드 리포트</h1>
                    <div class="date">{{ date }}</div>
                    
                    <div class="agents-info">
                        <div class="agent-badge agent-main">👑 메인 에이전트</div>
                        <div class="agent-badge agent-a">🤖 AI/ML 전문</div>
                        <div class="agent-badge agent-b">🎨 Frontend 전문</div>
                        <div class="agent-badge agent-c">⚙️ Backend 전문</div>
                    </div>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="number">{{ sub_agents_count }}</div>
                        <div class="label">참여 에이전트</div>
                    </div>
                    <div class="stat-card">
                        <div class="number">{{ total_items }}</div>
                        <div class="label">수집 아이템</div>
                    </div>
                    <div class="stat-card">
                        <div class="number">{{ unique_items }}</div>
                        <div class="label">고유 아이템</div>
                    </div>
                    <div class="stat-card">
                        <div class="number">{{ dedup_rate }}%</div>
                        <div class="label">중복 제거율</div>
                    </div>
                </div>
                
                {% if trends_evolution %}
                <div class="trend-evolution">
                    <h2>📈 트렌드 진화</h2>
                    {% for trend in trends_evolution %}
                    <div class="trend-item trend-{{ trend.trend }}">
                        <div>
                            <strong>{{ trend.topic }}</strong>
                            <br>
                            <small>언급 {{ trend.frequency }}회 | 첫 발견: {{ trend.first_seen[:10] }}</small>
                        </div>
                        <div>
                            {% if trend.trend == 'growing' %}
                            📈 성장중
                            {% elif trend.trend == 'stable' %}
                            📊 안정적
                            {% else %}
                            📉 하락중
                            {% endif %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
                
                <div class="synthesis">
                    <h2>🎯 AI 종합 분석</h2>
                    <div class="synthesis-content">{{ synthesis }}</div>
                </div>
                
                <div class="footer">
                    <p>이 리포트는 4개의 AI 에이전트가 협력하여 자동 생성했습니다.</p>
                    <p>매주 월요일 오전 10시에 새로운 트렌드를 받아보세요! 🎉</p>
                    <p><a href="mailto:{{ sender_email }}">문의하기</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Jinja2 템플릿 렌더링
        template = Template(html_template)
        
        # 통계 계산
        dedup_stats = data.get("deduplication_stats", {})
        total = dedup_stats.get("total_items", 0)
        unique = dedup_stats.get("unique_items", 0)
        dedup_rate = round((1 - unique/total) * 100) if total > 0 else 0
        
        html = template.render(
            date=datetime.now().strftime("%Y년 %m월 %d일"),
            sub_agents_count=data.get("sub_agents_count", 0),
            total_items=total,
            unique_items=unique,
            dedup_rate=dedup_rate,
            trends_evolution=data.get("context", {}).get("trends_evolution", [])[:5],
            synthesis=data.get("synthesis", "분석 결과 없음"),
            sender_email=self.email_config.get("sender_email", "")
        )
        
        return html
    
    def _create_single_agent_html(self, data: Dict) -> str:
        """단일 에이전트 HTML 리포트"""
        
        html_template = """
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>주간 웹개발 & AI 트렌드 리포트</title>
            <style>
                body {
                    font-family: 'Noto Sans KR', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }
                .header {
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    margin-bottom: 30px;
                }
                .section {
                    background: #f8f9fa;
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 10px;
                }
                .item {
                    background: white;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 5px;
                    border-left: 3px solid #667eea;
                }
                .footer {
                    text-align: center;
                    padding: 20px;
                    color: #666;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 주간 웹개발 & AI 트렌드</h1>
                <p>{{ date }}</p>
            </div>
            
            {% if reddit_data %}
            <div class="section">
                <h2>🔥 Reddit 인기 포스트</h2>
                {% for item in reddit_data[:5] %}
                <div class="item">
                    <strong>{{ item.title }}</strong><br>
                    <small>r/{{ item.subreddit }} | 👍 {{ item.score }} | 💬 {{ item.num_comments }}</small>
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            {% if hackernews_data %}
            <div class="section">
                <h2>🟠 Hacker News</h2>
                {% for item in hackernews_data[:5] %}
                <div class="item">
                    <strong>{{ item.title }}</strong><br>
                    <small>⬆️ {{ item.score }} points | 💬 {{ item.comments }} comments</small>
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            <div class="footer">
                <p>매주 월요일 오전 10시에 만나요! 🎉</p>
            </div>
        </body>
        </html>
        """
        
        template = Template(html_template)
        
        html = template.render(
            date=datetime.now().strftime("%Y년 %m월 %d일"),
            reddit_data=data.get("reddit", []),
            hackernews_data=data.get("hackernews", [])
        )
        
        return html
    
    def _attach_json_data(self, msg: MIMEMultipart, data: Dict):
        """JSON 데이터 첨부"""
        
        json_filename = f"trends_data_{datetime.now().strftime('%Y%m%d')}.json"
        json_data = json.dumps(data, ensure_ascii=False, indent=2, default=str)
        
        attachment = MIMEBase("application", "json")
        attachment.set_payload(json_data.encode("utf-8"))
        encoders.encode_base64(attachment)
        attachment.add_header(
            "Content-Disposition",
            f"attachment; filename={json_filename}"
        )
        msg.attach(attachment)
    
    def save_report_locally(self, data: Dict[str, Any], output_dir: str = "outputs") -> str:
        """리포트를 로컬에 저장"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        
        # HTML 리포트 저장
        html_filename = os.path.join(output_dir, f"report_{timestamp}.html")
        html_content = self.create_html_report(data)
        
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        # JSON 데이터 저장
        json_filename = os.path.join(output_dir, f"data_{timestamp}.json")
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"📁 리포트 저장 완료:")
        print(f"  - HTML: {html_filename}")
        print(f"  - JSON: {json_filename}")
        
        return html_filename
    
    def send_custom_html(self, html_content: str, subject: str) -> bool:
        """커스텀 HTML 이메일 전송"""
        
        try:
            msg = MIMEMultipart()
            msg["Subject"] = subject
            msg["From"] = self.email_config["sender_email"]
            msg["To"] = self.email_config["receiver_email"]
            
            msg.attach(MIMEText(html_content, "html", "utf-8"))
            
            with smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"]) as server:
                server.starttls()
                server.login(
                    self.email_config["sender_email"],
                    self.email_config["sender_password"]
                )
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"❌ 이메일 전송 실패: {e}")
            return False
