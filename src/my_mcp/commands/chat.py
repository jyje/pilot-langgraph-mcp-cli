"""
채팅 명령어 비즈니스 로직
"""

import asyncio
import sys
from typing import Dict, Optional
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..agent.service import create_agent_service
from ..utils.markdown_utils import save_conversation_to_markdown
from ..logging import get_logger

console = Console()
logger = get_logger("my_mcp.commands.chat")


class ChatCommand:
    """채팅 명령어 처리 클래스"""
    
    def __init__(self, openai_config: Dict, chatbot_config: Dict, mcp_servers: list = None):
        """
        채팅 명령어 초기화
        
        Args:
            openai_config: OpenAI 설정
            chatbot_config: 챗봇 설정
            mcp_servers: MCP 서버 설정 목록
        """
        self.openai_config = openai_config
        self.chatbot_config = chatbot_config
        self.mcp_servers = mcp_servers or []
        self.agent_service = None
    
    def _get_user_input(self, prompt: str) -> str:
        """
        사용자 입력을 받는 함수
        파이프 입력인 경우 프롬프트를 표시하지 않지만 입력 내용은 표시함
        
        Args:
            prompt: 터미널에서 표시할 프롬프트
            
        Returns:
            사용자 입력 문자열
        """
        if sys.stdin.isatty():
            # 터미널에서 직접 입력받는 경우
            return console.input(prompt)
        else:
            # 파이프 입력인 경우
            line = sys.stdin.readline()
            if not line:
                raise EOFError()
            user_input = line.rstrip('\n\r')
            # 파이프 입력 내용을 화면에 표시 (일관성을 위해 항상 "You:" 사용)
            console.print(f"[bold green]🧑 You:[/bold green] {user_input}")
            return user_input
    
    async def _initialize_agent(self):
        """에이전트 서비스 초기화"""
        if self.agent_service is None:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True
            ) as progress:
                task = progress.add_task("에이전트 초기화 중...", total=None)
                self.agent_service = create_agent_service(self.openai_config, self.chatbot_config, self.mcp_servers)
                progress.update(task, completed=100)
                
                # MCP 서버 연결 시도
                if self.mcp_servers:
                    connection_task = progress.add_task("MCP 서버 연결 중...", total=None)
                    connection_results = await self.agent_service.connect_mcp_servers()
                    progress.update(connection_task, completed=100)
                    
                    # 연결 결과 로그
                    connected_count = sum(1 for success in connection_results.values() if success)
                    logger.info(f"MCP 서버 연결 완료: {connected_count}/{len(self.mcp_servers)}개 성공")
    
    async def execute_once(self, question: str = None, no_stream: bool = False, save: str = None):
        """
        일회성 대화 모드 실행
        
        Args:
            question: 질문 내용
            no_stream: 스트리밍 모드 비활성화
            save: 저장할 파일명
        """
        await self._initialize_agent()
        
        # 마크다운 저장을 위한 대화 기록
        conversation_log = []
        
        # 간단한 환영 메시지 (일회성)
        console.print(f"[bold blue]🤖 {self.agent_service.get_agent_name()}[/bold blue]")
        console.print("[dim]일회성 대화 모드입니다.[/dim]")
        console.print()
        
        # 질문 결정
        if question:
            user_input = question
        else:
            # 사용자 입력 받기
            try:
                user_input = self._get_user_input("[bold green]🧑 You:[/bold green] ")
            except EOFError:
                logger.debug("EOF 발생으로 일회성 대화 모드 종료")
                return
            except KeyboardInterrupt:
                console.print("\n[yellow]대화가 취소되었습니다.[/yellow]")
                return
        
        # 빈 입력 처리
        if not user_input.strip():
            console.print("[yellow]질문을 입력해주세요.[/yellow]")
            return
        
        # 대화 상태 저장 (일회성이므로 빈 상태)
        conversation_state = {"messages": []}
        
        # 스트리밍 모드 확인 (옵션으로 재정의)
        streaming_enabled = self.openai_config.get("streaming", True) and not no_stream
        
        ai_response = await self._process_message(user_input, conversation_state, streaming_enabled)
        
        # 마크다운 저장 (일회성)
        if save:
            conversation_log.append(f"**사용자**: {user_input}\n")
            conversation_log.append(f"**AI**: {ai_response}\n")
            save_conversation_to_markdown(conversation_log, save)
    
    async def execute_continuous(self, no_stream: bool = False, save: str = None):
        """
        연속 대화 모드 실행
        
        Args:
            no_stream: 스트리밍 모드 비활성화
            save: 저장할 파일명
        """
        await self._initialize_agent()
        
        # 마크다운 저장을 위한 대화 기록
        conversation_log = []
        
        # 환영 메시지 표시
        welcome_panel = Panel(
            self.agent_service.get_welcome_message(),
            title=f"🤖 {self.agent_service.get_agent_name()}",
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
                user_input = self._get_user_input("[bold green]🧑 You:[/bold green] ")
                
                # 종료 명령어 확인
                if user_input.strip().lower() == "/bye":
                    console.print("[yellow]대화를 종료합니다. 안녕히 가세요! 👋[/yellow]")
                    break
                
                # 빈 입력 무시
                if not user_input.strip():
                    continue
                
                # 스트리밍 모드 확인 (옵션으로 재정의)
                streaming_enabled = self.openai_config.get("streaming", True) and not no_stream
                
                ai_response = await self._process_message(user_input, conversation_state, streaming_enabled)
                
                # 마크다운 저장을 위한 대화 기록
                if save:
                    conversation_log.append(f"**사용자**: {user_input}\n")
                    conversation_log.append(f"**AI**: {ai_response}\n")
                
            except KeyboardInterrupt:
                console.print("\n[yellow]대화를 종료합니다. 안녕히 가세요! 👋[/yellow]")
                break
            except EOFError:
                # EOF 발생 시 조용히 종료
                logger.debug("EOF 발생 - 연속 대화 모드 종료")
                break
            except Exception as e:
                console.print(f"[red]오류가 발생했습니다: {e}[/red]")
                logger.error(f"채팅 오류: {e}")
                # 연속적인 오류 방지를 위해 잠시 대기 후 계속
                continue
        
        # 연속 대화 모드 종료 시 마크다운 저장
        if save and conversation_log:
            save_conversation_to_markdown(conversation_log, save)
    
    async def _process_message(self, user_input: str, conversation_state: Dict, streaming_enabled: bool) -> str:
        """
        메시지 처리 (스트리밍 또는 일반 모드)
        
        Args:
            user_input: 사용자 입력
            conversation_state: 대화 상태
            streaming_enabled: 스트리밍 활성화 여부
            
        Returns:
            AI 응답
        """
        ai_response = ""
        
        if streaming_enabled:
            # AI 응답 스트리밍 생성
            try:
                response_started = False
                tool_calls_processed = False
                
                async for chunk in self.agent_service.chat_stream(user_input, conversation_state):
                    chunk_type = chunk.get("type", "text")
                    chunk_data = chunk.get("data", "")
                    
                    if chunk_type == "tool_calls" and not tool_calls_processed:
                        # 도구 호출 정보 처리
                        tool_calls_processed = True
                        if chunk_data:  # 도구 호출이 있는 경우
                            self._display_tool_usage_info(chunk_data)
                        # AI 응답 시작
                        console.print("🤖 AI: ", end="", style="bold cyan")
                        
                    elif chunk_type == "text":
                        if not response_started:
                            response_started = True
                        console.print(chunk_data, end="", style="white")
                        ai_response += chunk_data
                        
                    elif chunk_type == "error":
                        console.print(f"\n[red]스트리밍 오류: {chunk_data}[/red]")
                        ai_response = chunk_data
                        
                # 스트리밍 완료 후 줄 나눔 추가
                console.print("\n")
                
            except Exception as e:
                console.print(f"\n[red]스트리밍 오류: {e}[/red]")
                logger.error(f"스트리밍 오류: {e}")
                ai_response = "죄송합니다. 요청을 처리하는 중에 오류가 발생했습니다."
        else:
            # 기존 방식 (전체 응답 한 번에)
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True
            ) as progress:
                task = progress.add_task("AI가 답변을 생성하는 중...", total=None)
                
                # 비동기 호출 (수정된 반환 타입 처리)
                ai_response, tool_calls = await self.agent_service.chat(user_input, conversation_state)
                progress.update(task, completed=100)
            
            # 도구 사용 정보 표시
            if tool_calls:
                self._display_tool_usage_info(tool_calls)
            
            # AI 응답 표시
            ai_panel = Panel(
                ai_response,
                title="🤖 AI",
                border_style="cyan"
            )
            console.print(ai_panel)
            console.print()
        
        return ai_response
    
    def _display_tool_usage_info(self, tool_calls: list):
        """도구 사용 정보를 사용자에게 표시합니다."""
        if not tool_calls:
            return
            
        # 도구 사용 정보 패널 생성
        tool_info = self.agent_service.get_tool_usage_info(tool_calls)
        
        tool_panel = Panel(
            tool_info,
            title=f"🛠️ 도구 사용 정보 ({len(tool_calls)}개 도구)",
            border_style="yellow",
            padding=(0, 1)
        )
        console.print(tool_panel)
        console.print()  # 구분을 위한 빈 줄 