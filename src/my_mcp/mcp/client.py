"""
공식 LangGraph MCP 어댑터를 사용하는 클라이언트
"""
import asyncio
from typing import Dict, List, Optional, Any
from loguru import logger
from langchain_mcp_adapters.client import MultiServerMCPClient
from .server import MCPServer


class MCPClient:
    """공식 LangGraph MCP 어댑터를 사용하는 클라이언트"""
    
    def __init__(self, servers: List[MCPServer]):
        self.servers = servers
        self.client: Optional[MultiServerMCPClient] = None
        self.tools: List[Any] = []
        
    async def initialize(self) -> bool:
        """MCP 클라이언트 초기화"""
        try:
            # 서버 설정 변환
            server_config = {}
            for server in self.servers:
                # HTTP 전송 방식 사용
                server_config[server.name] = {
                    "url": server.url,
                    "transport": "streamable_http",
                }
            
            # MultiServerMCPClient 초기화
            self.client = MultiServerMCPClient(server_config)
            
            # 도구 가져오기 (이 과정에서 실제 연결 상태가 확인됨)
            self.tools = await self.client.get_tools()
            
            # get_tools() 호출이 성공했다면 연결 성공으로 간주
            # 도구가 없어도 연결 자체는 성공한 것으로 판단
            logger.info(f"MCP 클라이언트 초기화 완료: {len(self.tools)}개 도구")
            return True
            
        except Exception as e:
            logger.error(f"MCP 클라이언트 초기화 실패: {e}")
            self.tools = []
            return False
    
    async def close(self):
        """클라이언트 종료"""
        if self.client:
            # MultiServerMCPClient에는 close() 메서드가 없으므로 생략
            logger.info("MCP 클라이언트 종료")
    
    def get_tools(self) -> List[Any]:
        """도구 목록 반환"""
        return self.tools
    
    def get_tool_info(self) -> Dict[str, Any]:
        """도구 정보 반환"""
        tool_info = {}
        for tool in self.tools:
            # 서버 정보 추가
            server_name = None
            if hasattr(tool, 'server_name') and tool.server_name:
                server_name = tool.server_name
            else:
                # 도구 이름에서 서버 이름 추출 (예: "server_name/tool_name")
                if "/" in tool.name:
                    server_name = tool.name.split("/")[0]
                else:
                    # 서버 목록에서 찾기
                    for server in self.servers:
                        server_name = server.name
                        break
            
            tool_info[tool.name] = {
                "name": tool.name,
                "description": tool.description,
                "server": server_name or "Unknown",
                "args_schema": tool.args_schema.schema() if hasattr(tool.args_schema, 'schema') else str(tool.args_schema)
            }
        return tool_info


class MCPClientManager:
    """MCP 클라이언트 관리자"""
    
    def __init__(self):
        self.client: Optional[MCPClient] = None
        self.servers: List[MCPServer] = []
        
    def set_servers(self, servers: List[MCPServer]):
        """서버 목록 설정"""
        self.servers = servers
        
    async def initialize(self) -> bool:
        """MCP 관리자 초기화"""
        if not self.servers:
            logger.warning("초기화할 MCP 서버가 없습니다")
            return False
            
        self.client = MCPClient(self.servers)
        return await self.client.initialize()
    
    async def close(self):
        """관리자 종료"""
        if self.client:
            await self.client.close()
    
    def get_tools(self) -> List[Any]:
        """도구 목록 반환"""
        if self.client:
            return self.client.get_tools()
        return []
    
    def get_tool_info(self) -> Dict[str, Any]:
        """도구 정보 반환"""
        if self.client:
            return self.client.get_tool_info()
        return {}


# 전역 인스턴스
mcp_client_manager = MCPClientManager() 