# logger.py
# 공통 로그 유틸리티 모듈
# - 파일 로그 + 콘솔 로그 + (옵션) 사용자 안내 메시지 버퍼
import logging
import os
from datetime import datetime
from typing import List, Dict

# 기본 로그 디렉토리 (프로젝트 루트 기준에서 조정 가능)
BASE_LOG_DIR = "../logs"

# 메모리에 사용자 안내 메시지 저장용 버퍼
#   - 나중에 웹에서 최근 안내 메시지를 가져갈 때 사용 가능
_USER_LOG_BUFFER: List[Dict] = []


def init_logger(work_dir: str | None = None) -> logging.Logger:
    """
    work_dir가 지정되면 해당 폴더에도 로그 파일 생성
    work_dir 없으면 기본 logs 폴더에 생성
    """
    if work_dir is None:
        log_dir = BASE_LOG_DIR
    else:
        log_dir = os.path.join(work_dir, "logs")

    os.makedirs(log_dir, exist_ok=True)

    # 로그 파일명 예: 2025-01-18.log
    log_filename = datetime.now().strftime("%Y-%m-%d") + ".log"
    log_file_path = os.path.join(log_dir, log_filename)

    logger = logging.getLogger("FinAI")
    logger.setLevel(logging.DEBUG)

    # 중복 핸들러 방지
    if logger.handlers:
        return logger

    # 파일 핸들러
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_format = logging.Formatter("[%(levelname)s] %(message)s")
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    logger.info(f"로그 초기화 완료 → {log_file_path}")
    return logger


# 공용 로그 함수
def log(message: str, level: str = "info", logger: logging.Logger | None = None):
    """
    일반 로그용 유틸 함수
    - logger가 없으면 자동으로 기본 로거 사용
    """
    if logger is None:
        logger = logging.getLogger("FinAI")
        if not logger.handlers:
            logger = init_logger()

    if level == "error":
        logger.error(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "debug":
        logger.debug(message)
    else:
        logger.info(message)


# 사용자용 안내 메시지 로그
def user_log(message: str, step: str | None = None):
    """
    사용자에게 보여줄 '대기 안내 메시지' 기록용 함수.
    - 콘솔/파일에도 찍고
    - _USER_LOG_BUFFER 에도 저장 (나중에 웹에서 사용 가능)
    """
    logger = logging.getLogger("FinAI")
    if not logger.handlers:
        logger = init_logger()

    prefix = "[사용자 안내] "
    full_msg = prefix + message
    logger.info(full_msg)

    _USER_LOG_BUFFER.append(
        {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "step": step or "",
            "message": message,
        }
    )


def get_user_logs(clear: bool = False) -> List[Dict]:
    """
    (옵션) 웹이나 다른 모듈에서 최근 사용자 안내 로그를 가져갈 수 있도록 제공.
    - clear=True면 반환 후 버퍼 비움
    """
    global _USER_LOG_BUFFER
    logs_copy = list(_USER_LOG_BUFFER)
    if clear:
        _USER_LOG_BUFFER = []
    return logs_copy
