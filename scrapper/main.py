import asyncio
import schedule
import time
from datetime import datetime

from configs.config import CONFIG
from scrapper.multi_agent_system import NewMultiAgentOrchestrator
from scrapper.ai_quota_manager import AIQuotaManager
from scrapper.utils.logger import logger

class WebDevTrendsAgent:
    """웹개발 & AI 트렌드 수집 메인 에이전트"""
    
    def __init__(self):
        self.config = CONFIG
        self.orchestrator = NewMultiAgentOrchestrator(self.config)
        self.quota_manager = AIQuotaManager(self.config)
        
    async def run_analysis(self):
        """데이터 분석 및 리포팅을 실행합니다."""
        logger.info("="*60)
        logger.info("🚀 최신 FE 트렌드 분석 및 코드 리뷰 시작")
        logger.info(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*60)
        
        try:
            await self.orchestrator.run_weekly_analysis()
            logger.info("="*60)
            logger.info("✅ 모든 에이전트 작업 완료!")
            logger.info("="*60)
            return True
        except Exception as e:
            logger.critical(f"❌ 메인 에이전트 실행 중 심각한 오류 발생: {e}", exc_info=True)
            return False

    def setup_schedule(self):
        """설정에 따라 작업을 스케줄링합니다."""
        schedule_config = self.config["SCHEDULE"]
        job = lambda: asyncio.run(self.run_analysis())

        day = schedule_config.get("day", "monday").lower()
        time_str = schedule_config.get("time", "10:00")
        
        schedule_method = getattr(schedule.every(), day, schedule.every().monday)
        schedule_method.at(time_str).do(job)
        
        logger.info(f"📅 스케줄 설정 완료: 매주 {day.capitalize()} {time_str}")

    def run_scheduler(self):
        """스케줄러를 시작하고 대기합니다."""
        self.setup_schedule()
        logger.info("⏳ 스케줄러가 실행 중입니다. Ctrl+C로 종료할 수 있습니다.")
        logger.info(f"   다음 실행 예정: {schedule.next_run()}")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except KeyboardInterrupt:
                logger.info("\n👋 스케줄러를 종료합니다.")
                break

    async def check_quotas(self):
        """API 서비스들의 현재 사용량 한도를 확인하고 출력합니다."""
        await self.quota_manager.check_all_quotas()
        summary = self.quota_manager.get_quota_summary()
        print("\n" + summary)
        input("\n계속하려면 엔터를 누르세요...")

    def interactive_mode(self):
        """사용자와 상호작용하며 메뉴를 제공합니다."""
        while True:
            print("\n" + "="*60)
            print("🎨 FE 트렌드 & 코드 개선 멀티 에이전트 v4.1 (Full)")
            print("="*60)
            print("\n메뉴를 선택하세요:")
            print("1. 🚀 지금 바로 전체 시스템 실행")
            # 따옴표와 괄호를 올바르게 닫아주었습니다.
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
                logger.info("👋 프로그램을 종료합니다.")
                break
            else:
                print("\n⚠️ 잘못된 선택입니다. 다시 시도해주세요.")

def main():
    """메인 함수 (진입점)"""
    agent = WebDevTrendsAgent()
    agent.interactive_mode()