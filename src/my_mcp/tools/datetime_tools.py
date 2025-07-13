"""
시간 관련 도구 모듈
"""

import datetime
from typing import Optional
from langchain.tools import tool
from ..logging import get_logger

logger = get_logger("my_mcp.tools.datetime")


@tool
def get_current_time(format_type: Optional[str] = None, timezone: Optional[str] = None) -> str:
    """
    현재 시각을 안전하게 반환합니다.
    
    Args:
        format_type: 시간 형식 ('datetime', 'date', 'time', 'iso') 중 하나
                   기본값은 'datetime'으로 'YYYY-MM-DD HH:MM:SS' 형식
        timezone: 시간대 ('utc', 'local') 중 하나
                기본값은 'local'로 로컬 시간대
    
    Returns:
        현재 시각 문자열 (시간대 정보 포함)
    """
    try:
        # 보안: format_type 입력 검증 (화이트리스트 방식)
        allowed_formats = ['datetime', 'date', 'time', 'iso']
        if format_type and format_type not in allowed_formats:
            logger.warning(f"허용되지 않은 형식: {format_type}")
            format_type = 'datetime'  # 기본값으로 설정
        
        # 보안: timezone 입력 검증 (화이트리스트 방식)
        allowed_timezones = ['utc', 'local']
        if timezone and timezone not in allowed_timezones:
            logger.warning(f"허용되지 않은 시간대: {timezone}")
            timezone = 'local'  # 기본값으로 설정
        
        # 시간대에 따른 현재 시간 가져오기
        if timezone == 'utc':
            now = datetime.datetime.now(datetime.timezone.utc)
            tz_info = " UTC"
        else:  # 'local' 또는 None
            now = datetime.datetime.now()
            tz_info = " (Local)"
        
        # 형식별 시간 반환
        if format_type == 'date':
            return f"{now.strftime('%Y-%m-%d')}{tz_info}"
        elif format_type == 'time':
            return f"{now.strftime('%H:%M:%S')}{tz_info}"
        elif format_type == 'iso':
            return now.isoformat()
        else:  # 'datetime' 또는 None
            return f"{now.strftime('%Y-%m-%d %H:%M:%S')}{tz_info}"
            
    except Exception as e:
        logger.error(f"시간 조회 실패: {e}")
        return "시간 정보를 가져올 수 없습니다."


def _validate_format_input(format_input: str) -> bool:
    """
    format_type 입력 검증 함수
    
    Args:
        format_input: 사용자 입력 형식
        
    Returns:
        검증 결과 (True: 유효, False: 무효)
    """
    # 허용된 형식만 승인
    allowed_formats = ['datetime', 'date', 'time', 'iso']
    
    # 기본 타입 검증
    if not isinstance(format_input, str):
        return False
        
    # 길이 제한 (보안: 긴 입력 차단)
    if len(format_input) > 20:
        return False
        
    # 특수문자 차단 (보안: 주입 공격 방지)
    if any(char in format_input for char in ['/', '\\', ';', '&', '|', '`', '$', '(', ')', '<', '>']):
        return False
    
    # 화이트리스트 검증
    return format_input in allowed_formats


def _validate_timezone_input(timezone_input: str) -> bool:
    """
    timezone 입력 검증 함수
    
    Args:
        timezone_input: 사용자 입력 시간대
        
    Returns:
        검증 결과 (True: 유효, False: 무효)
    """
    # 허용된 시간대만 승인
    allowed_timezones = ['utc', 'local']
    
    # 기본 타입 검증
    if not isinstance(timezone_input, str):
        return False
        
    # 길이 제한 (보안: 긴 입력 차단)
    if len(timezone_input) > 10:
        return False
        
    # 특수문자 차단 (보안: 주입 공격 방지)
    if any(char in timezone_input for char in ['/', '\\', ';', '&', '|', '`', '$', '(', ')', '<', '>']):
        return False
    
    # 화이트리스트 검증
    return timezone_input in allowed_timezones 