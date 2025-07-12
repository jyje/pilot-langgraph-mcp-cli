"""
채팅 명령어 비즈니스 로직
"""

import asyncio
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
    
    def __init__(self, openai_config: Dict, chatbot_config: Dict):
        """
        채팅 명령어 초기화
        
        Args:
            openai_config: OpenAI 설정
            chatbot_config: 챗봇 설정
        """
        self.openai_config = openai_config
        self.chatbot_config = chatbot_config
        self.agent_service = None
    
    async def _initialize_agent(self):
        """에이전트 서비스 초기화"""
        if self.agent_service is None:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True
            ) as progress:
                task = progress.add_task("에이전트 초기화 중...", total=None)
                self.agent_service = create_agent_service(self.openai_config, self.chatbot_config)
                progress.update(task, completed=100)
    
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
            user_input = console.input("[bold green]질문:[/bold green] ")
        
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
                user_input = console.input("[bold green]You:[/bold green] ")
                
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
            except Exception as e:
                console.print(f"[red]오류가 발생했습니다: {e}[/red]")
                logger.error(f"채팅 오류: {e}")
        
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
            console.print("🤖 AI: ", end="", style="bold cyan")
            
            try:
                response_started = False
                async for chunk in self.agent_service.chat_stream(user_input, conversation_state):
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
        else:
            # 기존 방식 (전체 응답 한 번에)
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True
            ) as progress:
                task = progress.add_task("AI가 답변을 생성하는 중...", total=None)
                
                # 비동기 호출
                ai_response = await self.agent_service.chat(user_input, conversation_state)
                progress.update(task, completed=100)
            
            # AI 응답 표시
            ai_panel = Panel(
                ai_response,
                title="🤖 AI",
                border_style="cyan"
            )
            console.print(ai_panel)
            console.print()
        
        return ai_response 