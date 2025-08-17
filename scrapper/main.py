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

from configs.config import CONFIG # 이제 단일 설정을 사용
# 새로 만든 NewMultiAgentOrchestrator를 가져옵니다.
from scrapper.multi_agent_system import NewMultiAgentOrchestrator
from scrapper.ai_quota_manager import AIQuotaManager
from scrapper.email_reporter import EmailReporter

class WebDevTrendsAgent:
    """웹개발 & AI 트렌드 수집 메인 에이전트"""
    
    def __init__(self):
        self.config = CONFIG
        # NewMultiAgentOrchestrator를 사용하도록 교체합니다.
        self.orchestrator = NewMultiAgentOrchestrator(self.config)
        self.quota_manager = AIQuotaManager(self.config)
        
    async def run_analysis(self):
        """데이터 분석 및 리포팅 실행 (이름 변경)"""
        
        print("\n" + "="*60)
        print(f"🚀 최신 FE 트렌드 분석 및 코드 리뷰 시작")
        print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")
        
        try:
            # 오케스트레이터의 메인 플로우를 실행합니다.
            await self.orchestrator.run_weekly_analysis()
            
            print("\n" + "="*60)
            print("✅ 모든 에이전트 작업 완료!")
            print("="*60 + "\n")
            
            return True
            
        except Exception as e:
            print(f"\n❌ 메인 에이전트 오류 발생: {e}")
            # 오류 알림 기능은 오케스트레이터 내부 로직으로 이동 가능 (현재는 유지)
            # self.send_error_notification(str(e))
            return False

    def setup_schedule(self):
        """스케줄 설정"""
        schedule_config = self.config["SCHEDULE"]
        
        job = lambda: asyncio.run(self.run_analysis())

        if schedule_config["type"] == "weekly":
            day = schedule_config["day"].lower()
            time_str = schedule_config["time"]
            
            # schedule 라이브러리에 맞게 요일별로 설정
            schedule_method = getattr(schedule.every(), day)
            schedule_method.at(time_str).do(job)
            
            print(f"📅 스케줄 설정: 매주 {schedule_config['day']} {schedule_config['time']} ({schedule_config['timezone']})")
            
        elif schedule_config["type"] == "daily":
            schedule.every().day.at(schedule_config["time"]).do(job)
            print(f"📅 스케줄 설정: 매일 {schedule_config['time']} ({schedule_config['timezone']})")
    
    def run_scheduler(self):
        """스케줄러 실행"""
        self.setup_schedule()
        
        print("⏳ 스케줄러가 실행 중입니다. Ctrl+C로 종료할 수 있습니다.")
        print(f"   다음 실행: {schedule.next_run()}")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
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
            print("🎨 FE 트렌드 & 코드 개선 멀티 에이전트 v3.0")
            print("="*60)
            print("\n메뉴를 선택하세요:")
            print("1. 🚀 지금 바로 전체 시스템 실행")
            print("2. ⏰ 스케줄러 시작 (매주 월요일 오전 10시)")
            print("3. 📊 AI API 한도 확인")
            print("4. 🚪 종료")
            print("-"*60)
            
            choice = input("선택 (1-4): ").strip()
            
            if choice == "1":
                asyncio.run(self.run_analysis())
            elif choice == "2":
                self.run_scheduler()
            elif choice == "3":
                asyncio.run(self.check_quotas())
            elif choice == "4":
                print("\n👋 프로그램을 종료합니다.")
                break
            else:
                print("\n⚠️ 잘못된 선택입니다. 다시 시도해주세요.")
    
    async def check_quotas(self):
        """API 한도 확인"""
        await self.quota_manager.check_all_quotas()
        print(self.quota_manager.get_quota_summary())
        input("\n엔터를 눌러 계속...")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="FE 트렌드 & 코드 개선 멀지 에이전트 시스템")
    
    parser.add_argument("--run", action="store_true", help="즉시 전체 시스템 실행")
    parser.add_argument("--schedule", action="store_true", help="스케줄러 시작")
    parser.add_argument("--check-quota", action="store_true", help="API 한도 확인")
    
    args = parser.parse_args()
    
    agent = WebDevTrendsAgent()
    
    if args.run:
        asyncio.run(agent.run_analysis())
    elif args.schedule:
        agent.run_scheduler()
    elif args.check_quota:
        asyncio.run(agent.check_quotas())
    else:
        agent.interactive_mode()

if __name__ == "__main__":
    main()