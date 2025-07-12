"""My MCP CLI 패키지"""

def _get_version():
    """버전 정보를 동적으로 가져옵니다."""
    try:
        from pathlib import Path
        
        # Python 3.12+ 환경에서 내장 tomllib 사용
        try:
            import tomllib
        except ImportError:
            return "0.0.0"
        
        # 프로젝트 루트 경로
        project_root = Path(__file__).parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"
        
        if not pyproject_path.exists():
            return "0.0.0"
        
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
            return data.get("project", {}).get("version", "0.0.0")
    
    except Exception:
        return "0.0.0"

__version__ = _get_version()
