"""
MCP 서버 레지스트리 관리 클래스
"""
from typing import Dict, List, Optional
from loguru import logger
from .server import MCPServer


class MCPRegistry:
    """MCP 서버들을 등록하고 관리하는 레지스트리"""
    
    def __init__(self):
        self._servers: Dict[str, MCPServer] = {}
        logger.debug("MCP 레지스트리 초기화")
    
    def register(self, server: MCPServer) -> None:
        """MCP 서버 등록"""
        if server.name in self._servers:
            logger.warning(f"MCP 서버 {server.name}이 이미 등록되어 있습니다. 덮어씁니다.")
        
        self._servers[server.name] = server
        logger.info(f"MCP 서버 등록: {server.name} - {server.url}")
    
    def unregister(self, name: str) -> bool:
        """MCP 서버 등록 해제"""
        if name in self._servers:
            del self._servers[name]
            logger.info(f"MCP 서버 등록 해제: {name}")
            return True
        return False
    
    def get_server(self, name: str) -> Optional[MCPServer]:
        """이름으로 MCP 서버 조회"""
        return self._servers.get(name)
    
    def get_all_servers(self) -> List[MCPServer]:
        """모든 MCP 서버 목록 반환"""
        return list(self._servers.values())
    
    def get_enabled_servers(self) -> List[MCPServer]:
        """활성화된 MCP 서버 목록 반환"""
        return [server for server in self._servers.values() if server.enabled]
    
    def get_connected_servers(self) -> List[MCPServer]:
        """연결된 MCP 서버 목록 반환"""
        return [server for server in self._servers.values() if server.is_connected]
    
    def get_server_count(self) -> int:
        """등록된 MCP 서버 개수"""
        return len(self._servers)
    
    def get_status_summary(self) -> Dict[str, int]:
        """MCP 서버 상태 요약"""
        total = len(self._servers)
        enabled = len(self.get_enabled_servers())
        connected = len(self.get_connected_servers())
        
        return {
            "total": total,
            "enabled": enabled,
            "connected": connected,
            "disconnected": enabled - connected
        }
    
    def clear(self) -> None:
        """모든 MCP 서버 등록 해제"""
        count = len(self._servers)
        self._servers.clear()
        logger.info(f"모든 MCP 서버 등록 해제: {count}개")
    
    def load_from_config(self, config_list: List[Dict]) -> None:
        """설정에서 MCP 서버들 로드"""
        for config in config_list:
            try:
                server = MCPServer.from_config(config)
                self.register(server)
            except Exception as e:
                logger.error(f"MCP 서버 로드 실패: {config.get('name', 'Unknown')} - {e}")
    
    def __len__(self) -> int:
        """등록된 서버 개수"""
        return len(self._servers)
    
    def __contains__(self, name: str) -> bool:
        """서버 존재 여부 확인"""
        return name in self._servers
    
    def __iter__(self):
        """서버 목록 반복"""
        return iter(self._servers.values())


# 전역 레지스트리 인스턴스
mcp_registry = MCPRegistry() 