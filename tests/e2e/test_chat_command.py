"""E2E tests for 'my-mcp chat' command - all option combinations"""

import pytest
from src.main import app


class TestChatCommand:
    """chat 명령어의 모든 옵션 조합 테스트"""
    
    # 기본 chat 명령어 테스트
    def test_chat_help(self, cli_runner):
        """chat --help 명령 테스트"""
        result = cli_runner.invoke(app, ['chat', '--help'])
        assert result.exit_code == 0
        assert 'Usage:' in result.output
        assert '대화형 챗봇을 시작합니다' in result.output
    
    @pytest.mark.parametrize("question", [
        "안녕하세요",
        "현재 시간이 몇 시인가요?",
        "간단한 계산을 도와주세요",
    ])
    def test_chat_with_question_argument(self, cli_runner, mock_agent_service, question):
        """chat [QUESTION] - 직접 질문 입력 테스트"""
        result = cli_runner.invoke(app, ['chat', question])
        assert result.exit_code == 0
        assert '일회성 대화 모드입니다' in result.output
    
    def test_chat_once_flag(self, cli_runner, mock_agent_service):
        """chat --once - 일회성 대화 모드 테스트"""
        result = cli_runner.invoke(app, ['chat', '--once'], input='테스트 질문\n')
        assert result.exit_code == 0
        assert '일회성 대화 모드입니다' in result.output
    
    @pytest.mark.parametrize("question", [
        "스트리밍 테스트",
        "비스트리밍 테스트",
    ])
    def test_chat_no_stream_flag(self, cli_runner, mock_agent_service, question):
        """chat --no-stream - 스트리밍 비활성화 테스트"""
        result = cli_runner.invoke(app, ['chat', '--no-stream', question])
        assert result.exit_code == 0
        assert '일회성 대화 모드입니다' in result.output
    
    def test_chat_debug_flag(self, cli_runner, mock_agent_service):
        """chat --debug - 디버그 모드 테스트"""
        result = cli_runner.invoke(app, ['chat', '--debug', '디버그 테스트'])
        assert result.exit_code == 0
        assert '디버그 모드가 활성화되었습니다' in result.output
    
    def test_chat_save_flag(self, cli_runner, mock_agent_service, temp_output_dir):
        """chat --save - 대화 저장 테스트"""
        save_file = temp_output_dir / "test_conversation.md"
        result = cli_runner.invoke(app, [
            'chat', 
            '--save', str(save_file),
            '저장 테스트'
        ])
        assert result.exit_code == 0
    
    # 옵션 조합 테스트
    @pytest.mark.parametrize("options,question", [
        (['--once', '--no-stream'], '조합 테스트 1'),
        (['--once', '--debug'], '조합 테스트 2'),
        (['--no-stream', '--debug'], '조합 테스트 3'),
        (['--once', '--no-stream', '--debug'], '조합 테스트 4'),
    ])
    def test_chat_option_combinations(self, cli_runner, mock_agent_service, options, question):
        """chat 명령어 옵션 조합 테스트"""
        cmd = ['chat'] + options + [question]
        result = cli_runner.invoke(app, cmd)
        assert result.exit_code == 0
        
        # 각 옵션에 따른 출력 검증
        if '--debug' in options:
            assert '디버그 모드가 활성화되었습니다' in result.output
        if question:
            assert '일회성 대화 모드입니다' in result.output
    
    @pytest.mark.parametrize("save_options", [
        ['--save', 'test1.md'],
        ['--save', 'conversations/test2.md'],
    ])
    def test_chat_save_combinations(self, cli_runner, mock_agent_service, temp_output_dir, save_options):
        """chat --save 옵션 조합 테스트"""
        save_path = temp_output_dir / save_options[1]
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        cmd = ['chat', '--save', str(save_path), '저장 테스트']
        result = cli_runner.invoke(app, cmd)
        assert result.exit_code == 0
    
    # 전역 옵션과의 조합 테스트
    @pytest.mark.parametrize("global_options", [
        ['--verbose'],
        ['--quiet'],
        ['--verbose', '--output', 'json'],
    ])
    def test_chat_with_global_options(self, cli_runner, mock_agent_service, global_options):
        """chat 명령어와 전역 옵션 조합 테스트"""
        cmd = global_options + ['chat', '전역 옵션 테스트']
        result = cli_runner.invoke(app, cmd)
        assert result.exit_code == 0
    
    # 에러 케이스 테스트
    def test_chat_invalid_save_path(self, cli_runner, mock_agent_service):
        """chat --save 잘못된 경로 테스트"""
        result = cli_runner.invoke(app, [
            'chat', 
            '--save', '/invalid/path/test.md',
            '에러 테스트'
        ])
        # 에러가 발생해도 graceful하게 처리되어야 함
        assert result.exit_code in [0, 1]  # 에러 처리에 따라 다를 수 있음
    
    # 연속 대화 모드 종료 테스트
    def test_chat_continuous_mode_exit(self, cli_runner, mock_agent_service):
        """연속 대화 모드 종료 테스트"""
        result = cli_runner.invoke(app, ['chat'], input='/bye\n')
        assert result.exit_code == 0
        assert '안녕하세요! 코드비머 어시스턴트 입니다' in result.output


class TestChatCommandEdgeCases:
    """chat 명령어 엣지 케이스 테스트"""
    
    def test_chat_empty_question(self, cli_runner, mock_agent_service):
        """빈 질문 입력 테스트"""
        result = cli_runner.invoke(app, ['chat', ''])
        assert result.exit_code == 0
    

    def test_chat_special_characters(self, cli_runner, mock_agent_service):
        """특수 문자가 포함된 질문 테스트"""
        special_question = "특수문자 테스트: !@#$%^&*()_+-=[]{}|;:,.<>?"
        result = cli_runner.invoke(app, ['chat', special_question])
        assert result.exit_code == 0
    
    def test_chat_unicode_question(self, cli_runner, mock_agent_service):
        """유니코드 문자 질문 테스트"""
        unicode_question = "이모지 테스트: 🤖🔧✨🎯🚀"
        result = cli_runner.invoke(app, ['chat', unicode_question])
        assert result.exit_code == 0 