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

# Agent 하위 커맨드 그룹 생성
agent_app = typer.Typer(help="LangGraph 에이전트 관리 명령어")



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
        console.print("[red]설정 파일을 먼저 구성해주세요.[/red]")
        return
    
    # 기본 출력 경로 설정
    if not output:
        default_dir = Path(".my-mcp")
        try:
            # 디렉토리가 없으면 생성
            default_dir.mkdir(exist_ok=True)
            output = str(default_dir / "diagram.md")
            console.print(f"[dim]기본 경로에 저장합니다: {output}[/dim]")
        except Exception as e:
            console.print(f"[red]❌ 기본 디렉토리 생성 실패: {e}[/red]")
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
            task = progress.add_task("챗봇 서비스 초기화 중...", total=None)
            chatbot_service = create_chatbot_service(openai_config, chatbot_config)
            progress.update(task, completed=100)
        
        # 그래프 구조 가져오기
        graph = chatbot_service.app.get_graph()
        
        # 그래프에서 실제 노드와 엣지 정보 추출
        try:
            # LangGraph의 그래프 객체에서 노드와 엣지를 올바르게 추출
            nodes = []
            edges = []
            
            # 그래프가 dict 형태인지 확인
            if hasattr(graph, 'nodes') and hasattr(graph, 'edges'):
                # 노드 정보 추출
                if hasattr(graph.nodes, '__call__'):
                    nodes = list(graph.nodes())
                elif hasattr(graph.nodes, 'keys'):
                    nodes = list(graph.nodes.keys())
                else:
                    nodes = list(graph.nodes) if graph.nodes else []
                
                # 엣지 정보 추출
                if hasattr(graph.edges, '__call__'):
                    raw_edges = list(graph.edges())
                    # Edge 객체에서 source와 target 추출
                    edges = []
                    for edge in raw_edges:
                        if hasattr(edge, 'source') and hasattr(edge, 'target'):
                            edges.append((edge.source, edge.target))
                        elif isinstance(edge, (list, tuple)) and len(edge) >= 2:
                            edges.append((edge[0], edge[1]))
                elif hasattr(graph.edges, 'keys'):
                    edges = [(k, v) for k, v in graph.edges.items()]
                else:
                    edges = list(graph.edges) if graph.edges else []
            
            # 추출 실패 시 서비스 객체에서 직접 가져오기
            if not nodes:
                # 워크플로우 객체에서 직접 노드 정보 가져오기
                workflow = chatbot_service.workflow
                if hasattr(workflow, 'nodes'):
                    nodes = list(workflow.nodes.keys()) if hasattr(workflow.nodes, 'keys') else []
            
            # 그래프 정보가 없으면 오류 발생
            if not nodes or not edges:
                raise ValueError("그래프 구조 정보를 추출할 수 없습니다.")
            
        except Exception as e:
            logger.error(f"그래프 정보 추출 실패: {e}")
            console.print(f"[red]❌ 그래프 구조를 추출할 수 없습니다: {e}[/red]")
            return
        
        # AI 설명 생성
        description = None
        if ai_description:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True
            ) as progress:
                task = progress.add_task("AI가 그래프 구조 설명을 생성하는 중...", total=None)
                description = generate_ai_description_sync(chatbot_service, nodes, edges)
                progress.update(task, completed=100)
        
        if format.lower() == "mermaid":
            try:
                # 출력 파일 경로 준비
                output_path = Path(output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 마크다운 코드블럭으로 감싸기
                mermaid_content = generate_mermaid_diagram(nodes, edges, description, for_console=False)
                markdown_content = f"""# LangGraph 워크플로우 구조

```mermaid
{mermaid_content}
```
"""
                if description:
                    markdown_content += f"\n## 설명\n\n{description}\n"
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                console.print(f"[green]✅ Mermaid 다이어그램이 '{output}' 파일에 저장되었습니다.[/green]")
            except Exception as e:
                console.print(f"[red]❌ Mermaid 다이어그램 생성 실패: {e}[/red]")
                return
                
        elif format.lower() == "json":
            # JSON 형식으로 내보내기
            import json
            
            try:
                # 출력 파일 경로 준비
                output_path = Path(output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # JSON 데이터 생성
                node_list = [{"id": node, "type": "node", "label": node} for node in nodes]
                edge_list = [{"source": edge[0], "target": edge[1]} for edge in edges if isinstance(edge, (list, tuple)) and len(edge) >= 2]
                
                graph_data = {
                    "nodes": node_list,
                    "edges": edge_list,
                    "workflow": "LangGraph Assistant",
                    "description": description or "입력 처리 → 응답 생성 → 출력 포맷팅 워크플로우"
                }
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(graph_data, f, ensure_ascii=False, indent=2)
                console.print(f"[green]✅ 그래프 구조가 '{output}' 파일에 저장되었습니다.[/green]")
            except Exception as e:
                console.print(f"[red]❌ JSON 형식 생성 실패: {e}[/red]")
                return
        
        else:
            console.print(f"[red]지원되지 않는 형식입니다: {format}[/red]")
            console.print("지원되는 형식: mermaid, json")
            
    except Exception as e:
        console.print(f"[red]그래프 내보내기 실패: {e}[/red]")
        logger.error(f"그래프 내보내기 실패: {e}")

def generate_ai_description_sync(chatbot_service, nodes, edges) -> str:
    """AI를 이용해 그래프 구조 설명을 생성합니다. (동기 버전)"""
    try:
        # 그래프 구조 정보 정리
        node_info = []
        for node in nodes:
            node_info.append(f"{node}")
        
        edge_info = []
        for edge in edges:
            if isinstance(edge, (list, tuple)) and len(edge) >= 2:
                edge_info.append(f"{edge[0]} → {edge[1]}")
        
        # AI에게 설명 생성 요청
        prompt = f"""다음 LangGraph 워크플로우에 대한 간단하고 명확한 설명을 한국어로 작성해주세요:

노드 (처리 단계):
{', '.join(node_info)}

연결 관계:
{', '.join(edge_info)}

요구사항:
- 2-3문장으로 간단하게 설명
- 워크플로우의 전체적인 흐름과 목적을 설명
- 기술적 용어보다는 이해하기 쉬운 표현 사용
- 설명만 반환하고 다른 내용은 포함하지 마세요"""

        # 직접 LLM 호출 (동기 방식)
        from langchain.schema import HumanMessage, SystemMessage
        
        messages = [
            SystemMessage(content="당신은 워크플로우 설명을 작성하는 전문가입니다. 간단하고 명확한 설명을 제공해주세요."),
            HumanMessage(content=prompt)
        ]
        
        # LLM 직접 호출
        response = chatbot_service.llm.invoke(messages)
        description = response.content.strip()
        
        return description
        
    except Exception as e:
        logger.error(f"AI 설명 생성 실패: {e}")
        return "사용자 입력을 처리하고 AI가 응답을 생성한 후 적절한 형식으로 출력하는 워크플로우입니다."

def generate_mermaid_diagram(nodes, edges, description=None, for_console=False) -> str:
    """LangGraph를 Mermaid 다이어그램으로 변환"""
    try:
        # 노드와 엣지가 모두 비어있으면 오류
        if not nodes or not edges:
            raise ValueError("그래프 정보를 추출할 수 없습니다.")
        
        mermaid_lines = ["graph TD"]
        
        # 노드 정의
        for node in nodes:
            mermaid_lines.append(f'    {node}[\"{node}\"]')
        
        # 엣지 정의 (원본 이름 그대로 사용)
        for edge in edges:
            if isinstance(edge, (list, tuple)) and len(edge) >= 2:
                source, target = edge[0], edge[1]
                mermaid_lines.append(f"    {source} --> {target}")
        
        # 스타일 추가 (글씨 검은색으로)
        mermaid_lines.extend([
            "",
            "    classDef startEnd fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000;",
            "    classDef process fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#000;",
            "    classDef generate fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px,color:#000;",
            "    classDef format fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000;",
            "",
            "    class __start__,__end__ startEnd",
            "    class process_input process",
            "    class generate_response generate", 
            "    class format_output format"
        ])
        
        # 콘솔 출력일 때만 설명 추가
        if for_console and description:
            mermaid_lines.extend([
                "",
                "---",
                f"**설명**: {description}"
            ])
        
        return "\n".join(mermaid_lines)
        
    except Exception as e:
        logger.error(f"Mermaid 다이어그램 생성 실패: {e}")
        raise e  # 오류를 다시 발생시켜서 상위에서 처리하도록 함

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
def chat(
    question: Annotated[str, typer.Argument(help="질문 내용 (일회성 대화 시 사용)")] = None,
    once: Annotated[bool, typer.Option("--once", help="일회성 대화 모드 (한 번만 질문/답변 후 종료)")] = False,
    no_stream: Annotated[bool, typer.Option("--no-stream", help="스트리밍 모드 비활성화")] = False,
    save: Annotated[str, typer.Option("--save", help="대화 내용을 마크다운 파일로 저장 (파일명 지정)")] = None
):
    """대화형 챗봇을 시작합니다."""
    
    # 설정 파일 확인
    if not check_settings():
        console.print("[red]설정 파일을 먼저 구성해주세요.[/red]")
        return
    
    # 마크다운 저장을 위한 대화 기록
    conversation_log = []
    
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
        
        # 일회성 대화 모드 또는 질문이 제공된 경우
        if once or question:
            # 간단한 환영 메시지 (일회성)
            console.print(f"[bold blue]🤖 {chatbot_service.get_chatbot_name()}[/bold blue]")
            console.print("[dim]일회성 대화 모드입니다.[/dim]")
            console.print()
            
            # 질문 결정
            if question:
                user_input = question
            else:
                # 사용자 입력 받기
                user_input = console.input("[bold green]질문:[/bold green] ")
            
            # 빈 입력 처리
            if not user_input.strip():
                console.print("[yellow]질문을 입력해주세요.[/yellow]")
                return
            
            # 대화 상태 저장 (일회성이므로 빈 상태)
            conversation_state = {"messages": []}
            
            # 스트리밍 모드 확인 (옵션으로 재정의)
            streaming_enabled = get_openai_config().get("streaming", True) and not no_stream
            
            ai_response = ""
            
            if streaming_enabled:
                # AI 응답 스트리밍 생성
                console.print("🤖 답변: ", end="", style="bold cyan")
                
                async def process_stream():
                    nonlocal ai_response
                    try:
                        response_started = False
                        async for chunk in chatbot_service.chat_stream(user_input, conversation_state):
                            if not response_started:
                                response_started = True
                            console.print(chunk, end="", style="white")
                            ai_response += chunk
                        # 스트리밍 완료 후 줄 나눔 추가
                        console.print("\n")
                    except Exception as e:
                        console.print(f"\n[red]스트리밍 오류: {e}[/red]")
                        logger.error(f"스트리밍 오류: {e}")
                        ai_response = "죄송합니다. 요청을 처리하는 중에 오류가 발생했습니다."
                
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
                    ai_response = asyncio.run(chatbot_service.chat(user_input, conversation_state))
                    progress.update(task, completed=100)
                
                # AI 응답 표시
                ai_panel = Panel(
                    ai_response,
                    title="🤖 AI",
                    border_style="cyan"
                )
                console.print(ai_panel)
                console.print()
            
            # 마크다운 저장 (일회성)
            if save:
                conversation_log.append(f"**사용자**: {user_input}\n")
                conversation_log.append(f"**AI**: {ai_response}\n")
                save_conversation_to_markdown(conversation_log, save)
            
            # 일회성 대화 종료
            return
        
        # 기존 연속 대화 모드
        # 환영 메시지 표시
        welcome_panel = Panel(
            chatbot_service.get_welcome_message(),
            title=f"🤖 {chatbot_service.get_chatbot_name()}",
            border_style="blue"
        )
        console.print(welcome_panel)
        console.print("[dim]대화를 종료하려면 '/bye'를 입력하세요.[/dim]")
        if save:
            console.print(f"[dim]대화 내용이 '{save}' 파일에 저장됩니다.[/dim]")
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
                
                # 스트리밍 모드 확인 (옵션으로 재정의)
                streaming_enabled = get_openai_config().get("streaming", True) and not no_stream
                
                ai_response = ""
                
                if streaming_enabled:
                    # AI 응답 스트리밍 생성
                    console.print("🤖 AI: ", end="", style="bold cyan")
                    
                    async def process_stream():
                        nonlocal ai_response
                        try:
                            response_started = False
                            async for chunk in chatbot_service.chat_stream(user_input, conversation_state):
                                if not response_started:
                                    response_started = True
                                console.print(chunk, end="", style="white")
                                ai_response += chunk
                            # 스트리밍 완료 후 줄 나눔 추가
                            console.print("\n")
                        except Exception as e:
                            console.print(f"\n[red]스트리밍 오류: {e}[/red]")
                            logger.error(f"스트리밍 오류: {e}")
                            ai_response = "죄송합니다. 요청을 처리하는 중에 오류가 발생했습니다."
                    
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
                        ai_response = asyncio.run(chatbot_service.chat(user_input, conversation_state))
                        progress.update(task, completed=100)
                    
                    # AI 응답 표시
                    ai_panel = Panel(
                        ai_response,
                        title="🤖 AI",
                        border_style="cyan"
                    )
                    console.print(ai_panel)
                    console.print()
                
                # 마크다운 저장을 위한 대화 기록
                if save:
                    conversation_log.append(f"**사용자**: {user_input}\n")
                    conversation_log.append(f"**AI**: {ai_response}\n")
                
            except KeyboardInterrupt:
                console.print("\n[yellow]대화를 종료합니다. 안녕히 가세요! 👋[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]오류가 발생했습니다: {e}[/red]")
                logger.error(f"채팅 오류: {e}")
        
        # 연속 대화 모드 종료 시 마크다운 저장
        if save and conversation_log:
            save_conversation_to_markdown(conversation_log, save)
                
    except Exception as e:
        console.print(f"[red]챗봇 초기화 실패: {e}[/red]")
        logger.error(f"챗봇 초기화 실패: {e}")


def save_conversation_to_markdown(conversation_log: list, filename: str):
    """대화 내용을 마크다운 파일로 저장합니다."""
    try:
        import datetime
        
        # 파일명 처리 (.md 확장자 추가)
        if not filename.endswith('.md'):
            filename += '.md'
        
        # 마크다운 내용 생성
        markdown_content = f"# AI 대화 기록\n\n"
        markdown_content += f"**생성일시**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        markdown_content += "---\n\n"
        
        for entry in conversation_log:
            markdown_content += entry + "\n"
        
        # 파일 저장
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        console.print(f"[green]✅ 대화 내용이 '{filename}' 파일에 저장되었습니다.[/green]")
        
    except Exception as e:
        console.print(f"[red]파일 저장 실패: {e}[/red]")
        logger.error(f"마크다운 저장 실패: {e}")

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