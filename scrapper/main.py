import asyncio
import schedule
import time
import argparse
from datetime import datetime
import pytz
import sys
import os
from typing import Dict, Any

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from configs.multi_agent_config import MULTI_AGENT_CONFIG
from scrapper.multi_agent_system import MultiAgentOrchestrator
from scrapper.ai_quota_manager import AIQuotaManager
from scrapper.email_reporter import EmailReporter

class WebDevTrendsAgent:
    """웹개발 & AI 트렌드 수집 메인 에이전트"""
    
    def __init__(self, use_multi_agent=True):
        self.config = MULTI_AGENT_CONFIG
        self.use_multi_agent = use_multi_agent
        
        # 멀티 에이전트 시스템
        if use_multi_agent:
            self.orchestrator = MultiAgentOrchestrator(self.config)
        
        # AI 한도 관리
        self.quota_manager = AIQuotaManager(self.config)
        
        # 이메일 리포터
        self.email_reporter = EmailReporter(self.config)
        
    async def run_collection(self):
        """데이터 수집 및 분석 실행"""
        
        print("\n" + "="*60)
        print(f"🚀 데이터 수집 및 분석 시작")
        print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")
        
        try:
            # 1. AI 한도 체크
            print("📊 AI API 한도 체크...")
            quotas = await self.quota_manager.check_all_quotas()
            print(self.quota_manager.get_quota_summary())
            
            # 2. 멀티 에이전트 실행
            if self.use_multi_agent:
                print("\n🎭 멀티 에이전트 시스템 시작...")
                final_report = await self.orchestrator.run_weekly_analysis()
            else:
                # 단일 에이전트 모드 (폴백)
                print("\n🤖 단일 에이전트 모드...")
                from scrapper.collectors import DataCollector
                from scrapper.ai_agent_advanced import SmartAIAgent
                
                collector = DataCollector(self.config)
                ai_agent = SmartAIAgent(self.config)
                
                data = await collector.collect_all()
                insights = await ai_agent.generate_weekly_insights(data)
                
                final_report = {
                    "data": data,
                    "insights": insights
                }
            
            # 3. 최종 리포트 저장
            self.save_report(final_report)
            
            # 4. 이메일 발송
            if self.config["EMAIL_CONFIG"]["enabled"]:
                print("\n📧 이메일 발송 중...")
                self.email_reporter.send_email(final_report)
            
            print("\n" + "="*60)
            print("✅ 모든 작업 완료!")
            print("="*60 + "\n")
            
            return True
            
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            
            # 오류 알림 이메일
            self.send_error_notification(str(e))
            return False
    
    def save_report(self, report: Dict[str, Any]):
        """리포트 로컬 저장"""
        import json
        
        os.makedirs("outputs", exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"outputs/report_{timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"📁 리포트 저장: {filename}")
    
    def send_error_notification(self, error_msg: str):
        """오류 알림 이메일"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            
            msg = MIMEText(f"오류 발생:\n\n{error_msg}")
            msg["Subject"] = "⚠️ 웹개발 트렌드 에이전트 오류"
            msg["From"] = self.config["EMAIL_CONFIG"]["sender_email"]
            msg["To"] = self.config["EMAIL_CONFIG"]["receiver_email"]
            
            with smtplib.SMTP(
                self.config["EMAIL_CONFIG"]["smtp_server"],
                self.config["EMAIL_CONFIG"]["smtp_port"]
            ) as server:
                server.starttls()
                server.login(
                    self.config["EMAIL_CONFIG"]["sender_email"],
                    self.config["EMAIL_CONFIG"]["sender_password"]
                )
                server.send_message(msg)
                
        except Exception as e:
            print(f"오류 알림 실패: {e}")
    
    def setup_schedule(self):
        """스케줄 설정"""
        schedule_config = self.config["SCHEDULE"]
        
        if schedule_config["type"] == "weekly":
            # 매주 월요일 오전 10시
            schedule.every().monday.at(schedule_config["time"]).do(
                lambda: asyncio.run(self.run_collection())
            )
            print(f"📅 스케줄 설정: 매주 {schedule_config['day']} {schedule_config['time']} (KST)")
            
        elif schedule_config["type"] == "daily":
            # 매일 지정된 시간
            schedule.every().day.at(schedule_config["time"]).do(
                lambda: asyncio.run(self.run_collection())
            )
            print(f"📅 스케줄 설정: 매일 {schedule_config['time']} (KST)")
    
    def run_scheduler(self):
        """스케줄러 실행"""
        self.setup_schedule()
        
        print("⏳ 스케줄러가 실행 중입니다. Ctrl+C로 종료할 수 있습니다.")
        print(f"   다음 실행: {schedule.next_run()}")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # 1분마다 체크
                
            except KeyboardInterrupt:
                print("\n👋 스케줄러를 종료합니다.")
                break
                
            except Exception as e:
                print(f"⚠️ 스케줄러 오류: {e}")
                time.sleep(60)
    
    def interactive_mode(self):
        """대화형 모드"""
        
        while True:
            print("\n" + "="*60)
            print("🎨 웹개발 & AI 트렌드 멀티 에이전트")
            print("="*60)
            print("\n메뉴를 선택하세요:")
            print("1. 🚀 지금 바로 데이터 수집 및 분석 (멀티 에이전트)")
            print("2. ⏰ 스케줄러 시작 (매주 월요일 오전 10시)")
            print("3. 🧪 테스트 모드 (이메일 전송 없이)")
            print("4. 📊 AI API 한도 확인")
            print("5. 🔧 설정 확인")
            print("6. 📚 사용 가이드")
            print("7. 🚪 종료")
            print("-"*60)
            
            choice = input("선택 (1-7): ").strip()
            
            if choice == "1":
                print("\n🚀 멀티 에이전트 시스템을 시작합니다...")
                asyncio.run(self.run_collection())
                
            elif choice == "2":
                print("\n⏰ 스케줄러를 시작합니다...")
                self.run_scheduler()
                
            elif choice == "3":
                print("\n🧪 테스트 모드로 실행합니다...")
                original_email = self.config["EMAIL_CONFIG"]["enabled"]
                self.config["EMAIL_CONFIG"]["enabled"] = False
                asyncio.run(self.run_collection())
                self.config["EMAIL_CONFIG"]["enabled"] = original_email
                
            elif choice == "4":
                print("\n📊 AI API 한도 확인 중...")
                asyncio.run(self.check_quotas())
                
            elif choice == "5":
                self.show_config()
                
            elif choice == "6":
                self.show_guide()
                
            elif choice == "7":
                print("\n👋 프로그램을 종료합니다.")
                break
                
            else:
                print("\n⚠️ 잘못된 선택입니다. 다시 시도해주세요.")
    
    async def check_quotas(self):
        """API 한도 확인"""
        quotas = await self.quota_manager.check_all_quotas()
        print(self.quota_manager.get_quota_summary())
        input("\n엔터를 눌러 계속...")
    
    def show_config(self):
        """설정 확인"""
        print("\n📋 현재 설정:")
        print(f"  - 멀티 에이전트: {'활성화' if self.use_multi_agent else '비활성화'}")
        print(f"  - 메인 에이전트: {self.config.get('MAIN_AGENT_EMAIL', 'N/A')}")
        print(f"  - 서브 에이전트 A: {self.config.get('AGENT_A_EMAIL', 'N/A')}")
        print(f"  - 서브 에이전트 B: {self.config.get('AGENT_B_EMAIL', 'N/A')}")
        print(f"  - 서브 에이전트 C: {self.config.get('AGENT_C_EMAIL', 'N/A')}")
        print(f"  - 수신 이메일: {self.config['EMAIL_CONFIG']['receiver_email']}")
        print(f"  - 스케줄: {self.config['SCHEDULE']['type']} - {self.config['SCHEDULE']['time']}")
        print(f"  - RSS 피드: {len(self.config['RSS_FEEDS'])}개")
        print(f"  - Reddit 서브레딧: {len(self.config['REDDIT_CONFIG']['subreddits'])}개")
        input("\n엔터를 눌러 계속...")
    
    def show_guide(self):
        """사용 가이드"""
        print("""
        📚 사용 가이드
        ═══════════════════════════════════════════════
        
        🎯 시스템 구조:
        • 4개의 AI 에이전트가 협력하여 분석
        • 서브 에이전트 3개: 전문 분야별 수집
        • 메인 에이전트 1개: 종합 분석
        
        🔄 작동 방식:
        1. 서브 에이전트들이 병렬로 데이터 수집
        2. 각자 Gemini AI로 1차 분석
        3. Gmail로 메인 에이전트에게 전송
        4. 메인 에이전트가 종합 분석
        5. 최종 리포트 생성 및 이메일 발송
        
        ⚙️ API 한도:
        • Gemini: 1500회/일 × 4 = 6000회/일
        • Claude: $5 크레딧 (백업용)
        • Hugging Face: 무제한 (폴백용)
        
        📧 이메일 설정:
        • Gmail 앱 비밀번호 필요 (일반 비밀번호 X)
        • 2단계 인증 활성화 필수
        
        🚀 추천 사용법:
        • 주 1회 실행 (월요일 오전)
        • 테스트는 옵션 3번 사용
        • API 한도는 주기적으로 확인
        
        ═══════════════════════════════════════════════
        """)
        input("\n엔터를 눌러 계속...")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="웹개발 & AI 트렌드 멀티 에이전트 시스템"
    )
    
    parser.add_argument(
        "--collect",
        action="store_true",
        help="즉시 데이터 수집 및 분석"
    )
    
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="스케줄러 시작"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="테스트 모드 (이메일 전송 없음)"
    )
    
    parser.add_argument(
        "--single-agent",
        action="store_true",
        help="단일 에이전트 모드"
    )
    
    parser.add_argument(
        "--check-quota",
        action="store_true",
        help="API 한도 확인"
    )
    
    args = parser.parse_args()
    
    # 에이전트 생성
    use_multi = not args.single_agent
    agent = WebDevTrendsAgent(use_multi_agent=use_multi)
    
    # 명령 처리
    if args.collect:
        asyncio.run(agent.run_collection())
        
    elif args.schedule:
        agent.run_scheduler()
        
    elif args.test:
        agent.config["EMAIL_CONFIG"]["enabled"] = False
        asyncio.run(agent.run_collection())
        
    elif args.check_quota:
        asyncio.run(agent.check_quotas())
        
    else:
        # 인터랙티브 모드
        agent.interactive_mode()

if __name__ == "__main__":
    main()