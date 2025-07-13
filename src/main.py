"""LangGraph 챗봇 CLI 진입점"""

import asyncio
import typer
from typing_extensions import Annotated
from pathlib import Path

# 프로젝트 모듈 import
from my_mcp.config import check_settings, get_openai_config, get_chatbot_config, get_version, get_mcp_servers
from my_mcp.logging import setup_logging
from my_mcp.utils import OutputFormat, CommonOptions, output_result
from my_mcp.commands import ChatCommand, InfoCommand, SetupCommand, ExportCommand


# 전역 상태 저장
state = {"options": None}

# Agent 하위 커맨드 그룹 생성
agent_app = typer.Typer(help="LangGraph 에이전트 관리 명령어", rich_markup_mode="markdown")
app = typer.Typer(help="OpenAI API 기반 LangGraph 챗봇 CLI", rich_markup_mode="markdown")

# Agent 하위 커맨드 그룹을 메인 앱에 추가
app.add_typer(agent_app, name="agent")


@agent_app.command("export")
def export_graph(
    format: Annotated[str, typer.Option("--format", "-f", help="출력 형식 (mermaid, json)")] = "mermaid",
    output: Annotated[str, typer.Option("--output", "-o", help="출력 파일 경로")] = None,
    ai_description: Annotated[bool, typer.Option("--ai-description", help="AI가 그래프 구조 설명을 자동 생성")] = False
):
    """LangGraph 그래프 구조를 내보냅니다."""
    
    # 설정 파일 확인
    if not check_settings():
        print("설정 파일을 먼저 구성해주세요.")
        return
    
    try:
        # 설정 로드
        openai_config = get_openai_config()
        chatbot_config = get_chatbot_config()
        mcp_servers = get_mcp_servers()
        
        # 내보내기 명령어 실행
        export_command = ExportCommand(openai_config, chatbot_config, mcp_servers)
        export_command.execute(format, output, ai_description)
        
    except Exception as e:
        print(f"그래프 내보내기 실패: {e}")


@app.callback()
def main_callback(
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="상세 출력 모드")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="조용한 모드")] = False,
    output_format: Annotated[OutputFormat, typer.Option("--output", "-o", help="출력 형식")] = OutputFormat.text,
    config_file: Annotated[str, typer.Option("--config", "-c", help="설정 파일 경로")] = None,
):
    """공통 옵션 설정"""
    state["options"] = CommonOptions(
        verbose = verbose,
        quiet = quiet,
        output_format = output_format,
        config_file = config_file
    )
    
    # loguru 로깅 설정
    setup_logging()


@app.command()
def chat(
    question: Annotated[str, typer.Argument(help="질문 내용 (제공 시 자동으로 일회성 대화 모드로 실행)")] = None,
    once: Annotated[bool, typer.Option("--once", help="일회성 대화 모드 (질문 입력 후 바로 종료)")] = False,
    no_stream: Annotated[bool, typer.Option("--no-stream", help="스트리밍 모드 비활성화")] = False,
    save: Annotated[str, typer.Option("--save", help="대화 내용을 마크다운 파일로 저장 (파일명 지정)")] = None
):
    """
    대화형 챗봇을 시작합니다.
    
    ## 사용법
    
    * **`my-mcp chat`** → 연속 대화 모드
    
    * **`my-mcp chat "질문내용"`** → 일회성 대화 (자동 종료)
    
    * **`my-mcp chat --once`** → 일회성 대화 (질문 입력 후 종료)
    
    * **`my-mcp chat --once "질문내용"`** → 일회성 대화 (명시적)
    """
    
    # 설정 파일 확인
    if not check_settings():
        print("설정 파일을 먼저 구성해주세요.")
        return
    
    try:
        # 설정 로드
        openai_config = get_openai_config()
        chatbot_config = get_chatbot_config()
        mcp_servers = get_mcp_servers()
        
        # 채팅 명령어 실행
        chat_command = ChatCommand(openai_config, chatbot_config, mcp_servers)
        
        # 일회성 대화 모드 또는 질문이 제공된 경우
        if once or question:
            asyncio.run(chat_command.execute_once(question, no_stream, save))
        else:
            # 연속 대화 모드
            asyncio.run(chat_command.execute_continuous(no_stream, save))
                
    except Exception as e:
        print(f"에이전트 초기화 실패: {e}")


@app.command()
def info():
    """LangGraph 챗봇 정보를 출력합니다."""
    options = state["options"]
    version = get_version()
    
    info_command = InfoCommand(version)
    info_command.execute(options)


@app.command()
def version():
    """버전 정보를 출력합니다."""
    version = get_version()
    message = f"LangGraph 챗봇 v{version}"
    options = state["options"]
    output_result(message, options=options)


@app.command()
def setup():
    """설정 파일을 생성합니다."""
    project_root = Path(__file__).parent.parent
    setup_command = SetupCommand(project_root)
    setup_command.execute()


def main():
    """메인 진입점"""
    app()


if __name__ == "__main__":
    main() 