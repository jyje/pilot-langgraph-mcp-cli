"""
다이어그램 관련 유틸리티 함수들
"""

from langchain.schema import HumanMessage, SystemMessage
from ..logging import get_logger

logger = get_logger("my_mcp.utils.diagram")


def generate_ai_description_sync(agent_service, nodes, edges, tools=None) -> str:
    """
    AI를 이용해 그래프 구조 설명을 생성합니다. (동기 버전)
    
    Args:
        agent_service: 에이전트 서비스 인스턴스
        nodes: 그래프 노드 리스트
        edges: 그래프 엣지 리스트
        tools: 도구 리스트 (선택사항)
        
    Returns:
        AI가 생성한 설명
    """
    try:
        # 그래프 구조 정보 정리
        node_info = []
        for node in nodes:
            node_info.append(f"{node}")
        
        edge_info = []
        for edge in edges:
            if isinstance(edge, (list, tuple)) and len(edge) >= 2:
                edge_info.append(f"{edge[0]} → {edge[1]}")
        
        # 도구 정보 정리
        tool_info = []
        if tools:
            for tool in tools:
                tool_info.append(f"{tool['name']}: {tool['description']}")
        
        # AI에게 설명 생성 요청
        prompt = f"""다음 LangGraph 워크플로우에 대한 간단하고 명확한 설명을 한국어로 작성해주세요:

노드 (처리 단계):
{', '.join(node_info)}

연결 관계:
{', '.join(edge_info)}"""

        if tool_info:
            prompt += f"""

사용 가능한 도구:
{chr(10).join(tool_info)}"""

        prompt += """

요구사항:
- 2-3문장으로 간단하게 설명
- 워크플로우의 전체적인 흐름과 목적을 설명
- 사용 가능한 도구가 있다면 언급
- 기술적 용어보다는 이해하기 쉬운 표현 사용
- 설명만 반환하고 다른 내용은 포함하지 마세요"""

        # 직접 LLM 호출 (동기 방식)
        messages = [
            SystemMessage(content="당신은 워크플로우 설명을 작성하는 전문가입니다. 간단하고 명확한 설명을 제공해주세요."),
            HumanMessage(content=prompt)
        ]
        
        # LLM 직접 호출
        response = agent_service.llm.invoke(messages)
        description = response.content.strip()
        
        return description
        
    except Exception as e:
        logger.error(f"AI 설명 생성 실패: {e}")
        return "사용자 입력을 처리하고 AI가 응답을 생성한 후 적절한 형식으로 출력하는 워크플로우입니다."


def generate_mermaid_diagram(nodes, edges, tools=None, description=None, for_console=False) -> str:
    """
    LangGraph를 Mermaid 다이어그램으로 변환
    
    Args:
        nodes: 그래프 노드 리스트
        edges: 그래프 엣지 리스트
        tools: 도구 리스트 (선택사항)
        description: 설명 (선택사항)
        for_console: 콘솔 출력 여부
        
    Returns:
        Mermaid 다이어그램 문자열
    """
    try:
        # 노드와 엣지가 모두 비어있으면 오류
        if not nodes or not edges:
            raise ValueError("그래프 정보를 추출할 수 없습니다.")
        
        mermaid_lines = ["graph TD"]
        
        # 노드 정의
        for node in nodes:
            mermaid_lines.append(f'    {node}["{node}"]')
        
        # 도구 노드 추가
        if tools:
            for tool in tools:
                tool_name = tool["name"]
                mermaid_lines.append(f'    {tool_name}["{tool_name}"]')
        
        # 엣지 정의 (원본 이름 그대로 사용)
        for edge in edges:
            if isinstance(edge, (list, tuple)) and len(edge) >= 2:
                source, target = edge[0], edge[1]
                mermaid_lines.append(f"    {source} --> {target}")
        
        # call_tools 노드와 도구들 연결
        if tools and "call_tools" in nodes:
            for tool in tools:
                tool_name = tool["name"]
                mermaid_lines.append(f"    call_tools --> {tool_name}")
        
        # 스타일 추가 (글씨 검은색으로)
        mermaid_lines.extend([
            "",
            "    classDef startEnd fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000;",
            "    classDef process fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#000;",
            "    classDef generate fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px,color:#000;",
            "    classDef format fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000;",
            "    classDef tool fill:#fce4ec,stroke:#880e4f,stroke-width:2px,color:#000;",
            "",
            "    class __start__,__end__ startEnd",
            "    class process_input process",
            "    class generate_response generate", 
            "    class format_output format"
        ])
        
        # 도구 노드에 스타일 적용
        if tools:
            tool_names = [tool["name"] for tool in tools]
            mermaid_lines.append(f"    class {','.join(tool_names)} tool")
        
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