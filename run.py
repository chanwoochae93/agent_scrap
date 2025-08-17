import sys
import os
import asyncio
from datetime import datetime

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_banner():
    """배너 출력"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║     🚀 웹개발 & AI 트렌드 멀티 에이전트 시스템 v2.0         ║
    ║                                                              ║
    ║     최신 웹개발과 AI 소식을 4개의 AI 에이전트가             ║
    ║     협력하여 분석하고 매주 월요일 10시에 전송합니다!        ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

def main():
    """메인 함수"""
    print_banner()
    
    from scrapper.main import WebDevTrendsAgent
    
    # 인터랙티브 모드 실행
    agent = WebDevTrendsAgent()
    agent.interactive_mode()

if __name__ == "__main__":
    main()