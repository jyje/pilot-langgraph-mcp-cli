"""
LangGraph를 사용한 챗봇 서비스
"""
import asyncio
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict
from .logging import get_logger

# 서비스 전용 로거 생성
logger = get_logger("my_mcp.service")

class ChatState(TypedDict):
    """채팅 상태를 나타내는 타입"""
    messages: Annotated[List[Any], add_messages]
    system_prompt: str
    user_input: str
    ai_response: str

class ChatbotService:
    """LangGraph 기반 챗봇 서비스"""
    
    def __init__(self, openai_config: Dict[str, Any], chatbot_config: Dict[str, Any]):
        """
        챗봇 서비스 초기화
        
        Args:
            openai_config: OpenAI API 설정
            chatbot_config: 챗봇 설정
        """
        self.openai_config = openai_config
        self.chatbot_config = chatbot_config
        self.llm = ChatOpenAI(
            api_key=openai_config["api_key"],
            model=openai_config["model"],
            temperature=openai_config["temperature"],
            max_tokens=openai_config["max_tokens"],
            streaming=openai_config.get("streaming", True)
        )
        
        # LangGraph 워크플로우 생성
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile()
        
        # 시스템 프롬프트 설정
        self.system_prompt = chatbot_config["system_prompt"]
        
        logger.info(f"챗봇 서비스 초기화 완료: {chatbot_config['name']}")
    
    def _create_workflow(self) -> StateGraph:
        """LangGraph 워크플로우 생성"""
        # 상태 그래프 생성
        workflow = StateGraph(ChatState)
        
        # 노드 추가
        workflow.add_node("process_input", self._process_input)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("format_output", self._format_output)
        
        # 엣지 추가
        workflow.add_edge("process_input", "generate_response")
        workflow.add_edge("generate_response", "format_output")
        workflow.add_edge("format_output", END)
        
        # 시작점 설정
        workflow.set_entry_point("process_input")
        
        return workflow
    
    def _process_input(self, state: ChatState) -> Dict[str, Any]:
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
    
    def _generate_response(self, state: ChatState) -> Dict[str, Any]:
        """AI 응답 생성"""
        messages = state["messages"]
        
        try:
            # LLM을 사용하여 응답 생성
            if self.llm.streaming:
                # 스트리밍 모드
                full_response = ""
                for chunk in self.llm.stream(messages):
                    if hasattr(chunk, 'content') and chunk.content:
                        full_response += chunk.content
                ai_response = full_response
            else:
                # 일반 모드
                response = self.llm.invoke(messages)
                ai_response = response.content
            
            # 응답을 메시지 목록에 추가
            messages.append(AIMessage(content=ai_response))
            
            logger.debug(f"AI 응답 생성: {ai_response[:100]}...")
            
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
    
    def _format_output(self, state: ChatState) -> Dict[str, Any]:
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
        사용자 입력에 대한 챗봇 응답 생성
        
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
        사용자 입력에 대한 챗봇 응답을 스트리밍으로 생성
        
        Args:
            user_input: 사용자 입력
            conversation_state: 대화 상태 (선택사항)
            
        Yields:
            AI 응답 청크
        """
        try:
            # 초기 상태 설정
            initial_state = {
                "messages": conversation_state.get("messages", []) if conversation_state else [],
                "user_input": user_input,
                "system_prompt": self.system_prompt,
                "ai_response": ""
            }
            
            # 직접 스트리밍 (LangGraph 워크플로우를 거치지 않고)
            messages = initial_state["messages"]
            
            # 첫 번째 메시지인 경우 시스템 프롬프트 추가
            if not messages:
                messages.append(SystemMessage(content=self.system_prompt))
            
            # 사용자 메시지 추가
            messages.append(HumanMessage(content=user_input))
            
            # 스트리밍 응답 생성 (로그 최소화)
            logger.debug("스트리밍 모드로 응답 생성 시작")
            full_response = ""
            chunk_count = 0
            async for chunk in self.llm.astream(messages):
                chunk_count += 1
                logger.debug(f"청크 {chunk_count}: {chunk}")
                if hasattr(chunk, 'content') and chunk.content:
                    content = chunk.content
                    logger.debug(f"응답 청크: '{content}'")
                    yield content
                    full_response += content
                else:
                    logger.debug(f"빈 청크 또는 content 없음: {chunk}")
            
            # 스트리밍 완료 후 로그 (줄 나눔 추가)
            logger.debug(f"스트리밍 완료 - 총 청크: {chunk_count}, 응답 길이: {len(full_response)}")
            
            # 대화 상태 업데이트
            if conversation_state is not None:
                # AI 응답을 메시지 목록에 추가
                messages.append(AIMessage(content=full_response))
                conversation_state["messages"] = messages
            
            logger.debug("스트리밍 응답 처리 완료")
            
        except Exception as e:
            logger.error(f"스트리밍 채팅 처리 실패: {e}")
            yield "죄송합니다. 요청을 처리하는 중에 오류가 발생했습니다."
    
    def get_welcome_message(self) -> str:
        """환영 메시지 반환"""
        return self.chatbot_config["welcome_message"]
    
    def get_chatbot_name(self) -> str:
        """챗봇 이름 반환"""
        return self.chatbot_config["name"]

def create_chatbot_service(openai_config: Dict[str, Any], chatbot_config: Dict[str, Any]) -> ChatbotService:
    """
    챗봇 서비스 인스턴스 생성
    
    Args:
        openai_config: OpenAI API 설정
        chatbot_config: 챗봇 설정
        
    Returns:
        ChatbotService 인스턴스
    """
    return ChatbotService(openai_config, chatbot_config) 