"""
MCP 서버 정보 관리 클래스
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class MCPServer:
    """MCP 서버 정보를 저장하는 데이터 클래스"""
    name: str
    url: str
    enabled: bool = True
    timeout: int = 30
    headers: Dict[str, str] = field(default_factory=dict)
    
    # 런타임 상태 정보
    _connected: bool = field(default=False, init=False)
    _last_error: Optional[str] = field(default=None, init=False)
    _tools: Dict[str, Any] = field(default_factory=dict, init=False)
    
    def __post_init__(self):
        """초기화 후 검증"""
        if not self.name:
            raise ValueError("MCP 서버 이름은 필수입니다")
        if not self.url:
            raise ValueError("MCP 서버 URL은 필수입니다")
        if not self.url.startswith(("http://", "https://")):
            raise ValueError(f"MCP 서버 URL은 HTTP 형식이어야 합니다: {self.url}")
        
        # 기본 헤더 설정
        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = "application/json"
            
        logger.debug(f"MCP 서버 정보 생성: {self.name} - {self.url}")
    
    @property
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self._connected
    
    @property
    def last_error(self) -> Optional[str]:
        """마지막 오류 메시지"""
        return self._last_error
    
    @property
    def tools(self) -> Dict[str, Any]:
        """서버에서 제공하는 도구 목록"""
        return self._tools
    
    def set_connected(self, connected: bool, error: Optional[str] = None):
        """연결 상태 설정"""
        self._connected = connected
        self._last_error = error
        logger.debug(f"MCP 서버 {self.name} 연결 상태 변경: {connected}")
    
    def set_tools(self, tools: Dict[str, Any]):
        """도구 목록 설정"""
        self._tools = tools
        logger.debug(f"MCP 서버 {self.name} 도구 목록 업데이트: {len(tools)}개")
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 형태로 변환"""
        return {
            "name": self.name,
            "url": self.url,
            "enabled": self.enabled,
            "timeout": self.timeout,
            "headers": self.headers,
            "connected": self._connected,
            "last_error": self._last_error,
            "tools_count": len(self._tools)
        }
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "MCPServer":
        """설정에서 MCP 서버 생성"""
        return cls(
            name=config["name"],
            url=config["url"],
            enabled=config.get("enabled", True),
            timeout=config.get("timeout", 30),
            headers=config.get("headers", {})
        ) 