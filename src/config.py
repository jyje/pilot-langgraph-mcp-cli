"""
Configuration management using Dynaconf
"""
from pathlib import Path
from dynaconf import Dynaconf
from loguru import logger

# Python 3.12+ 환경에서 내장 tomllib 사용
try:
    import tomllib
except ImportError:
    tomllib = None

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent

# 설정 파일 경로
SETTINGS_FILE = PROJECT_ROOT / "settings.yaml"

# Dynaconf 설정 객체 생성
settings = Dynaconf(
    settings_files=[str(SETTINGS_FILE)],
)

def get_version():
    """pyproject.toml에서 버전 정보를 읽어옵니다."""
    try:
        pyproject_path = PROJECT_ROOT / "pyproject.toml"
        
        if not pyproject_path.exists():
            logger.warning(f"pyproject.toml 파일을 찾을 수 없습니다: {pyproject_path}")
            return "0.1.0"  # 기본값
        
        if tomllib is None:
            logger.warning("tomllib 모듈을 찾을 수 없습니다. 기본 버전을 사용합니다.")
            return "0.1.0"
        
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
            version = data.get("project", {}).get("version", "0.1.0")
            return version
    
    except Exception as e:
        logger.error(f"버전 정보 읽기 실패: {e}")
        return "0.1.0"  # 기본값

def get_openai_config():
    """OpenAI API 설정 반환"""
    return {
        "api_key": settings.openai.api_key,
        "model": settings.get("openai.model", "gpt-4o-mini"),
        "temperature": settings.get("openai.temperature", 0.7),
        "max_tokens": settings.get("openai.max_tokens", 1000),
        "streaming": settings.get("openai.streaming", True),
    }

def get_chatbot_config():
    """챗봇 설정 반환"""
    return {
        "name": settings.get("chatbot.name", "LangGraph Assistant"),
        "welcome_message": settings.get("chatbot.welcome_message", "안녕하세요! LangGraph 챗봇입니다."),
        "system_prompt": settings.get("chatbot.system_prompt", "당신은 도움이 되는 AI 어시스턴트입니다."),
    }



def is_development():
    """개발 모드 여부 확인"""
    return settings.get("development.debug", False)

def is_verbose():
    """상세 모드 여부 확인"""
    return settings.get("development.verbose", False)

def check_settings():
    """설정 파일 존재 여부 확인"""
    if not SETTINGS_FILE.exists():
        logger.error(f"설정 파일이 없습니다: {SETTINGS_FILE}")
        logger.info(f"settings.sample.yaml을 {SETTINGS_FILE.name}로 복사하여 설정을 완료하세요.")
        return False
    
    # API 키 확인
    try:
        api_key = settings.openai.api_key
        if not api_key or api_key == "your-openai-api-key-here":
            logger.error("OpenAI API 키가 설정되지 않았습니다.")
            logger.info("settings.yaml에서 openai.api_key를 설정하세요.")
            return False
        
        logger.success("설정 파일 검증 완료")
        return True
    except Exception as e:
        logger.error(f"설정 파일 읽기 오류: {e}")
        return False 