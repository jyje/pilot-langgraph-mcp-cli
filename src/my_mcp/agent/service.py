"""
LangGraph를 사용한 AI 에이전트 서비스
"""
from typing import Dict, Any, List, Optional
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
            
            logger.debug(f"AI 응답 생성: {ai_response[:100]}...")
            logger.debug(f"도구 호출 여부: {hasattr(response, 'tool_calls') and response.tool_calls}")
            
            return {
                "messages": messages,
                "ai_response": ai_response
            }
        
        except Exception as e:
            logger.error(f"AI 응답 생성 실패: {e}")
            error_message = "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다."
            
            return {
                "messages": messages + [AIMessage(content=error_message)],
                "ai_response": error_message
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
                return "call_tools"
        
        logger.debug("도구 호출 없음, 출력 포맷팅으로 이동")
        return "format_output"
    
    def _format_output(self, state: AgentState) -> Dict[str, Any]:
        """출력 포맷팅"""
        ai_response = state["ai_response"]
        
        # 마크다운 텍스트 줄 나눔 개선
        formatted_response = self._improve_line_breaks(ai_response)
        
        logger.debug("응답 포맷팅 완료")
        
        return {
            "ai_response": formatted_response
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
        
        # **굵은 텍스트** 앞뒤에 적절한 공백 추가
        text = re.sub(r'([^\s])\s*(\*\*[^*]+\*\*)', r'\1 \2', text)
        text = re.sub(r'(\*\*[^*]+\*\*)\s*([^\s])', r'\1 \2', text)
        
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
    
    async def chat(self, user_input: str, conversation_state: Optional[Dict] = None) -> str:
        """
        사용자 입력에 대한 AI 에이전트 응답 생성
        
        Args:
            user_input: 사용자 입력
            conversation_state: 대화 상태 (선택사항)
            
        Returns:
            AI 응답
        """
        try:
            # 초기 상태 설정
            initial_state = {
                "messages": conversation_state.get("messages", []) if conversation_state else [],
                "user_input": user_input,
                "system_prompt": self.system_prompt,
                "ai_response": ""
            }
            
            # 워크플로우 실행
            result = await self.app.ainvoke(initial_state)
            
            # 대화 상태 업데이트
            if conversation_state is not None:
                conversation_state["messages"] = result["messages"]
            
            return result["ai_response"]
            
        except Exception as e:
            logger.error(f"채팅 처리 실패: {e}")
            return "죄송합니다. 요청을 처리하는 중에 오류가 발생했습니다."
    
    async def chat_stream(self, user_input: str, conversation_state: Optional[Dict] = None):
        """
        사용자 입력에 대한 AI 에이전트 응답을 스트리밍으로 생성
        
        Args:
            user_input: 사용자 입력
            conversation_state: 대화 상태 (선택사항)
            
        Yields:
            AI 응답 청크
        """
        try:
            # 워크플로우를 통해 응답 생성 (도구 호출 포함)
            response = await self.chat(user_input, conversation_state)
            
            # 줄 나눔 개선 적용
            formatted_response = self._improve_line_breaks(response)
            
            # 응답을 청크로 나누어 스트리밍 시뮬레이션
            # 마크다운 구문을 고려한 스마트 분할
            import re
            
            # 마크다운 구문을 보호하면서 분할
            lines = formatted_response.split('\n')
            for line_idx, line in enumerate(lines):
                if line.strip():  # 빈 줄이 아닌 경우
                    # 마크다운 구문(**텍스트**)을 보호하면서 분할
                    tokens = self._smart_split_for_streaming(line)
                    for token_idx, token in enumerate(tokens):
                        if token_idx == 0:
                            yield token
                        else:
                            yield " " + token
                else:
                    # 빈 줄인 경우 빈 줄 출력 (단락 구분)
                    pass
                
                # 마지막 줄이 아닌 경우 줄 나눔 추가
                if line_idx < len(lines) - 1:
                    yield "\n"
                    
            logger.debug("스트리밍 응답 처리 완료")
            
        except Exception as e:
            logger.error(f"스트리밍 채팅 처리 실패: {e}")
            yield "죄송합니다. 요청을 처리하는 중에 오류가 발생했습니다."
    
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