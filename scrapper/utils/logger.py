import logging
import os
from logging.handlers import TimedRotatingFileHandler

def setup_logger():
    """프로젝트 전반에 사용할 로거를 설정합니다."""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 로거 이름으로 'WebDevTrendsAgent'를 사용합니다.
    logger = logging.getLogger("WebDevTrendsAgent")
    logger.setLevel(logging.INFO)

    # 핸들러가 이미 설정되어 있다면, 중복 추가를 방지합니다.
    if logger.hasHandlers():
        return logger

    # 콘솔 핸들러: 화면에 로그를 출력합니다.
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러: 매일 자정에 새 로그 파일을 생성합니다.
    file_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, "agent.log"),
        when="midnight",
        interval=1,
        backupCount=7, # 최대 7일치 로그 보관
        encoding="utf-8"
    )
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger

# 다른 파일에서 import하여 사용할 수 있도록 logger 인스턴스를 생성합니다.
logger = setup_logger()