"""My MCP CLI 진입점"""

import typer
from rich.console import Console
from rich.text import Text
from typing_extensions import Annotated
from dataclasses import dataclass
from enum import Enum
import json

console = Console()

# 출력 형식 정의
class OutputFormat(str, Enum):
    text = "text"
    json = "json"
    yaml = "yaml"

# 인사 언어 정의
class GreetingLanguage(str, Enum):
    korean = "korean"
    english = "english"
    japanese = "japanese"
    chinese = "chinese"
    spanish = "spanish"

# 인사 스타일 정의
class GreetingStyle(str, Enum):
    formal = "formal"
    casual = "casual"
    friendly = "friendly"
    professional = "professional"

# 전역 상태 저장
state = {"options": None}

@dataclass
class CommonOptions:
    verbose: bool = False
    quiet: bool = False
    output_format: OutputFormat = OutputFormat.text
    config_file: str = None

def get_greeting_message(name: str, language: GreetingLanguage, style: GreetingStyle) -> str:
    """언어와 스타일에 따른 인사 메시지 생성"""
    greetings = {
        GreetingLanguage.korean: {
            GreetingStyle.formal: f"안녕하십니까, {name}님!",
            GreetingStyle.casual: f"안녕, {name}!",
            GreetingStyle.friendly: f"안녕하세요, {name}님! 반가워요!",
            GreetingStyle.professional: f"안녕하세요, {name}님. 좋은 하루 되세요.",
        },
        GreetingLanguage.english: {
            GreetingStyle.formal: f"Good day, {name}!",
            GreetingStyle.casual: f"Hey, {name}!",
            GreetingStyle.friendly: f"Hello, {name}! Nice to meet you!",
            GreetingStyle.professional: f"Greetings, {name}. Have a productive day.",
        },
        GreetingLanguage.japanese: {
            GreetingStyle.formal: f"こんにちは、{name}さん!",
            GreetingStyle.casual: f"やあ、{name}!",
            GreetingStyle.friendly: f"こんにちは、{name}さん！お元気ですか？",
            GreetingStyle.professional: f"お疲れ様です、{name}さん。",
        },
        GreetingLanguage.chinese: {
            GreetingStyle.formal: f"您好，{name}！",
            GreetingStyle.casual: f"嗨，{name}！",
            GreetingStyle.friendly: f"你好，{name}！很高兴见到你！",
            GreetingStyle.professional: f"您好，{name}。祝您工作顺利。",
        },
        GreetingLanguage.spanish: {
            GreetingStyle.formal: f"Buenos días, {name}!",
            GreetingStyle.casual: f"¡Hola, {name}!",
            GreetingStyle.friendly: f"¡Hola, {name}! ¡Encantado de conocerte!",
            GreetingStyle.professional: f"Saludos, {name}. Que tenga un buen día.",
        }
    }

    return greetings[language][style]

def add_emoji_to_message(message: str, style: GreetingStyle) -> str:
    """스타일에 따른 이모지 추가"""
    emoji_map = {
        GreetingStyle.formal: "🎩",
        GreetingStyle.casual: "😄",
        GreetingStyle.friendly: "😊",
        GreetingStyle.professional: "💼",
    }

    return f"{emoji_map[style]} {message}"

def output_result(message: str, style: str = ""):
    """공통 출력 함수"""
    options = state["options"]
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

app = typer.Typer(help="My MCP CLI 도구")

@app.callback()
def main_callback(
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="상세 출력 모드")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="조용한 모드")] = False,
    output_format: Annotated[OutputFormat, typer.Option("--output", "-o", help="출력 형식")] = OutputFormat.text,
    config_file: Annotated[str, typer.Option("--config", "-c", help="설정 파일 경로")] = None,
):
    """공통 옵션 설정"""
    state["options"] = CommonOptions(
        verbose=verbose,
        quiet=quiet,
        output_format=output_format,
        config_file=config_file
    )

@app.command()
def hello(
    name: Annotated[str, typer.Option("--name", "-n", help="인사할 이름")] = "World",
    count: Annotated[int, typer.Option("--count", help="인사 메시지 반복 횟수")] = 1,
    language: Annotated[GreetingLanguage, typer.Option("--language", "-l", help="인사 언어")] = GreetingLanguage.korean,
    style: Annotated[GreetingStyle, typer.Option("--style", "-s", help="인사 스타일")] = GreetingStyle.friendly,
    emoji: Annotated[bool, typer.Option("--emoji", help="이모지 추가")] = False,
    uppercase: Annotated[bool, typer.Option("--uppercase", help="대문자로 출력")] = False,
    separator: Annotated[str, typer.Option("--separator", help="반복 시 구분자")] = "\n",
):
    """인사 메시지를 출력합니다."""
    # 기본 인사 메시지 생성
    message = get_greeting_message(name, language, style)

    # 이모지 추가
    if emoji:
        message = add_emoji_to_message(message, style)

    # 대문자 변환
    if uppercase:
        message = message.upper()

    # 반복 처리
    if count > 1:
        messages = [message] * count
        final_message = separator.join(messages)
    else:
        final_message = message

    # 스타일 색상 결정
    style_colors = {
        GreetingStyle.formal: "bold blue",
        GreetingStyle.casual: "bold green",
        GreetingStyle.friendly: "bold yellow",
        GreetingStyle.professional: "bold cyan",
    }

    output_result(final_message, style_colors[style])

@app.command()
def info():
    """MCP CLI 정보를 출력합니다."""
    options = state["options"]
    if options and options.output_format == OutputFormat.json:
        data = {
            "name": "My MCP CLI",
            "version": "0.1.0",
            "description": "MCP(Model Context Protocol) 관련 CLI 도구입니다."
        }
        console.print(json.dumps(data, ensure_ascii=False, indent=2))
    elif options and options.output_format == OutputFormat.yaml:
        console.print("name: My MCP CLI")
        console.print("version: 0.1.0")
        console.print("description: MCP(Model Context Protocol) 관련 CLI 도구입니다.")
    else:
        console.print("[bold blue]My MCP CLI[/bold blue]")
        console.print("버전: 0.1.0")
        console.print("MCP(Model Context Protocol) 관련 CLI 도구입니다.")

    if options and options.verbose:
        console.print(f"[dim]설정 파일: {options.config_file or 'None'}[/dim]")

@app.command()
def version():
    """버전 정보를 출력합니다."""
    message = "My MCP CLI v0.1.0"
    output_result(message)

def main():
    """메인 진입점"""
    app()

if __name__ == "__main__":
    main()