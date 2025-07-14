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
    
    async def execute_once(self, question: str = None, no_stream: bool = False, save: str = None, debug: bool = False):
        """
        일회성 대화 모드 실행
        
        Args:
            question: 질문 내용
            no_stream: 스트리밍 모드 비활성화
            save: 저장할 파일명
            debug: 디버그 모드 활성화
        """
        await self._initialize_agent()
        
        # 마크다운 저장을 위한 대화 기록
        conversation_log = []
        
        # 간단한 환영 메시지 (일회성)
        console.print(f"[bold blue]🤖 {self.agent_service.get_agent_name()}[/bold blue]")
        console.print("[dim]일회성 대화 모드입니다.[/dim]")
        if debug:
            console.print("[dim]디버그 모드가 활성화되었습니다.[/dim]")
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
        
        ai_response = await self._process_message(user_input, conversation_state, streaming_enabled, debug)
        
        # 마크다운 저장 (일회성)
        if save:
            conversation_log.append(f"**사용자**: {user_input}\n")
            conversation_log.append(f"**AI**: {ai_response}\n")
            save_conversation_to_markdown(conversation_log, save)
    
    async def execute_continuous(self, no_stream: bool = False, save: str = None, debug: bool = False):
        """
        연속 대화 모드 실행
        
        Args:
            no_stream: 스트리밍 모드 비활성화
            save: 저장할 파일명
            debug: 디버그 모드 활성화
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
        if debug:
            console.print("[dim]디버그 모드가 활성화되었습니다.[/dim]")
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
                
                ai_response = await self._process_message(user_input, conversation_state, streaming_enabled, debug)
                
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
    
    async def _process_message(self, user_input: str, conversation_state: Dict, streaming_enabled: bool, debug_mode: bool = False) -> str:
        """
        메시지 처리 (스트리밍 또는 일반 모드)
        
        Args:
            user_input: 사용자 입력
            conversation_state: 대화 상태
            streaming_enabled: 스트리밍 활성화 여부
            debug_mode: 디버그 모드 (모델 ID 표시 여부)
            
        Returns:
            AI 응답
        """
        ai_response = ""
        
        if streaming_enabled:
            # AI 응답 스트리밍 생성
            try:
                response_started = False
                current_tools = []
                
                async for chunk in self.agent_service.chat_stream(user_input, conversation_state, debug_mode):
                    chunk_type = chunk.get("type", "text")
                    chunk_data = chunk.get("data", "")
                    
                    if chunk_type == "workflow_step":
                        # 워크플로우 단계 표시 (디버그 모드에서만)
                        if debug_mode:
                            step = chunk_data.get("step", "")
                            status = chunk_data.get("status", "")
                            console.print(f"[dim]🔧 워크플로우: {step} - {status}[/dim]")
                    
                    elif chunk_type == "tools_pending":
                        # 도구 호출 예정 알림
                        tool_calls = chunk_data.get("tool_calls", [])
                        debug_mode_flag = chunk_data.get("debug_mode", False)
                        if tool_calls:
                            self._display_tools_pending(tool_calls, debug_mode_flag)
                            current_tools = tool_calls
                    
                    elif chunk_type == "tool_executing":
                        # 개별 도구 실행 중 상태 표시
                        tool_name = chunk_data.get("tool_name", "unknown")
                        self._display_tool_executing(tool_name, current_tools, debug_mode)
                    
                    elif chunk_type == "ai_response_ready":
                        # AI 응답 준비 완료 (도구 실행 후)
                        console.print("[green]✅ 도구 실행 완료[/green]")
                        console.print("🤖 AI: ", end="", style="bold cyan")
                        response_started = True
                    
                    elif chunk_type == "text":
                        # 텍스트 청크 처리
                        if not response_started:
                            # 도구 호출 없이 직접 응답하는 경우
                            console.print("🤖 AI: ", end="", style="bold cyan")
                            response_started = True
                        
                        console.print(chunk_data, end="", style="white")
                        ai_response += chunk_data
                        
                    elif chunk_type == "streaming_complete":
                        # 스트리밍 완료
                        final_response = chunk_data.get("final_response", "")
                        if final_response and not ai_response:
                            ai_response = final_response
                        break
                        
                    elif chunk_type == "error":
                        console.print(f"\n[red]스트리밍 오류: {chunk_data}[/red]")
                        ai_response = chunk_data
                        break
                        
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
                self._display_tool_usage_info(tool_calls, debug_mode)
            
            # AI 응답 표시
            ai_panel = Panel(
                ai_response,
                title="🤖 AI",
                border_style="cyan"
            )
            console.print(ai_panel)
            console.print()
        
        return ai_response
    
    def _display_tools_pending(self, tool_calls: list, debug_mode: bool = False):
        """예정된 도구 호출 정보를 표시합니다."""
        if not tool_calls:
            return
            
        console.print(f"[yellow]🛠️  {len(tool_calls)}개 도구 실행 예정...[/yellow]")
        
        for i, tool_call in enumerate(tool_calls, 1):
            tool_name = tool_call.get("name", "unknown")
            tool_args = tool_call.get("args", {})
            tool_id = tool_call.get("id", "unknown")
            
            # 도구 이름을 친숙하게 표시
            display_name = self.agent_service._format_tool_display_name(tool_name)
            
            # 파라미터 요약
            param_summary = self.agent_service._format_tool_parameters(tool_args)
            
            console.print(f"[dim]   {i}. {display_name}[/dim]")
            if param_summary and param_summary != "없음":
                console.print(f"[dim]      파라미터: {param_summary}[/dim]")
            
            # 디버그 모드에서만 모델 ID 표시
            if debug_mode:
                console.print(f"[dim]      ID: {tool_id}[/dim]")
        
        console.print()
    
    def _display_tool_executing(self, tool_name: str, current_tools: list, debug_mode: bool = False):
        """도구 실행 중 상태를 표시합니다."""
        display_name = self.agent_service._format_tool_display_name(tool_name)
        
        # 현재 도구 목록에서 해당 도구 찾기
        tool_description = None
        for tool in current_tools:
            if tool.get("name") == tool_name:
                tool_description = self.agent_service._get_tool_description(tool_name)
                break
        
        console.print(f"[blue]⚡ 실행 중: {display_name}[/blue]")
        if tool_description and tool_description != '도구 설명이 없습니다':
            console.print(f"[dim]   {tool_description}[/dim]")
        console.print()
    
    def _display_tool_usage_info(self, tool_calls: list, debug_mode: bool = False):
        """도구 사용 정보를 사용자에게 표시합니다 (비스트리밍 모드용)."""
        if not tool_calls:
            return
            
        # 도구 사용 정보 패널 생성
        info_parts = []
        
        for i, tool_call in enumerate(tool_calls, 1):
            tool_name = tool_call.get("name", "unknown")
            tool_args = tool_call.get("args", {})
            tool_id = tool_call.get("id", "unknown")
            
            # 도구 이름을 친숙하게 표시
            display_name = self.agent_service._format_tool_display_name(tool_name)
            
            # 도구 설명 가져오기
            tool_description = self.agent_service._get_tool_description(tool_name)
            
            # 파라미터 요약
            param_summary = self.agent_service._format_tool_parameters(tool_args)
            
            info_parts.append(f"**{i}. {display_name}**")
            if tool_description and tool_description != '도구 설명이 없습니다':
                info_parts.append(f"   - 설명: {tool_description}")
            if param_summary:
                info_parts.append(f"   - 파라미터: {param_summary}")
            
            # 디버그 모드에서만 모델 ID 표시
            if debug_mode:
                info_parts.append(f"   - 도구 ID: `{tool_id}`")
        
        tool_info = "\n".join(info_parts)
        tool_panel = Panel(
            tool_info,
            title=f"🛠️ 도구 사용 정보 ({len(tool_calls)}개 도구)",
            border_style="yellow",
            padding=(0, 1)
        )
        console.print(tool_panel)
        console.print()  # 구분을 위한 빈 줄 