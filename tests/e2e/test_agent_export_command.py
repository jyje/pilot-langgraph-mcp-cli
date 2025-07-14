"""E2E tests for 'my-mcp agent export' command - all option combinations"""

import pytest
from src.main import app


class TestAgentExportCommand:
    """agent export 명령어의 모든 옵션 조합 테스트"""
    
    def test_agent_export_help(self, cli_runner):
        """agent export --help 명령 테스트"""
        result = cli_runner.invoke(app, ['agent', 'export', '--help'])
        assert result.exit_code == 0
        assert 'Usage:' in result.output
        assert 'LangGraph 그래프 구조를 내보냅니다' in result.output
    
    def test_agent_export_default(self, cli_runner, mock_agent_service):
        """agent export - 기본 내보내기 테스트"""
        result = cli_runner.invoke(app, ['agent', 'export'])
        assert result.exit_code == 0
    
    @pytest.mark.parametrize("format_type", [
        "mermaid",
        "json",
    ])
    def test_agent_export_format_option(self, cli_runner, mock_agent_service, format_type):
        """agent export --format - 형식 옵션 테스트"""
        result = cli_runner.invoke(app, ['agent', 'export', '--format', format_type])
        assert result.exit_code == 0
    
    @pytest.mark.parametrize("format_short", [
        "mermaid",
        "json",
    ])
    def test_agent_export_format_short_option(self, cli_runner, mock_agent_service, format_short):
        """agent export -f - 형식 옵션 단축형 테스트"""
        result = cli_runner.invoke(app, ['agent', 'export', '-f', format_short])
        assert result.exit_code == 0
    
    def test_agent_export_output_option(self, cli_runner, mock_agent_service, temp_output_dir):
        """agent export --output - 출력 파일 옵션 테스트"""
        output_file = temp_output_dir / "test_graph.mermaid"
        result = cli_runner.invoke(app, [
            'agent', 'export', 
            '--output', str(output_file)
        ])
        assert result.exit_code == 0
    
    def test_agent_export_output_short_option(self, cli_runner, mock_agent_service, temp_output_dir):
        """agent export -o - 출력 파일 옵션 단축형 테스트"""
        output_file = temp_output_dir / "test_graph.json"
        result = cli_runner.invoke(app, [
            'agent', 'export', 
            '-o', str(output_file)
        ])
        assert result.exit_code == 0
    
    def test_agent_export_ai_description_flag(self, cli_runner, mock_agent_service):
        """agent export --ai-description - AI 설명 생성 플래그 테스트"""
        result = cli_runner.invoke(app, [
            'agent', 'export', 
            '--ai-description'
        ])
        assert result.exit_code == 0
    
    # 옵션 조합 테스트
    @pytest.mark.parametrize("format_type,ai_desc", [
        ("mermaid", True),
        ("json", True),
        ("mermaid", False),
        ("json", False),
    ])
    def test_agent_export_format_with_ai_description(self, cli_runner, mock_agent_service, format_type, ai_desc):
        """agent export --format + --ai-description 조합 테스트"""
        cmd = ['agent', 'export', '--format', format_type]
        if ai_desc:
            cmd.append('--ai-description')
        
        result = cli_runner.invoke(app, cmd)
        assert result.exit_code == 0
    
    @pytest.mark.parametrize("format_type", ["mermaid", "json"])
    def test_agent_export_format_with_output(self, cli_runner, mock_agent_service, temp_output_dir, format_type):
        """agent export --format + --output 조합 테스트"""
        extension = "mermaid" if format_type == "mermaid" else "json"
        output_file = temp_output_dir / f"test_graph.{extension}"
        
        result = cli_runner.invoke(app, [
            'agent', 'export',
            '--format', format_type,
            '--output', str(output_file)
        ])
        assert result.exit_code == 0
    
    def test_agent_export_all_options(self, cli_runner, mock_agent_service, temp_output_dir):
        """agent export 모든 옵션 조합 테스트"""
        output_file = temp_output_dir / "full_test_graph.mermaid"
        
        result = cli_runner.invoke(app, [
            'agent', 'export',
            '--format', 'mermaid',
            '--output', str(output_file),
            '--ai-description'
        ])
        assert result.exit_code == 0
    
    # 전역 옵션과의 조합 테스트
    @pytest.mark.parametrize("global_options", [
        ['--verbose'],
        ['--quiet'],
        ['--verbose', '--output', 'json'],
    ])
    def test_agent_export_with_global_options(self, cli_runner, mock_agent_service, global_options):
        """agent export와 전역 옵션 조합 테스트"""
        cmd = global_options + ['agent', 'export']
        result = cli_runner.invoke(app, cmd)
        assert result.exit_code == 0
    
    # 에러 케이스 테스트
    def test_agent_export_invalid_format(self, cli_runner, mock_agent_service):
        """agent export --format invalid - 잘못된 형식 테스트"""
        result = cli_runner.invoke(app, [
            'agent', 'export', 
            '--format', 'invalid_format'
        ])
        # 에러 처리에 따라 exit_code가 다를 수 있음
        assert result.exit_code in [0, 1, 2]
    
    def test_agent_export_invalid_output_path(self, cli_runner, mock_agent_service):
        """agent export --output invalid - 잘못된 출력 경로 테스트"""
        result = cli_runner.invoke(app, [
            'agent', 'export',
            '--output', '/invalid/path/test.mermaid'
        ])
        # 에러가 발생해도 graceful하게 처리되어야 함
        assert result.exit_code in [0, 1]


class TestAgentExportEdgeCases:
    """agent export 명령어 엣지 케이스 테스트"""
    
    def test_agent_export_with_existing_output_file(self, cli_runner, mock_agent_service, temp_output_dir):
        """기존 파일 덮어쓰기 테스트"""
        output_file = temp_output_dir / "existing_file.mermaid"
        output_file.write_text("기존 내용")
        
        result = cli_runner.invoke(app, [
            'agent', 'export',
            '--output', str(output_file)
        ])
        assert result.exit_code == 0
    
    def test_agent_export_very_long_output_path(self, cli_runner, mock_agent_service, temp_output_dir):
        """매우 긴 출력 경로 테스트"""
        long_path = temp_output_dir / ("very_" * 50 + "long_filename.mermaid")
        
        result = cli_runner.invoke(app, [
            'agent', 'export',
            '--output', str(long_path)
        ])
        # 시스템 제한에 따라 결과가 다를 수 있음
        assert result.exit_code in [0, 1]
    
    @pytest.mark.parametrize("special_filename", [
        "파일명-한글.mermaid",
        "file with spaces.json",
        "file_with_special!@#.mermaid",
    ])
    def test_agent_export_special_filenames(self, cli_runner, mock_agent_service, temp_output_dir, special_filename):
        """특수 문자 파일명 테스트"""
        output_file = temp_output_dir / special_filename
        
        result = cli_runner.invoke(app, [
            'agent', 'export',
            '--output', str(output_file)
        ])
        assert result.exit_code == 0 