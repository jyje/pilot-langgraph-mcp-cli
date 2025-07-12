"""
설정 명령어 비즈니스 로직
"""

import shutil
from pathlib import Path
from rich.console import Console
from ..logging import get_logger

console = Console()
logger = get_logger("my_mcp.commands.setup")


class SetupCommand:
    """설정 명령어 처리 클래스"""
    
    def __init__(self, project_root: Path):
        """
        설정 명령어 초기화
        
        Args:
            project_root: 프로젝트 루트 경로
        """
        self.project_root = project_root
        self.settings_file = project_root / "settings.yaml"
        self.sample_file = project_root / "settings.sample.yaml"
    
    def execute(self):
        """설정 파일 생성 명령어 실행"""
        if self.settings_file.exists():
            console.print(f"[yellow]설정 파일이 이미 존재합니다: {self.settings_file}[/yellow]")
            return
        
        if not self.sample_file.exists():
            console.print(f"[red]템플릿 파일을 찾을 수 없습니다: {self.sample_file}[/red]")
            return
        
        try:
            # 템플릿 파일 복사
            shutil.copy2(self.sample_file, self.settings_file)
            
            console.print(f"[green]✅ 설정 파일이 생성되었습니다: {self.settings_file}[/green]")
            console.print("[yellow]settings.yaml 파일을 편집하여 OpenAI API 키를 설정하세요.[/yellow]")
            
        except Exception as e:
            console.print(f"[red]설정 파일 생성 실패: {e}[/red]")
            logger.error(f"설정 파일 생성 실패: {e}") 