import asyncio
from datetime import datetime

from configs.config import CONFIG
from scrapper.multi_agent_system import NewMultiAgentOrchestrator
from scrapper.utils.logger import logger

class WebDevTrendsAgent:
    """웹개발 & AI 트렌드 수집 메인 에이전트"""
    
    def __init__(self):
        self.config = CONFIG
        self.orchestrator = NewMultiAgentOrchestrator(self.config)
        
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

    def interactive_mode(self):
        """사용자와 상호작용하며 메뉴를 제공합니다."""
        while True:
            print("\n" + "="*60)
            print("🎨 FE 트렌드 & 코드 개선 멀티 에이전트 v4.0 (개선판)")
            print("="*60)
            print("\n메뉴를 선택하세요:")
            print("1. 🚀 지금 바로 전체 시스템 실행")
            print("2. 🚪 종료")
            print("-"*60)
            
            choice = input("선택 (1-2): ").strip()
            
            if choice == "1":
                asyncio.run(self.run_analysis())
            elif choice == "2":
                logger.info("👋 프로그램을 종료합니다.")
                break
            else:
                print("\n⚠️ 잘못된 선택입니다. 다시 시도해주세요.")

def main():
    """메인 함수 (진입점)"""
    agent = WebDevTrendsAgent()
    agent.interactive_mode()