"""
그래프 내보내기 명령어 비즈니스 로직
"""

import json
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..agent.service import create_agent_service
from ..utils.diagram_utils import generate_ai_description_sync, generate_mermaid_diagram
from ..logging import get_logger

console = Console()
logger = get_logger("my_mcp.commands.export")


class ExportCommand:
    """그래프 내보내기 명령어 처리 클래스"""
    
    def __init__(self, openai_config: dict, chatbot_config: dict, mcp_servers: list = None):
        """
        그래프 내보내기 명령어 초기화
        
        Args:
            openai_config: OpenAI 설정
            chatbot_config: 챗봇 설정
            mcp_servers: MCP 서버 설정 목록
        """
        self.openai_config = openai_config
        self.chatbot_config = chatbot_config
        self.mcp_servers = mcp_servers or []
    
    def execute(self, format: str = "mermaid", output: str = None, ai_description: bool = False):
        """
        그래프 내보내기 명령어 실행
        
        Args:
            format: 출력 형식 (mermaid, json)
            output: 출력 파일 경로
            ai_description: AI 설명 생성 여부
        """
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
            # 챗봇 서비스 생성
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True
            ) as progress:
                task = progress.add_task("에이전트 서비스 초기화 중...", total=None)
                agent_service = create_agent_service(self.openai_config, self.chatbot_config, self.mcp_servers)
                
                # MCP 서버 연결 (비동기)
                import asyncio
                if self.mcp_servers:
                    connection_results = asyncio.run(agent_service.connect_mcp_servers())
                    logger.debug(f"MCP 서버 연결 결과: {connection_results}")
                
                progress.update(task, completed=100)
            
            # 성공 메시지 출력
            logger.debug("✅ 에이전트 서비스 초기화 완료")
            
            # 그래프 구조 가져오기
            nodes, edges, tools = self._extract_graph_structure(agent_service)
            
            # AI 설명 생성
            description = None
            if ai_description:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    transient=True
                ) as progress:
                    task = progress.add_task("AI가 그래프 구조 설명을 생성하는 중...", total=None)
                    description = generate_ai_description_sync(agent_service, nodes, edges, tools)
                    progress.update(task, completed=100)
                
                # 성공 메시지 출력
                logger.debug("✅ AI 설명 생성 완료")
            
            # 형식에 따라 내보내기
            if format.lower() == "mermaid":
                self._export_mermaid(nodes, edges, tools, description, output)
            elif format.lower() == "json":
                self._export_json(nodes, edges, tools, description, output)
            else:
                console.print(f"[red]지원되지 않는 형식입니다: {format}[/red]")
                console.print("지원되는 형식: mermaid, json")
                
        except Exception as e:
            console.print(f"[red]그래프 내보내기 실패: {e}[/red]")
            logger.error(f"그래프 내보내기 실패: {e}")
    
    def _extract_graph_structure(self, agent_service):
        """
        그래프 구조 추출
        
        Args:
            agent_service: 에이전트 서비스
            
        Returns:
            tuple: (nodes, edges, tools)
        """
        graph = agent_service.app.get_graph()
        
        try:
            # 그래프에서 실제 노드와 엣지 정보 추출
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
                workflow = agent_service.workflow
                if hasattr(workflow, 'nodes'):
                    nodes = list(workflow.nodes.keys()) if hasattr(workflow.nodes, 'keys') else []
            
            # __start__와 __end__ 노드 명시적 추가
            if "__start__" not in nodes:
                nodes.insert(0, "__start__")
            if "__end__" not in nodes:
                nodes.append("__end__")
            
            # 그래프 정보가 없으면 오류 발생
            if not nodes or not edges:
                raise ValueError("그래프 구조 정보를 추출할 수 없습니다.")
            
            # 모든 도구 정보 추출 (기본 도구 + MCP 도구)
            tools = []
            
            # 기본 도구 정보 추출
            if hasattr(agent_service, 'tool_registry') and agent_service.tool_registry:
                basic_tools = agent_service.tool_registry.get_tool_info()
                logger.debug(f"기본 도구 개수: {len(basic_tools)}")
                for tool in basic_tools:
                    logger.debug(f"기본 도구: {tool['name']}")
                    tools.append({
                        'name': tool['name'],
                        'description': tool['description'],
                        'type': 'basic'
                    })
            
            # MCP 도구 정보 추출
            from ..mcp import mcp_client_manager
            mcp_tools = mcp_client_manager.get_tool_info()
            logger.debug(f"MCP 도구 개수: {len(mcp_tools)}")
            for tool_name, tool_info in mcp_tools.items():
                logger.debug(f"MCP 도구: {tool_name} - {tool_info}")
                tools.append({
                    'name': tool_name,
                    'description': tool_info.get('description', '설명 없음'),
                    'type': 'mcp',
                    'server': tool_info.get('server', 'Unknown')
                })
            
            logger.debug(f"총 도구 개수: {len(tools)}")
            
            return nodes, edges, tools
            
        except Exception as e:
            logger.error(f"그래프 정보 추출 실패: {e}")
            raise ValueError(f"그래프 구조를 추출할 수 없습니다: {e}")
    
    def _export_mermaid(self, nodes, edges, tools, description, output):
        """
        Mermaid 형식으로 내보내기
        
        Args:
            nodes: 노드 리스트
            edges: 엣지 리스트
            tools: 도구 리스트
            description: 설명
            output: 출력 파일 경로
        """
        try:
            # 출력 파일 경로 준비
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 마크다운 코드블럭으로 감싸기
            mermaid_content = generate_mermaid_diagram(nodes, edges, tools, description, for_console=False)
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
            logger.error(f"Mermaid 다이어그램 생성 실패: {e}")
    
    def _export_json(self, nodes, edges, tools, description, output):
        """
        JSON 형식으로 내보내기
        
        Args:
            nodes: 노드 리스트
            edges: 엣지 리스트
            tools: 도구 리스트
            description: 설명
            output: 출력 파일 경로
        """
        try:
            # 출력 파일 경로 준비
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # JSON 데이터 생성
            node_list = [{"id": node, "type": "node", "label": node} for node in nodes]
            edge_list = [{"source": edge[0], "target": edge[1]} for edge in edges if isinstance(edge, (list, tuple)) and len(edge) >= 2]
            
            # 도구 정보 추가
            tool_list = []
            if tools:
                for tool in tools:
                    tool_list.append({
                        "name": tool["name"],
                        "description": tool["description"],
                        "type": "tool"
                    })
            
            graph_data = {
                "nodes": node_list,
                "edges": edge_list,
                "tools": tool_list,
                "workflow": "LangGraph Assistant",
                "description": description or "입력 처리 → 응답 생성 → 출력 포맷팅 워크플로우"
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(graph_data, f, ensure_ascii=False, indent=2)
            console.print(f"[green]✅ 그래프 구조가 '{output}' 파일에 저장되었습니다.[/green]")
        except Exception as e:
            console.print(f"[red]❌ JSON 형식 생성 실패: {e}[/red]")
            logger.error(f"JSON 형식 생성 실패: {e}") 