import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapper.utils.logger import logger # 로거를 가장 먼저 임포트합니다.

def print_banner():
    """프로그램 시작 배너를 출력합니다."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║     🚀 웹개발 & AI 트렌드 멀티 에이전트 시스템 v4.0 (개선판) ║
    ║                                                              ║
    ║     4개의 AI 에이전트가 협력하여 최신 트렌드를 분석하고,      ║
    ║     스스로 코드를 리뷰하며 개선해나가는 자동화 시스템입니다.  ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    """메인 함수"""
    print_banner()
    logger.info("프로그램 시작.")
    
    # ImportError를 방지하기 위해 main 함수 안에서 import 합니다.
    from scrapper.main import WebDevTrendsAgent
    
    agent = WebDevTrendsAgent()
    agent.interactive_mode()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"프로그램 실행 중 예외 발생: {e}", exc_info=True)