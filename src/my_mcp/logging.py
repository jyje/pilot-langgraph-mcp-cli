"""
로깅 설정 및 관리 모듈 (loguru 기반)
"""
import sys
from pathlib import Path
from loguru import logger
from dynaconf import Dynaconf

# 설정 파일 경로 (상대 경로로 접근)
PROJECT_ROOT = Path(__file__).parent.parent.parent
SETTINGS_FILE = PROJECT_ROOT / "settings.yaml"

# 로깅 전용 설정 객체 (최소한의 설정만)
logging_settings = Dynaconf(
    settings_files=[str(SETTINGS_FILE)],
)

def get_logging_config():
    """로깅 설정 반환"""
    return {
        "level": logging_settings.get("logging.level", "INFO"),
        "format": logging_settings.get("logging.format", "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"),
        "rotation": logging_settings.get("logging.rotation", "10 MB"),
        "retention": logging_settings.get("logging.retention", "10 days"),
        "compression": logging_settings.get("logging.compression", "zip"),
        "backtrace": logging_settings.get("logging.backtrace", True),
        "diagnose": logging_settings.get("logging.diagnose", True),
    }

def setup_logging():
    """loguru 로깅 설정"""
    log_config = get_logging_config()
    
    # 기본 핸들러 제거
    logger.remove()
    
    # 콘솔 핸들러 추가
    logger.add(
        sys.stdout,
        format=log_config["format"],
        level=log_config["level"],
        colorize=True,
        backtrace=log_config["backtrace"],
        diagnose=log_config["diagnose"],
    )
    
    # 파일 핸들러 추가 (선택사항)
    if logging_settings.get("logging.file_enabled", False):
        log_file = logging_settings.get("logging.file_path", "logs/app.log")
        
        # 로그 디렉토리 생성
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            format=log_config["format"],
            level=log_config["level"],
            rotation=log_config["rotation"],
            retention=log_config["retention"],
            compression=log_config["compression"],
            backtrace=log_config["backtrace"],
            diagnose=log_config["diagnose"],
        )
    
    logger.info("로깅 시스템 초기화 완료")
    return logger

def get_logger(name: str = None):
    """로거 인스턴스 반환"""
    if name:
        return logger.bind(name=name)
    return logger 