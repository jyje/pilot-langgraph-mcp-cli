"""
출력 관련 유틸리티 함수들
"""

import json
from dataclasses import dataclass
from enum import Enum
from rich.console import Console
from rich.text import Text


console = Console()


class OutputFormat(str, Enum):
    """출력 형식 정의"""
    text = "text"
    json = "json"
    yaml = "yaml"


@dataclass
class CommonOptions:
    """공통 옵션 데이터 클래스"""
    verbose: bool = False
    quiet: bool = False
    output_format: OutputFormat = OutputFormat.text
    config_file: str = None


def output_result(message: str, style: str = "", options: CommonOptions = None):
    """
    공통 출력 함수
    
    Args:
        message: 출력할 메시지
        style: 텍스트 스타일
        options: 공통 옵션
    """
    if options and options.quiet:
        return

    if options and options.output_format == OutputFormat.json:
        data = {"message": message, "status": "success"}
        console.print(json.dumps(data, ensure_ascii=False, indent=2))
    elif options and options.output_format == OutputFormat.yaml:
        console.print(f"message: {message}")
        console.print("status: success")
    else:
        if style:
            text = Text(message, style=style)
            console.print(text)
        else:
            console.print(message)

    if options and options.verbose:
        console.print(f"[dim]설정 파일: {options.config_file or 'None'}[/dim]") 