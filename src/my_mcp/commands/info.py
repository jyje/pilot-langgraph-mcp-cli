"""
정보 출력 명령어 비즈니스 로직
"""

import json
import asyncio
from rich.console import Console
from rich.table import Table
from ..utils.output_utils import CommonOptions, OutputFormat
from ..logging import get_logger
from ..tools import get_tool_registry
from ..mcp import mcp_registry, mcp_client_manager
from ..config import get_mcp_servers

console = Console()
logger = get_logger("my_mcp.commands.info")


class InfoCommand:
    """정보 출력 명령어 처리 클래스"""
    
    def __init__(self, version: str):
        """
        정보 명령어 초기화
        
        Args:
            version: 애플리케이션 버전
        """
        self.version = version
    
    def execute(self, options: CommonOptions = None):
        """
        정보 출력 명령어 실행
        
        Args:
            options: 공통 옵션
        """
        # 도구 정보 가져오기
        tool_registry = get_tool_registry()
        tool_info = tool_registry.get_tool_info()
        tool_count = tool_registry.get_tool_count()
        
        # MCP 서버 정보 가져오기
        # 설정에서 직접 MCP 서버 로드
        mcp_server_configs = get_mcp_servers()
        
        # MCP 서버가 없는 경우 MCP 관련 처리 생략
        if not mcp_server_configs:
            logger.debug("MCP 서버가 설정되지 않았습니다. MCP 기능을 생략합니다.")
            mcp_servers = []
            mcp_status = {"total": 0, "active": 0, "connected": 0}
            mcp_tools = {}
        else:
            # 임시로 registry에 로드
            mcp_registry.load_from_config(mcp_server_configs)
            
            # MCP 서버 연결 테스트
            connection_success = asyncio.run(self._test_mcp_connections())
            
            mcp_servers = mcp_registry.get_all_servers()
            mcp_status = mcp_registry.get_status_summary()
            
            # 연결 성공 시에만 도구 정보 가져오기
            if connection_success:
                mcp_tools = mcp_client_manager.get_tool_info()
            else:
                mcp_tools = {}
        
        if options and options.output_format == OutputFormat.json:
            data = {
                "name": "LangGraph 챗봇",
                "version": self.version,
                "description": "OpenAI API를 이용한 LangGraph 기반 챗봇 CLI 도구입니다.",
                "tools": {
                    "built_in": {
                        "count": tool_count,
                        "list": tool_info
                    }
                }
            }
            
            # MCP 서버가 있을 때만 MCP 정보 추가
            if mcp_server_configs:
                data["tools"]["mcp"] = {
                    "count": len(mcp_tools),
                    "list": mcp_tools
                }
                data["mcp_servers"] = {
                    "count": mcp_status,
                    "status": mcp_status,
                    "servers": [server.to_dict() for server in mcp_servers]
                }
            
            console.print(json.dumps(data, ensure_ascii=False, indent=2))
        elif options and options.output_format == OutputFormat.yaml:
            console.print("name: LangGraph 챗봇")
            console.print(f"version: {self.version}")
            console.print("description: OpenAI API를 이용한 LangGraph 기반 챗봇 CLI 도구입니다.")
            console.print("tools:")
            console.print("  built_in:")
            console.print(f"    total: {tool_count['total']}")
            console.print(f"    enabled: {tool_count['enabled']}")
            console.print(f"    disabled: {tool_count['disabled']}")
            
            # MCP 서버가 있을 때만 MCP 정보 추가
            if mcp_server_configs:
                console.print("  mcp:")
                console.print(f"    total: {len(mcp_tools)}")
                console.print("mcp_servers:")
                console.print(f"  total: {mcp_status['total']}")
                console.print(f"  enabled: {mcp_status['enabled']}")
                console.print(f"  connected: {mcp_status['connected']}")
        else:
            # 텍스트 형식으로 출력
            console.print("[bold blue]🤖 LangGraph 챗봇[/bold blue]")
            console.print(f"버전: {self.version}")
            console.print("OpenAI API를 이용한 LangGraph 기반 챗봇 CLI 도구입니다.")
            console.print()
            
            # 도구 정보 테이블 생성
            self._display_tool_info(tool_info, tool_count)
            
            # MCP 서버 정보 표시 (서버가 있을 때만)
            if mcp_server_configs:
                self._display_mcp_info(mcp_servers, mcp_status, mcp_tools)

        if options and options.verbose:
            console.print(f"[dim]설정 파일: {options.config_file or 'None'}[/dim]")
    
    def _display_tool_info(self, tool_info: list, tool_count: dict):
        """
        도구 정보를 테이블로 표시
        
        Args:
            tool_info: 도구 정보 목록
            tool_count: 도구 개수 정보
        """
        console.print("[bold green]🔧 사용 가능한 도구[/bold green]")
        console.print(f"총 {tool_count['total']}개 도구 (활성화: {tool_count['enabled']}개, 비활성화: {tool_count['disabled']}개)")
        console.print()
        
        if tool_info:
            table = Table(title="도구 목록")
            table.add_column("도구명", style="cyan", no_wrap=True)
            table.add_column("상태", style="magenta", width=12)
            table.add_column("설명", style="white")
            
            for tool in tool_info:
                status_color = "green" if tool["enabled"] else "red"
                status_text = f"[{status_color}]{tool['status']}[/{status_color}]"
                table.add_row(tool["name"], status_text, tool["description"])
            
            console.print(table)
        else:
            console.print("[yellow]등록된 도구가 없습니다.[/yellow]")
        
        console.print()
    
    def _display_mcp_info(self, servers: list, status: dict, tools: dict):
        """
        MCP 서버 정보를 테이블로 표시
        
        Args:
            servers: MCP 서버 목록
            status: MCP 서버 상태 요약
            tools: MCP 도구 목록
        """
        console.print("[bold green]🌐 MCP 서버[/bold green]")
        console.print(f"총 {status['total']}개 서버 (활성화: {status['enabled']}개, 연결됨: {status['connected']}개)")
        console.print()
        
        if servers:
            # 서버 정보 테이블
            server_table = Table(title="MCP 서버 목록")
            server_table.add_column("서버명", style="cyan", no_wrap=True)
            server_table.add_column("상태", style="magenta", width=12)
            server_table.add_column("URL", style="white")
            server_table.add_column("도구 수", style="yellow", width=10)
            server_table.add_column("오류", style="red")
            
            for server in servers:
                # 상태 색상 결정
                if not server.enabled:
                    status_color = "dim"
                    status_text = "비활성화"
                elif server.is_connected:
                    status_color = "green"
                    status_text = "연결됨"
                else:
                    status_color = "red"
                    status_text = "연결 실패"
                
                server_table.add_row(
                    server.name,
                    f"[{status_color}]{status_text}[/{status_color}]",
                    server.url,
                    str(len(server.tools)),
                    server.last_error or ""
                )
            
            console.print(server_table)
            console.print()
        
        # MCP 도구 정보
        if tools:
            console.print("[bold green]🔧 MCP 도구[/bold green]")
            console.print(f"총 {len(tools)}개 도구 사용 가능")
            console.print()
            
            tool_table = Table(title="MCP 도구 목록")
            tool_table.add_column("도구명", style="cyan", no_wrap=True)
            tool_table.add_column("서버", style="magenta", width=20)
            tool_table.add_column("설명", style="white")
            
            for tool_name, tool_info in tools.items():
                server_name = tool_info.get("server", "Unknown")
                description = tool_info.get("description", "설명 없음")
                
                tool_table.add_row(
                    tool_name.split("/")[-1],  # 서버 이름 제거
                    server_name,
                    description
                )
            
            console.print(tool_table)
        else:
            console.print("[yellow]사용 가능한 MCP 도구가 없습니다.[/yellow]")
        
        console.print()
    
    def get_version(self) -> str:
        """
        버전 정보 반환
        
        Returns:
            str: 버전 정보
        """
        return self.version
    
    async def _test_mcp_connections(self) -> bool:
        """MCP 서버 연결 테스트"""
        try:
            # 서버 목록 설정
            servers = mcp_registry.get_enabled_servers()
            if servers:
                mcp_client_manager.set_servers(servers)
                
                # MCP 클라이언트 초기화 및 연결 테스트
                success = await mcp_client_manager.initialize()
                
                # 각 서버의 연결 상태 업데이트
                for server in servers:
                    if success:
                        server.set_connected(True)
                        logger.debug(f"MCP 서버 {server.name} 연결 성공")
                    else:
                        server.set_connected(False, "연결 실패")
                        logger.debug(f"MCP 서버 {server.name} 연결 실패")
                
                if success:
                    logger.debug("MCP 서버 연결 테스트 성공")
                    tools = mcp_client_manager.get_tools()
                    logger.debug(f"발견된 MCP 도구: {len(tools)}개")
                    
                    # 각 서버에 도구 정보 설정
                    all_tools = mcp_client_manager.get_tool_info()
                    for server in servers:
                        # 해당 서버의 도구만 필터링
                        server_tools = {k: v for k, v in all_tools.items() if v.get("server") == server.name}
                        server.set_tools(server_tools)
                    
                    return True
                else:
                    logger.debug("MCP 서버 연결 테스트 실패")
                    return False
            
            return False
        except Exception as e:
            logger.error(f"MCP 서버 연결 테스트 오류: {e}")
            # 오류 발생 시 모든 서버를 연결 실패로 설정
            for server in mcp_registry.get_all_servers():
                server.set_connected(False, str(e))
            return False 