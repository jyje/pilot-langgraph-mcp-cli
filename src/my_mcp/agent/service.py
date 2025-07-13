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
    
    def __init__(self, openai_config: Dict[str, Any], agent_config: Dict[str, Any]):
        """
        AI 에이전트 서비스 초기화
        
        Args:
            openai_config: OpenAI API 설정
            agent_config: 에이전트 설정
        """
        self.openai_config = openai_config
        self.agent_config = agent_config
        
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
            logger.info(f"도구 바인딩 완료: {len(self.tools)}개 도구")
        else:
            self.llm_with_tools = self.llm
            logger.info("사용 가능한 도구가 없습니다")
        
        # 도구 노드 생성
        self.tool_node = ToolNode(self.tools) if self.tools else None
        
        # LangGraph 워크플로우 생성
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile()
        
        # 시스템 프롬프트 설정
        self.system_prompt = agent_config["system_prompt"]
        
        logger.info(f"AI 에이전트 서비스 초기화 완료: {agent_config['name']}")
    
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
        
        # 필요에 따라 응답 포맷팅 로직 추가
        formatted_response = ai_response.strip()
        
        logger.debug("응답 포맷팅 완료")
        
        return {
            "ai_response": formatted_response
        }
    
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
            
            # 응답을 청크로 나누어 스트리밍 시뮬레이션
            words = response.split()
            for i, word in enumerate(words):
                if i == 0:
                    yield word
                else:
                    yield " " + word
                    
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
        return {
            "tools": self.tool_registry.get_tool_info(),
            "tool_count": self.tool_registry.get_tool_count()
        }

def create_agent_service(openai_config: Dict[str, Any], agent_config: Dict[str, Any]) -> AgentService:
    """
    AI 에이전트 서비스 인스턴스 생성
    
    Args:
        openai_config: OpenAI API 설정
        agent_config: 에이전트 설정
        
    Returns:
        AgentService 인스턴스
    """
    return AgentService(openai_config, agent_config) 