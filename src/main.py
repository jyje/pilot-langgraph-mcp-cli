"""LangGraph 챗봇 CLI 진입점"""

import asyncio
import sys
import typer
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.markdown import Markdown
from typing_extensions import Annotated
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
from loguru import logger

# 프로젝트 모듈 import
from config import check_settings, get_openai_config, get_chatbot_config
from my_mcp.logging import setup_logging
from my_mcp.service import create_chatbot_service

console = Console()

# 출력 형식 정의
class OutputFormat(str, Enum):
    text = "text"
    json = "json"
    yaml = "yaml"

# 전역 상태 저장
state = {"options": None}

@dataclass
class CommonOptions:
    verbose: bool = False
    quiet: bool = False
    output_format: OutputFormat = OutputFormat.text
    config_file: str = None



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

app = typer.Typer(help="OpenAI API 기반 LangGraph 챗봇 CLI")

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
    
    # loguru 로깅 설정
    setup_logging()

@app.command()
def chat():
    """대화형 챗봇을 시작합니다."""
    
    # 설정 파일 확인
    if not check_settings():
        console.print("[red]설정 파일을 먼저 구성해주세요.[/red]")
        return
    
    try:
        # 설정 로드
        openai_config = get_openai_config()
        chatbot_config = get_chatbot_config()
        
        # 챗봇 서비스 생성
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            task = progress.add_task("챗봇 초기화 중...", total=None)
            chatbot_service = create_chatbot_service(openai_config, chatbot_config)
            progress.update(task, completed=100)
        
        # 환영 메시지 표시
        welcome_panel = Panel(
            chatbot_service.get_welcome_message(),
            title=f"🤖 {chatbot_service.get_chatbot_name()}",
            border_style="blue"
        )
        console.print(welcome_panel)
        console.print("[dim]대화를 종료하려면 '/bye'를 입력하세요.[/dim]")
        console.print()
        
        # 대화 상태 저장
        conversation_state = {"messages": []}
        
        # 대화 루프
        while True:
            try:
                # 사용자 입력 받기
                user_input = console.input("[bold green]You:[/bold green] ")
                
                # 종료 명령어 확인
                if user_input.strip().lower() == "/bye":
                    console.print("[yellow]대화를 종료합니다. 안녕히 가세요! 👋[/yellow]")
                    break
                
                # 빈 입력 무시
                if not user_input.strip():
                    continue
                
                # 스트리밍 모드 확인
                streaming_enabled = get_openai_config().get("streaming", True)
                
                if streaming_enabled:
                    # AI 응답 스트리밍 생성
                    console.print("🤖 AI: ", end="", style="bold cyan")
                    
                    async def process_stream():
                        try:
                            response_started = False
                            async for chunk in chatbot_service.chat_stream(user_input, conversation_state):
                                if not response_started:
                                    response_started = True
                                console.print(chunk, end="", style="white")
                            # 스트리밍 완료 후 줄 나눔 추가
                            console.print("\n")
                        except Exception as e:
                            console.print(f"\n[red]스트리밍 오류: {e}[/red]")
                            logger.error(f"스트리밍 오류: {e}")
                    
                    # 비동기 스트리밍 실행
                    asyncio.run(process_stream())
                else:
                    # 기존 방식 (전체 응답 한 번에)
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        transient=True
                    ) as progress:
                        task = progress.add_task("AI가 답변을 생성하는 중...", total=None)
                        
                        # 비동기 호출을 동기적으로 실행
                        response = asyncio.run(chatbot_service.chat(user_input, conversation_state))
                        progress.update(task, completed=100)
                    
                    # AI 응답 표시
                    ai_panel = Panel(
                        response,
                        title="🤖 AI",
                        border_style="cyan"
                    )
                    console.print(ai_panel)
                    console.print()
                
            except KeyboardInterrupt:
                console.print("\n[yellow]대화를 종료합니다. 안녕히 가세요! 👋[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]오류가 발생했습니다: {e}[/red]")
                logger.error(f"채팅 오류: {e}")
                
    except Exception as e:
        console.print(f"[red]챗봇 초기화 실패: {e}[/red]")
        logger.error(f"챗봇 초기화 실패: {e}")

@app.command()
def info():
    """LangGraph 챗봇 정보를 출력합니다."""
    options = state["options"]
    if options and options.output_format == OutputFormat.json:
        data = {
            "name": "LangGraph 챗봇",
            "version": "0.1.0",
            "description": "OpenAI API를 이용한 LangGraph 기반 챗봇 CLI 도구입니다."
        }
        console.print(json.dumps(data, ensure_ascii=False, indent=2))
    elif options and options.output_format == OutputFormat.yaml:
        console.print("name: LangGraph 챗봇")
        console.print("version: 0.1.0")
        console.print("description: OpenAI API를 이용한 LangGraph 기반 챗봇 CLI 도구입니다.")
    else:
        console.print("[bold blue]🤖 LangGraph 챗봇[/bold blue]")
        console.print("버전: 0.1.0")
        console.print("OpenAI API를 이용한 LangGraph 기반 챗봇 CLI 도구입니다.")

    if options and options.verbose:
        console.print(f"[dim]설정 파일: {options.config_file or 'None'}[/dim]")

@app.command()
def version():
    """버전 정보를 출력합니다."""
    message = "LangGraph 챗봇 v0.1.0"
    output_result(message)

@app.command()
def setup():
    """설정 파일을 생성합니다."""
    project_root = Path(__file__).parent.parent
    settings_file = project_root / "settings.yaml"
    sample_file = project_root / "settings.sample.yaml"
    
    if settings_file.exists():
        console.print(f"[yellow]설정 파일이 이미 존재합니다: {settings_file}[/yellow]")
        return
    
    if not sample_file.exists():
        console.print(f"[red]템플릿 파일을 찾을 수 없습니다: {sample_file}[/red]")
        return
    
    try:
        # 템플릿 파일 복사
        import shutil
        shutil.copy2(sample_file, settings_file)
        
        console.print(f"[green]✅ 설정 파일이 생성되었습니다: {settings_file}[/green]")
        console.print("[yellow]settings.yaml 파일을 편집하여 OpenAI API 키를 설정하세요.[/yellow]")
        
    except Exception as e:
        console.print(f"[red]설정 파일 생성 실패: {e}[/red]")

def main():
    """메인 진입점"""
    app()

if __name__ == "__main__":
    main() 