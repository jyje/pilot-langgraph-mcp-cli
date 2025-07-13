"""
도구 레지스트리 - 사용 가능한 도구들을 관리하는 모듈
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
from ..logging import get_logger

logger = get_logger("my_mcp.tools.registry")


class ToolRegistry:
    """도구 레지스트리 클래스"""
    
    def __init__(self):
        """도구 레지스트리 초기화"""
        self._tools: Dict[str, BaseTool] = {}
        self._tool_status: Dict[str, bool] = {}
        self._tool_descriptions: Dict[str, str] = {}
        
    def register_tool(self, tool: BaseTool, enabled: bool = True) -> None:
        """
        도구를 레지스트리에 등록합니다.
        
        Args:
            tool: 등록할 도구
            enabled: 도구 활성화 여부
        """
        try:
            tool_name = tool.name
            self._tools[tool_name] = tool
            self._tool_status[tool_name] = enabled
            self._tool_descriptions[tool_name] = tool.description
            
            logger.info(f"도구 등록: {tool_name} (활성화: {enabled})")
            
        except Exception as e:
            logger.error(f"도구 등록 실패: {e}")
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        도구를 이름으로 조회합니다.
        
        Args:
            tool_name: 도구 이름
            
        Returns:
            도구 객체 또는 None
        """
        return self._tools.get(tool_name)
    
    def get_enabled_tools(self) -> List[BaseTool]:
        """
        활성화된 도구 목록을 반환합니다.
        
        Returns:
            활성화된 도구 목록
        """
        return [
            tool for tool_name, tool in self._tools.items() 
            if self._tool_status.get(tool_name, False)
        ]
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """
        모든 등록된 도구를 반환합니다.
        
        Returns:
            도구 딕셔너리
        """
        return self._tools.copy()
    
    def get_tool_info(self) -> List[Dict[str, Any]]:
        """
        도구 정보 목록을 반환합니다.
        
        Returns:
            도구 정보 목록
        """
        tool_info = []
        for tool_name, tool in self._tools.items():
            info = {
                "name": tool_name,
                "description": self._tool_descriptions.get(tool_name, "설명 없음"),
                "enabled": self._tool_status.get(tool_name, False),
                "status": "사용 가능" if self._tool_status.get(tool_name, False) else "비활성화"
            }
            tool_info.append(info)
        
        return tool_info
    
    def enable_tool(self, tool_name: str) -> bool:
        """
        도구를 활성화합니다.
        
        Args:
            tool_name: 도구 이름
            
        Returns:
            활성화 성공 여부
        """
        if tool_name in self._tools:
            self._tool_status[tool_name] = True
            logger.info(f"도구 활성화: {tool_name}")
            return True
        return False
    
    def disable_tool(self, tool_name: str) -> bool:
        """
        도구를 비활성화합니다.
        
        Args:
            tool_name: 도구 이름
            
        Returns:
            비활성화 성공 여부
        """
        if tool_name in self._tools:
            self._tool_status[tool_name] = False
            logger.info(f"도구 비활성화: {tool_name}")
            return True
        return False
    
    def get_tool_count(self) -> Dict[str, int]:
        """
        도구 개수 정보를 반환합니다.
        
        Returns:
            도구 개수 정보
        """
        total_tools = len(self._tools)
        enabled_tools = sum(1 for enabled in self._tool_status.values() if enabled)
        
        return {
            "total": total_tools,
            "enabled": enabled_tools,
            "disabled": total_tools - enabled_tools
        }


# 전역 도구 레지스트리 인스턴스
_tool_registry = None


def get_tool_registry() -> ToolRegistry:
    """
    전역 도구 레지스트리 인스턴스를 반환합니다.
    
    Returns:
        도구 레지스트리 인스턴스
    """
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
        _initialize_default_tools()
    return _tool_registry


def _initialize_default_tools():
    """기본 도구들을 레지스트리에 등록합니다."""
    try:
        from .datetime_tools import get_current_time
        
        registry = _tool_registry
        
        # 시간 도구 등록
        registry.register_tool(get_current_time, enabled=True)
        
        logger.info("기본 도구들이 레지스트리에 등록되었습니다.")
        
    except Exception as e:
        logger.error(f"기본 도구 초기화 실패: {e}") 