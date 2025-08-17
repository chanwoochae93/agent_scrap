import schedule
import time
import asyncio
from datetime import datetime
import pytz
import threading
import os
import signal
import sys

class SchedulerManager:
    """스케줄링 관리자"""
    
    def __init__(self, config, agent):
        self.config = config
        self.agent = agent
        self.scheduler_thread = None
        self.running = False
        
    def setup_schedule(self):
        """스케줄 설정"""
        
        schedule_config = self.config["SCHEDULE"]
        
        # 한국 시간대 설정
        kst = pytz.timezone(schedule_config["timezone"])
        
        if schedule_config["type"] == "weekly":
            # 매주 특정 요일
            day = schedule_config["day"].lower()
            time = schedule_config["time"]
            
            if day == "monday":
                schedule.every().monday.at(time).do(self._run_job)
            elif day == "tuesday":
                schedule.every().tuesday.at(time).do(self._run_job)
            elif day == "wednesday":
                schedule.every().wednesday.at(time).do(self._run_job)
            elif day == "thursday":
                schedule.every().thursday.at(time).do(self._run_job)
            elif day == "friday":
                schedule.every().friday.at(time).do(self._run_job)
            elif day == "saturday":
                schedule.every().saturday.at(time).do(self._run_job)
            elif day == "sunday":
                schedule.every().sunday.at(time).do(self._run_job)
            
            print(f"📅 스케줄 설정: 매주 {day} {time} (KST)")
            
        elif schedule_config["type"] == "daily":
            # 매일
            time = schedule_config["time"]
            schedule.every().day.at(time).do(self._run_job)
            print(f"📅 스케줄 설정: 매일 {time} (KST)")
            
        elif schedule_config["type"] == "hourly":
            # 매시간
            schedule.every().hour.do(self._run_job)
            print("📅 스케줄 설정: 매시간")
        
        # 다음 실행 시간 출력
        self._print_next_run()
    
    def _run_job(self):
        """작업 실행"""
        
        print("\n" + "="*60)
        print(f"⏰ 스케줄된 작업 실행")
        print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # 비동기 작업 실행
        asyncio.run(self.agent.run_collection())
        
        # 다음 실행 시간 출력
        self._print_next_run()
    
    def _print_next_run(self):
        """다음 실행 시간 출력"""
        
        next_run = schedule.next_run()
        if next_run:
            print(f"⏰ 다음 실행: {next_run}")
    
    def start(self):
        """스케줄러 시작 (백그라운드)"""
        
        if self.running:
            print("⚠️ 스케줄러가 이미 실행 중입니다.")
            return
        
        self.running = True
        self.setup_schedule()
        
        # 백그라운드 스레드에서 실행
        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        print("✅ 스케줄러가 백그라운드에서 실행 중입니다.")
    
    def _run_scheduler(self):
        """스케줄러 실행 루프"""
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # 1분마다 체크
                
            except Exception as e:
                print(f"⚠️ 스케줄러 오류: {e}")
                time.sleep(60)
    
    def stop(self):
        """스케줄러 중지"""
        
        self.running = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        schedule.clear()
        print("✅ 스케줄러가 중지되었습니다.")
    
    def status(self):
        """스케줄러 상태"""
        
        if self.running:
            jobs = schedule.get_jobs()
            
            print("\n📊 스케줄러 상태")
            print("="*40)
            print(f"상태: 🟢 실행 중")
            print(f"작업 수: {len(jobs)}")
            
            if jobs:
                print(f"다음 실행: {schedule.next_run()}")
            
            print("="*40)
        else:
            print("\n📊 스케줄러 상태: 🔴 중지됨")
    
    def run_once(self):
        """한 번만 실행"""
        
        print("🚀 단일 실행 모드")
        asyncio.run(self.agent.run_collection())


class DaemonScheduler:
    """데몬 모드 스케줄러 (Linux/Mac)"""
    
    def __init__(self, config, agent):
        self.config = config
        self.agent = agent
        self.manager = SchedulerManager(config, agent)
        
    def start_daemon(self):
        """데몬 모드로 시작"""
        
        # PID 파일 생성
        pid_file = "scheduler.pid"
        
        # 이미 실행 중인지 확인
        if os.path.exists(pid_file):
            print("⚠️ 스케줄러가 이미 실행 중입니다.")
            with open(pid_file, "r") as f:
                pid = f.read()
            print(f"   PID: {pid}")
            return
        
        # 시그널 핸들러 설정
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # PID 저장
        with open(pid_file, "w") as f:
            f.write(str(os.getpid()))
        
        print(f"🚀 데몬 모드 시작 (PID: {os.getpid()})")
        
        # 스케줄러 시작
        self.manager.setup_schedule()
        
        # 메인 루프
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
                
        except KeyboardInterrupt:
            print("\n👋 스케줄러 종료")
        finally:
            # PID 파일 삭제
            if os.path.exists(pid_file):
                os.remove(pid_file)
    
    def _signal_handler(self, signum, frame):
        """시그널 핸들러"""
        
        print(f"\n📡 시그널 {signum} 받음. 종료합니다.")
        
        # PID 파일 삭제
        pid_file = "scheduler.pid"
        if os.path.exists(pid_file):
            os.remove(pid_file)
        
        sys.exit(0)
    
    def stop_daemon(self):
        """데몬 중지"""
        
        pid_file = "scheduler.pid"
        
        if not os.path.exists(pid_file):
            print("⚠️ 실행 중인 스케줄러가 없습니다.")
            return
        
        with open(pid_file, "r") as f:
            pid = int(f.read())
        
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"✅ 스케줄러 중지 (PID: {pid})")
            
        except ProcessLookupError:
            print("⚠️ 프로세스를 찾을 수 없습니다.")
            os.remove(pid_file)
            
        except Exception as e:
            print(f"❌ 중지 실패: {e}")