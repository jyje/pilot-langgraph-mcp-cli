"""E2E tests for basic commands: info, version, setup - all option combinations"""

import pytest
from src.main import app


class TestInfoCommand:
    """info 명령어 테스트"""
    
    def test_info_help(self, cli_runner):
        """info --help 명령 테스트"""
        result = cli_runner.invoke(app, ['info', '--help'])
        assert result.exit_code == 0
        assert 'Usage:' in result.output
    
    def test_info_basic(self, cli_runner):
        """info - 기본 정보 표시 테스트"""
        result = cli_runner.invoke(app, ['info'])
        assert result.exit_code == 0
    
    # 전역 옵션과의 조합 테스트
    @pytest.mark.parametrize("global_options", [
        ['--verbose'],
        ['--quiet'],
        ['--verbose', '--output', 'json'],
        ['--output', 'text'],
    ])
    def test_info_with_global_options(self, cli_runner, global_options):
        """info와 전역 옵션 조합 테스트"""
        cmd = global_options + ['info']
        result = cli_runner.invoke(app, cmd)
        assert result.exit_code == 0


class TestVersionCommand:
    """version 명령어 테스트"""
    
    def test_version_help(self, cli_runner):
        """version --help 명령 테스트"""
        result = cli_runner.invoke(app, ['version', '--help'])
        assert result.exit_code == 0
        assert 'Usage:' in result.output
    
    def test_version_basic(self, cli_runner):
        """version - 기본 버전 표시 테스트"""
        result = cli_runner.invoke(app, ['version'])
        assert result.exit_code == 0
    
    # 전역 옵션과의 조합 테스트
    @pytest.mark.parametrize("global_options", [
        ['--verbose'],
        ['--quiet'],
        ['--verbose', '--output', 'json'],
        ['--output', 'text'],
    ])
    def test_version_with_global_options(self, cli_runner, global_options):
        """version과 전역 옵션 조합 테스트"""
        cmd = global_options + ['version']
        result = cli_runner.invoke(app, cmd)
        assert result.exit_code == 0


class TestSetupCommand:
    """setup 명령어 테스트"""
    
    def test_setup_help(self, cli_runner):
        """setup --help 명령 테스트"""
        result = cli_runner.invoke(app, ['setup', '--help'])
        assert result.exit_code == 0
        assert 'Usage:' in result.output
    
    def test_setup_basic(self, cli_runner):
        """setup - 기본 설정 테스트"""
        result = cli_runner.invoke(app, ['setup'])
        assert result.exit_code == 0
    
    # 전역 옵션과의 조합 테스트
    @pytest.mark.parametrize("global_options", [
        ['--verbose'],
        ['--quiet'],
        ['--verbose', '--output', 'json'],
        ['--output', 'text'],
    ])
    def test_setup_with_global_options(self, cli_runner, global_options):
        """setup과 전역 옵션 조합 테스트"""
        cmd = global_options + ['setup']
        result = cli_runner.invoke(app, cmd)
        assert result.exit_code == 0


class TestMainAppBasics:
    """메인 앱 기본 기능 테스트"""
    
    def test_main_help(self, cli_runner):
        """my-mcp --help 명령 테스트"""
        result = cli_runner.invoke(app, ['--help'])
        assert result.exit_code == 0
        assert 'Usage:' in result.output
        assert 'OpenAI API 기반 LangGraph 챗봇 CLI' in result.output
    
    def test_main_no_command(self, cli_runner):
        """my-mcp (명령어 없음) 테스트"""
        result = cli_runner.invoke(app, [])
        assert result.exit_code == 0
        assert 'Usage:' in result.output
    
    def test_main_invalid_command(self, cli_runner):
        """my-mcp invalid_command 테스트"""
        result = cli_runner.invoke(app, ['invalid_command'])
        assert result.exit_code != 0
        assert 'No such command' in result.output or 'Usage:' in result.output
    
    # 전역 옵션 단독 테스트
    @pytest.mark.parametrize("global_option", [
        ['--verbose'],
        ['--quiet'],
        ['--output', 'json'],
        ['--output', 'text'],
    ])
    def test_global_options_alone(self, cli_runner, global_option):
        """전역 옵션만 사용 테스트"""
        result = cli_runner.invoke(app, global_option)
        assert result.exit_code == 0
    
    def test_global_options_combination(self, cli_runner):
        """전역 옵션 조합 테스트"""
        result = cli_runner.invoke(app, ['--verbose', '--output', 'json'])
        assert result.exit_code == 0
    
    # Config 파일 옵션 테스트
    def test_config_option(self, cli_runner, temp_config_file):
        """--config 옵션 테스트"""
        result = cli_runner.invoke(app, ['--config', temp_config_file, 'version'])
        assert result.exit_code == 0
    
    def test_config_short_option(self, cli_runner, temp_config_file):
        """-c 옵션 테스트"""
        result = cli_runner.invoke(app, ['-c', temp_config_file, 'version'])
        assert result.exit_code == 0
    
    def test_config_with_invalid_path(self, cli_runner):
        """잘못된 config 경로 테스트"""
        result = cli_runner.invoke(app, ['--config', '/invalid/path.yaml', 'version'])
        # 설정 파일이 없어도 graceful하게 처리되어야 함
        assert result.exit_code in [0, 1]


class TestAgentSubcommandGroup:
    """agent 하위 명령어 그룹 테스트"""
    
    def test_agent_help(self, cli_runner):
        """my-mcp agent --help 명령 테스트"""
        result = cli_runner.invoke(app, ['agent', '--help'])
        assert result.exit_code == 0
        assert 'Usage:' in result.output
        assert 'LangGraph 에이전트 관리 명령어' in result.output
    
    def test_agent_no_subcommand(self, cli_runner):
        """my-mcp agent (하위 명령어 없음) 테스트"""
        result = cli_runner.invoke(app, ['agent'])
        assert result.exit_code == 0
        assert 'Usage:' in result.output
    
    def test_agent_invalid_subcommand(self, cli_runner):
        """my-mcp agent invalid_subcommand 테스트"""
        result = cli_runner.invoke(app, ['agent', 'invalid_subcommand'])
        assert result.exit_code != 0
        assert 'No such command' in result.output or 'Usage:' in result.output


class TestAllCommandsSmoke:
    """모든 명령어 스모크 테스트 (기본 실행 확인)"""
    
    @pytest.mark.parametrize("command", [
        ['info'],
        ['version'],
        ['setup'],
        ['agent', 'export'],
        ['chat', '--help'],  # chat은 interactive라서 help만
    ])
    def test_all_commands_smoke(self, cli_runner, command):
        """모든 명령어 기본 실행 스모크 테스트"""
        result = cli_runner.invoke(app, command)
        assert result.exit_code == 0
    
    @pytest.mark.parametrize("command", [
        ['info'],
        ['version'],
        ['setup'],
        ['agent', 'export'],
    ])
    def test_all_commands_with_verbose(self, cli_runner, command):
        """모든 명령어 --verbose 옵션 테스트"""
        cmd = ['--verbose'] + command
        result = cli_runner.invoke(app, cmd)
        assert result.exit_code == 0
    
    @pytest.mark.parametrize("command", [
        ['info'],
        ['version'],
        ['setup'],
        ['agent', 'export'],
    ])
    def test_all_commands_with_quiet(self, cli_runner, command):
        """모든 명령어 --quiet 옵션 테스트"""
        cmd = ['--quiet'] + command
        result = cli_runner.invoke(app, cmd)
        assert result.exit_code == 0 