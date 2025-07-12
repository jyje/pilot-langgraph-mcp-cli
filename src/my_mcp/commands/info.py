"""
정보 출력 명령어 비즈니스 로직
"""

import json
from rich.console import Console
from ..utils.output_utils import CommonOptions, OutputFormat
from ..logging import get_logger

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
        if options and options.output_format == OutputFormat.json:
            data = {
                "name": "LangGraph 챗봇",
                "version": self.version,
                "description": "OpenAI API를 이용한 LangGraph 기반 챗봇 CLI 도구입니다."
            }
            console.print(json.dumps(data, ensure_ascii=False, indent=2))
        elif options and options.output_format == OutputFormat.yaml:
            console.print("name: LangGraph 챗봇")
            console.print(f"version: {self.version}")
            console.print("description: OpenAI API를 이용한 LangGraph 기반 챗봇 CLI 도구입니다.")
        else:
            console.print("[bold blue]🤖 LangGraph 챗봇[/bold blue]")
            console.print(f"버전: {self.version}")
            console.print("OpenAI API를 이용한 LangGraph 기반 챗봇 CLI 도구입니다.")

        if options and options.verbose:
            console.print(f"[dim]설정 파일: {options.config_file or 'None'}[/dim]")
    
    def get_version(self) -> str:
        """
        버전 정보 반환
        
        Returns:
            버전 문자열
        """
        return self.version 