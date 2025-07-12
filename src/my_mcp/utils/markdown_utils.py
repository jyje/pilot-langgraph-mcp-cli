"""
마크다운 관련 유틸리티 함수들
"""

import datetime
from rich.console import Console
from ..logging import get_logger

console = Console()
logger = get_logger("my_mcp.utils.markdown")


def save_conversation_to_markdown(conversation_log: list, filename: str):
    """
    대화 내용을 마크다운 파일로 저장합니다.
    
    Args:
        conversation_log: 대화 기록 리스트
        filename: 저장할 파일명
    """
    try:
        # 파일명 처리 (.md 확장자 추가)
        if not filename.endswith('.md'):
            filename += '.md'
        
        # 마크다운 내용 생성
        markdown_content = f"# AI 대화 기록\n\n"
        markdown_content += f"**생성일시**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        markdown_content += "---\n\n"
        
        for entry in conversation_log:
            markdown_content += entry + "\n"
        
        # 파일 저장
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        console.print(f"[green]✅ 대화 내용이 '{filename}' 파일에 저장되었습니다.[/green]")
        
    except Exception as e:
        console.print(f"[red]파일 저장 실패: {e}[/red]")
        logger.error(f"마크다운 저장 실패: {e}") 