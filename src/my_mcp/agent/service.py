"""
LangGraph를 사용한 AI 에이전트 서비스
"""
from typing import Dict, Any, List, Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain_core.messages import ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import Annotated, TypedDict
from ..logging import get_logger
from ..tools import get_tool_registry
from ..mcp import mcp_registry, mcp_client_manager

# 서비스 전용 로거 생성
logger = get_logger("my_mcp.agent.service")

class AgentState(TypedDict):
    """에이전트 상태를 나타내는 타입"""
    messages: Annotated[List[Any], add_messages]
    system_prompt: str
    user_input: str
    ai_response: str
    tool_calls: List[Dict[str, Any]]  # 도구 호출 정보 저장

class AgentService:
    """LangGraph 기반 AI 에이전트 서비스"""
    
    def __init__(self, openai_config: Dict[str, Any], agent_config: Dict[str, Any], mcp_servers: List[Dict[str, Any]] = None):
        """
        AI 에이전트 서비스 초기화
        
        Args:
            openai_config: OpenAI API 설정
            agent_config: 에이전트 설정
            mcp_servers: MCP 서버 설정 목록
        """
        self.openai_config = openai_config
        self.agent_config = agent_config
        
        # MCP 서버 초기화
        self.mcp_servers = mcp_servers or []
        self._initialize_mcp_servers()
        
        # 도구 레지스트리 초기화
        self.tool_registry = get_tool_registry()
        self.tools = self.tool_registry.get_enabled_tools()
        
        # LLM 초기화 (도구 바인딩 포함)
        self.llm = ChatOpenAI(
            api_key=openai_config["api_key"],
            model=openai_config["model"],
            temperature=openai_config["temperature"],
            max_tokens=openai_config["max_tokens"],
            streaming=openai_config.get("streaming", True)
        )
        
        # LLM에 도구 바인딩
        if self.tools:
            self.llm_with_tools = self.llm.bind_tools(self.tools)
            logger.debug(f"도구 바인딩 완료: {len(self.tools)}개 도구")
        else:
            self.llm_with_tools = self.llm
            logger.debug("사용 가능한 도구가 없습니다")
        
        # 도구 노드 생성
        self.tool_node = ToolNode(self.tools) if self.tools else None
        
        # LangGraph 워크플로우 생성
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile()
        
        # 시스템 프롬프트 설정
        self.system_prompt = agent_config["system_prompt"]
        
        logger.debug(f"AI 에이전트 서비스 초기화 완료: {agent_config['name']}")
    
    def _initialize_mcp_servers(self) -> None:
        """MCP 서버 초기화"""
        if not self.mcp_servers:
            logger.debug("MCP 서버 설정이 없습니다")
            return
            
        try:
            # MCP 레지스트리에 서버 로드
            mcp_registry.load_from_config(self.mcp_servers)
            
            # 공식 MCP 관리자에 서버 설정
            servers = mcp_registry.get_enabled_servers()
            mcp_client_manager.set_servers(servers)
            
            logger.info(f"MCP 서버 초기화 완료: {len(self.mcp_servers)}개 서버")
            
        except Exception as e:
            logger.error(f"MCP 서버 초기화 실패: {e}")
    
    async def connect_mcp_servers(self) -> Dict[str, bool]:
        """MCP 서버들에 연결"""
        try:
            # 공식 MCP 관리자 초기화
            success = await mcp_client_manager.initialize()
            
            if success:
                # MCP 도구 통합
                await self._integrate_mcp_tools()
                
                # 연결 성공한 서버 목록
                servers = mcp_registry.get_enabled_servers()
                connection_results = {server.name: True for server in servers}
                logger.info(f"MCP 서버 연결 성공: {len(servers)}개 서버")
                
                return connection_results
            else:
                logger.error("MCP 서버 연결 실패")
                return {}
                
        except Exception as e:
            logger.error(f"MCP 서버 연결 오류: {e}")
            return {}
    
    async def _integrate_mcp_tools(self) -> None:
        """MCP 도구를 기존 도구 목록에 통합"""
        try:
            # 공식 라이브러리에서 도구 가져오기
            mcp_tools = mcp_client_manager.get_tools()
            
            if mcp_tools:
                # 기존 도구와 MCP 도구를 합치기
                combined_tools = list(self.tools) + mcp_tools
                self.tools = combined_tools
                
                # LLM에 다시 바인딩
                self.llm_with_tools = self.llm.bind_tools(self.tools)
                
                # 도구 노드 다시 생성
                self.tool_node = ToolNode(self.tools)
                
                # 워크플로우 재생성
                self.workflow = self._create_workflow()
                self.app = self.workflow.compile()
                
                logger.info(f"MCP 도구 통합 완료: {len(mcp_tools)}개 도구 추가")
                
        except Exception as e:
            logger.error(f"MCP 도구 통합 오류: {e}")
    
    async def disconnect_mcp_servers(self) -> None:
        """MCP 서버들 연결 해제"""
        await mcp_client_manager.close()
        logger.info("모든 MCP 서버 연결 해제 완료")
    
    def _create_workflow(self) -> StateGraph:
        """LangGraph 워크플로우 생성"""
        # 상태 그래프 생성
        workflow = StateGraph(AgentState)
        
        # 노드 추가
        workflow.add_node("process_input", self._process_input)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("format_output", self._format_output)
        
        # 도구 사용 시 도구 노드 추가
        if self.tool_node:
            workflow.add_node("call_tools", self.tool_node)
        
        # 엣지 추가
        workflow.add_edge("process_input", "generate_response")
        
        # 도구 사용 여부에 따른 조건부 엣지 추가
        if self.tool_node:
            workflow.add_conditional_edges(
                "generate_response",
                self._should_call_tools,
                {
                    "call_tools": "call_tools",
                    "format_output": "format_output"
                }
            )
            workflow.add_edge("call_tools", "generate_response")
        else:
            workflow.add_edge("generate_response", "format_output")
        
        workflow.add_edge("format_output", END)
        
        # 시작점 설정
        workflow.set_entry_point("process_input")
        
        return workflow
    
    def _process_input(self, state: AgentState) -> Dict[str, Any]:
        """사용자 입력 처리"""
        user_input = state.get("user_input", "")
        
        # 메시지 목록에 사용자 입력 추가
        messages = state.get("messages", [])
        
        # 첫 번째 메시지인 경우 시스템 프롬프트 추가
        if not messages:
            messages.append(SystemMessage(content=self.system_prompt))
        
        # 사용자 메시지 추가
        messages.append(HumanMessage(content=user_input))
        
        logger.debug(f"사용자 입력 처리: {user_input}")
        
        return {
            "messages": messages,
            "user_input": user_input,
            "system_prompt": self.system_prompt
        }
    
    def _generate_response(self, state: AgentState) -> Dict[str, Any]:
        """AI 응답 생성"""
        messages = state["messages"]
        
        try:
            # 도구 바인딩된 LLM을 사용하여 응답 생성
            response = self.llm_with_tools.invoke(messages)
            
            # 응답을 메시지 목록에 추가
            messages.append(response)
            
            # 응답 내용 추출
            ai_response = response.content if response.content else ""
            
            # 도구 호출 정보 추출 (다양한 방법으로 시도)
            tool_calls = []
            
            # 방법 1: response.tool_calls 확인
            if hasattr(response, 'tool_calls') and response.tool_calls:
                logger.debug(f"tool_calls 속성 발견: {response.tool_calls}")
                for tool_call in response.tool_calls:
                    tool_info = {
                        "id": getattr(tool_call, 'id', str(tool_call.get('id', 'unknown'))),
                        "name": getattr(tool_call, 'name', tool_call.get('name', 'unknown')),
                        "args": getattr(tool_call, 'args', tool_call.get('args', {})),
                        "type": getattr(tool_call, 'type', tool_call.get('type', 'function'))
                    }
                    tool_calls.append(tool_info)
            
            # 방법 2: additional_kwargs 확인
            elif hasattr(response, 'additional_kwargs') and response.additional_kwargs:
                additional_kwargs = response.additional_kwargs
                logger.debug(f"additional_kwargs 확인: {additional_kwargs}")
                if 'tool_calls' in additional_kwargs:
                    for tool_call in additional_kwargs['tool_calls']:
                        tool_info = {
                            "id": tool_call.get('id', 'unknown'),
                            "name": tool_call.get('function', {}).get('name', 'unknown'),
                            "args": tool_call.get('function', {}).get('arguments', {}),
                            "type": tool_call.get('type', 'function')
                        }
                        tool_calls.append(tool_info)
            
            # 방법 3: 메시지 히스토리에서 도구 호출 확인
            if not tool_calls:
                # 최근 메시지들을 확인하여 도구 호출 찾기
                for msg in reversed(messages[-5:]):  # 최근 5개 메시지만 확인
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        logger.debug(f"메시지 히스토리에서 도구 호출 발견: {msg.tool_calls}")
                        for tool_call in msg.tool_calls:
                            tool_info = {
                                "id": getattr(tool_call, 'id', str(tool_call.get('id', 'unknown'))),
                                "name": getattr(tool_call, 'name', tool_call.get('name', 'unknown')),
                                "args": getattr(tool_call, 'args', tool_call.get('args', {})),
                                "type": getattr(tool_call, 'type', tool_call.get('type', 'function'))
                            }
                            tool_calls.append(tool_info)
                        break
            
            # 디버그 로그 추가
            logger.debug(f"AI 응답 생성: {ai_response[:100]}...")
            logger.debug(f"도구 호출 정보 추출 결과: {tool_calls}")
            logger.debug(f"응답 타입: {type(response)}")
            logger.debug(f"응답 속성: {dir(response)}")
            
            return {
                "messages": messages,
                "ai_response": ai_response,
                "tool_calls": tool_calls
            }
        
        except Exception as e:
            logger.error(f"AI 응답 생성 실패: {e}")
            error_message = "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다."
            
            return {
                "messages": messages + [AIMessage(content=error_message)],
                "ai_response": error_message,
                "tool_calls": []
            }
    
    def _should_call_tools(self, state: AgentState) -> str:
        """도구 호출 여부 결정"""
        messages = state["messages"]
        
        # 마지막 메시지가 도구 호출인지 확인
        if messages:
            last_message = messages[-1]
            # AIMessage에서 tool_calls 확인
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                logger.debug(f"도구 호출 감지: {last_message.tool_calls}")
                
                # 도구 호출 정보를 상태에 저장
                tool_calls = []
                for tool_call in last_message.tool_calls:
                    tool_info = {
                        "id": getattr(tool_call, 'id', str(tool_call.get('id', 'unknown'))),
                        "name": getattr(tool_call, 'name', tool_call.get('name', 'unknown')),
                        "args": getattr(tool_call, 'args', tool_call.get('args', {})),
                        "type": getattr(tool_call, 'type', tool_call.get('type', 'function'))
                    }
                    tool_calls.append(tool_info)
                
                # 상태 업데이트
                state["tool_calls"] = tool_calls
                logger.debug(f"도구 호출 정보 상태에 저장: {tool_calls}")
                
                return "call_tools"
        
        logger.debug("도구 호출 없음, 출력 포맷팅으로 이동")
        return "format_output"
    
    def _format_output(self, state: AgentState) -> Dict[str, Any]:
        """출력 포맷팅"""
        ai_response = state["ai_response"]
        tool_calls = state.get("tool_calls", [])
        
        # 마크다운 텍스트 줄 나눔 개선
        formatted_response = self._improve_line_breaks(ai_response)
        
        logger.debug("응답 포맷팅 완료")
        
        return {
            "ai_response": formatted_response,
            "tool_calls": tool_calls
        }
    
    def _improve_line_breaks(self, text: str) -> str:
        """마크다운 텍스트의 줄 나눔을 개선합니다."""
        if not text:
            return text
        
        # 기본 텍스트 정리
        text = text.strip()
        
        # 마크다운 헤더 앞뒤에 빈 줄 추가
        import re
        
        # ###, ##, # 헤더 앞뒤에 빈 줄 추가
        text = re.sub(r'([^\n])\n(#{1,6}\s)', r'\1\n\n\2', text)
        text = re.sub(r'(#{1,6}[^\n]*)\n([^\n#])', r'\1\n\n\2', text)
        
        # 목록 항목 (-로 시작하는 줄) 앞에 줄 나눔 추가
        text = re.sub(r'([^\n])\n(-\s\*\*)', r'\1\n\n\2', text)
        text = re.sub(r'([^\n])\n(-\s)', r'\1\n\2', text)
        
        # **굵은 텍스트** 앞뒤에 적절한 공백 추가 (줄바꿈 보존)
        # 줄바꿈이 아닌 문자 뒤에 오는 굵은 텍스트 앞에 공백 추가
        text = re.sub(r'([^\s\n])\s*(\*\*[^*]+\*\*)', r'\1 \2', text)
        # 굵은 텍스트 뒤에 오는 줄바꿈이 아닌 문자 앞에 공백 추가
        text = re.sub(r'(\*\*[^*]+\*\*)\s*([^\s\n])', r'\1 \2', text)
        
        # **굵은 텍스트** 뒤에 줄바꿈 없이 바로 이어지는 항목들을 분리
        text = re.sub(r'(\*\*[^*]+\*\*)\s*(\*\*[^*]+\*\*)', r'\1\n\n\2', text)
        
        # 연속된 빈 줄을 하나로 통합
        text = re.sub(r'\n\n\n+', '\n\n', text)
        
        return text
    
    def _smart_split_for_streaming(self, text: str) -> list:
        """마크다운 구문을 보호하면서 텍스트를 분할합니다."""
        import re
        
        # 마크다운 구문을 보호하면서 분할
        # **텍스트**와 같은 패턴은 하나의 토큰으로 유지
        pattern = r'(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|[^\s]+)'
        
        # 패턴에 따라 토큰들을 분할
        tokens = re.findall(pattern, text)
        
        # 빈 토큰 제거
        result = [token for token in tokens if token.strip()]
        
        return result
    
    def _format_tool_display_name(self, tool_name: str) -> str:
        """도구 이름을 사용자에게 친숙하게 표시하기 위해 포맷팅합니다."""
        display_name = tool_name
        
        # MCP 도구의 경우 prefix 제거
        if tool_name.startswith("mcp_"):
            display_name = tool_name[4:]  # "mcp_" 제거
        
        # 언더스코어를 공백으로 변환하고 제목 형식으로 변환
        display_name = display_name.replace("_", " ").title()
        
        # 일반적인 약어들은 대문자로 유지
        common_abbreviations = ["Api", "Url", "Id", "Uuid", "Json", "Xml", "Http", "Https"]
        for abbr in common_abbreviations:
            display_name = display_name.replace(abbr, abbr.upper())
        
        return display_name

    def _format_tool_usage_info(self, tool_calls: List[Dict[str, Any]]) -> str:
        """도구 사용 정보를 포맷팅합니다."""
        if not tool_calls:
            return ""
        
        info_parts = []
        
        for i, tool_call in enumerate(tool_calls, 1):
            tool_name = tool_call.get("name", "unknown")
            tool_args = tool_call.get("args", {})
            tool_id = tool_call.get("id", "unknown")
            
            # 도구 이름을 친숙하게 표시
            display_name = self._format_tool_display_name(tool_name)
            
            # 도구 설명 가져오기
            tool_description = self._get_tool_description(tool_name)
            
            # 파라미터 요약
            param_summary = self._format_tool_parameters(tool_args)
            
            info_parts.append(f"**{i}. {display_name}**")
            if tool_description and tool_description != '도구 설명이 없습니다':
                info_parts.append(f"   - 설명: {tool_description}")
            if param_summary:
                info_parts.append(f"   - 파라미터: {param_summary}")
            info_parts.append(f"   - 도구 ID: `{tool_id}`")
        
        return "\n".join(info_parts)
    
    def _get_tool_description(self, tool_name: str) -> str:
        """도구 설명을 동적으로 가져옵니다."""
        # 1. 기본 도구 레지스트리에서 도구 정보 가져오기
        for tool in self.tools:
            if getattr(tool, 'name', None) == tool_name:
                # LangChain 도구의 description 속성 사용
                description = getattr(tool, 'description', None)
                if description:
                    return description
                
                # func 속성의 __doc__ 사용
                if hasattr(tool, 'func') and hasattr(tool.func, '__doc__') and tool.func.__doc__:
                    return tool.func.__doc__.strip()
                
                break
        
        # 2. MCP 도구의 경우 MCP 클라이언트에서 도구 정보 가져오기
        try:
            mcp_tool_info = mcp_client_manager.get_tool_info()
            if tool_name in mcp_tool_info:
                tool_info = mcp_tool_info[tool_name]
                if isinstance(tool_info, dict):
                    return tool_info.get('description', '도구 설명이 없습니다')
                elif hasattr(tool_info, 'description'):
                    return tool_info.description
        except Exception as e:
            logger.debug(f"MCP 도구 정보 가져오기 실패: {e}")
        
        # 3. 도구 레지스트리에서 메타데이터 가져오기
        try:
            tool_registry_info = self.tool_registry.get_tool_info()
            for tool_info in tool_registry_info:
                if tool_info.get('name') == tool_name:
                    return tool_info.get('description', '도구 설명이 없습니다')
        except Exception as e:
            logger.debug(f"도구 레지스트리 정보 가져오기 실패: {e}")
        
        # 4. 기본값 반환
        return '도구 설명이 없습니다'
    
    def _format_tool_parameters(self, args: Dict[str, Any]) -> str:
        """도구 파라미터를 포맷팅합니다."""
        if not args:
            return "없음"
        
        param_parts = []
        for key, value in args.items():
            if isinstance(value, str) and len(value) > 50:
                # 긴 문자열은 잘라서 표시
                param_parts.append(f"{key}=\"{value[:50]}...\"")
            else:
                param_parts.append(f"{key}={value}")
        
        return ", ".join(param_parts)

    async def chat(self, user_input: str, conversation_state: Optional[Dict] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """
        사용자 입력에 대한 AI 에이전트 응답 생성
        
        Args:
            user_input: 사용자 입력
            conversation_state: 대화 상태 (선택사항)
            
        Returns:
            AI 응답과 도구 호출 정보의 튜플
        """
        try:
            # 초기 상태 설정
            initial_state = {
                "messages": conversation_state.get("messages", []) if conversation_state else [],
                "user_input": user_input,
                "system_prompt": self.system_prompt,
                "ai_response": "",
                "tool_calls": []
            }
            
            # 워크플로우 실행
            result = await self.app.ainvoke(initial_state)
            
            # 대화 상태 업데이트
            if conversation_state is not None:
                conversation_state["messages"] = result["messages"]
            
            return result["ai_response"], result.get("tool_calls", [])
            
        except Exception as e:
            logger.error(f"채팅 처리 실패: {e}")
            return "죄송합니다. 요청을 처리하는 중에 오류가 발생했습니다.", []
    
    async def chat_stream_with_workflow(self, user_input: str, conversation_state: Optional[Dict] = None, debug_mode: bool = False):
        """
        워크플로우 단계별 실행과 함께 스트리밍 응답 생성
        
        Args:
            user_input: 사용자 입력
            conversation_state: 대화 상태 (선택사항)
            debug_mode: 디버그 모드 (모델 ID 표시 여부)
            
        Yields:
            워크플로우 단계별 정보와 응답 청크
        """
        try:
            # 초기 상태 설정
            initial_state = {
                "messages": conversation_state.get("messages", []) if conversation_state else [],
                "user_input": user_input,
                "system_prompt": self.system_prompt,
                "ai_response": "",
                "tool_calls": []
            }
            
            # 상태 추적 변수
            tools_displayed = False
            final_response_started = False
            
            # 워크플로우 스트리밍 실행
            async for chunk in self.app.astream(initial_state):
                # 각 노드 실행 상태 확인
                for node_name, node_state in chunk.items():
                    if node_name == "generate_response":
                        # AI 응답 생성 시작
                        if debug_mode:
                            yield {"type": "workflow_step", "data": {"step": "generate_response", "status": "started"}}
                        
                        # 도구 호출 정보 확인 (첫 번째 generate_response에서만)
                        tool_calls = node_state.get("tool_calls", [])
                        if tool_calls and not tools_displayed:
                            # 도구 호출 예정 알림
                            yield {"type": "tools_pending", "data": {"tool_calls": tool_calls, "debug_mode": debug_mode}}
                            tools_displayed = True
                        
                        # AI 응답이 시작된 경우 (도구 호출 후 두 번째 generate_response)
                        ai_response = node_state.get("ai_response", "")
                        if ai_response and not final_response_started:
                            final_response_started = True
                            yield {"type": "ai_response_ready", "data": {"response": ai_response}}
                    
                    elif node_name == "call_tools":
                        # 도구 실행 시작
                        if debug_mode:
                            yield {"type": "workflow_step", "data": {"step": "call_tools", "status": "started"}}
                        
                        # 메시지에서 도구 호출 정보 추출
                        messages = node_state.get("messages", [])
                        if messages:
                            # 도구 호출 메시지 찾기
                            for msg in reversed(messages):
                                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                    # 개별 도구 실행 상태 표시
                                    for tool_call in msg.tool_calls:
                                        tool_name = getattr(tool_call, 'name', tool_call.get('name', 'unknown'))
                                        yield {"type": "tool_executing", "data": {"tool_name": tool_name}}
                                    break
                        
                        # 도구 실행 완료
                        if debug_mode:
                            yield {"type": "workflow_step", "data": {"step": "call_tools", "status": "completed"}}
                    
                    elif node_name == "format_output":
                        # 출력 포맷팅
                        if debug_mode:
                            yield {"type": "workflow_step", "data": {"step": "format_output", "status": "started"}}
                        
                        # 최종 응답 포맷팅 및 스트리밍
                        ai_response = node_state.get("ai_response", "")
                        if ai_response:
                            # 대화 상태 업데이트
                            if conversation_state is not None:
                                conversation_state["messages"] = node_state.get("messages", [])
                            
                            # 포맷팅된 응답 스트리밍
                            formatted_response = self._improve_line_breaks(ai_response)
                            lines = formatted_response.split('\n')
                            
                            for line_idx, line in enumerate(lines):
                                if line.strip():
                                    tokens = self._smart_split_for_streaming(line)
                                    for token_idx, token in enumerate(tokens):
                                        if token_idx == 0:
                                            yield {"type": "text", "data": token}
                                        else:
                                            yield {"type": "text", "data": " " + token}
                                if line_idx < len(lines) - 1:
                                    yield {"type": "text", "data": "\n"}
                            
                            # 스트리밍 완료
                            yield {"type": "streaming_complete", "data": {"final_response": formatted_response}}
                            return
            
            logger.debug("워크플로우 스트리밍 완료")
            
        except Exception as e:
            logger.error(f"워크플로우 스트리밍 실패: {e}")
            yield {"type": "error", "data": "죄송합니다. 요청을 처리하는 중에 오류가 발생했습니다."}

    async def chat_stream(self, user_input: str, conversation_state: Optional[Dict] = None, debug_mode: bool = False):
        """
        사용자 입력에 대한 AI 에이전트 응답을 스트리밍으로 생성
        
        Args:
            user_input: 사용자 입력
            conversation_state: 대화 상태 (선택사항)
            debug_mode: 디버그 모드 (모델 ID 표시 여부)
            
        Yields:
            AI 응답 청크 (워크플로우 단계별 정보 포함)
        """
        # 새로운 워크플로우 스트리밍 방식 사용
        async for chunk in self.chat_stream_with_workflow(user_input, conversation_state, debug_mode):
            yield chunk

    def get_tool_usage_info(self, tool_calls: List[Dict[str, Any]]) -> str:
        """도구 사용 정보를 포맷팅된 문자열로 반환합니다."""
        return self._format_tool_usage_info(tool_calls)
    
    def get_welcome_message(self) -> str:
        """환영 메시지 반환"""
        return self.agent_config["welcome_message"]
    
    def get_agent_name(self) -> str:
        """에이전트 이름 반환"""
        return self.agent_config["name"]
    
    def get_tool_info(self) -> Dict[str, Any]:
        """도구 정보 반환"""
        tool_info = {
            "tools": self.tool_registry.get_tool_info(),
            "count": self.tool_registry.get_tool_count(),
            "mcp_tools": mcp_client_manager.get_tool_info(),
            "mcp_servers": [server.to_dict() for server in mcp_registry.get_all_servers()]
        }
        return tool_info

def create_agent_service(openai_config: Dict[str, Any], agent_config: Dict[str, Any], mcp_servers: List[Dict[str, Any]] = None) -> AgentService:
    """
    AI 에이전트 서비스 인스턴스 생성
    
    Args:
        openai_config: OpenAI API 설정
        agent_config: 에이전트 설정
        mcp_servers: MCP 서버 설정 목록
        
    Returns:
        AgentService 인스턴스
    """
    return AgentService(openai_config, agent_config, mcp_servers) 