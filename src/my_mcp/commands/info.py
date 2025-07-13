"""
정보 출력 명령어 비즈니스 로직
"""

import json
from rich.console import Console
from rich.table import Table
from ..utils.output_utils import CommonOptions, OutputFormat
from ..logging import get_logger
from ..tools import get_tool_registry

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
        
        if options and options.output_format == OutputFormat.json:
            data = {
                "name": "LangGraph 챗봇",
                "version": self.version,
                "description": "OpenAI API를 이용한 LangGraph 기반 챗봇 CLI 도구입니다.",
                "tools": {
                    "count": tool_count,
                    "available_tools": tool_info
                }
            }
            console.print(json.dumps(data, ensure_ascii=False, indent=2))
        elif options and options.output_format == OutputFormat.yaml:
            console.print("name: LangGraph 챗봇")
            console.print(f"version: {self.version}")
            console.print("description: OpenAI API를 이용한 LangGraph 기반 챗봇 CLI 도구입니다.")
            console.print("tools:")
            console.print(f"  total: {tool_count['total']}")
            console.print(f"  enabled: {tool_count['enabled']}")
            console.print(f"  disabled: {tool_count['disabled']}")
        else:
            # 텍스트 형식으로 출력
            console.print("[bold blue]🤖 LangGraph 챗봇[/bold blue]")
            console.print(f"버전: {self.version}")
            console.print("OpenAI API를 이용한 LangGraph 기반 챗봇 CLI 도구입니다.")
            console.print()
            
            # 도구 정보 테이블 생성
            self._display_tool_info(tool_info, tool_count)

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
    
    def get_version(self) -> str:
        """
        버전 정보 반환
        
        Returns:
            버전 문자열
        """
        return self.version 