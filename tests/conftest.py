"""Pytest configuration and fixtures for CLI E2E testing"""

import pytest
import tempfile
import yaml
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock


@pytest.fixture
def cli_runner():
    """CLI 테스트를 위한 CliRunner 인스턴스"""
    return CliRunner()


@pytest.fixture
def temp_config_file():
    """임시 설정 파일 생성"""
    config_data = {
        'openai': {
            'api_key': 'test-api-key',
            'model': 'gpt-4o-mini',
            'streaming': True
        },
        'chatbot': {
            'system_prompt': 'You are a test assistant.',
            'max_tokens': 1000,
            'temperature': 0.7
        },
        'mcp_servers': [
            {
                'name': 'test-server',
                'url': 'http://localhost:8000/mcp'
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        yield f.name
    
    # Cleanup
    Path(f.name).unlink(missing_ok=True)


@pytest.fixture
def mock_mcp_servers():
    """MCP 서버 모킹"""
    with patch('my_mcp.mcp.client.MCPClient') as mock_client:
        # Mock MCP client responses
        mock_instance = MagicMock()
        mock_instance.initialize.return_value = None
        mock_instance.list_tools.return_value = [
            {'name': 'test_tool', 'description': 'Test tool for CLI testing'}
        ]
        mock_client.return_value = mock_instance
        yield mock_client


@pytest.fixture
def mock_agent_service():
    """Agent 서비스 모킹"""
    with patch('my_mcp.agent.service.AgentService') as mock_service:
        mock_instance = MagicMock()
        mock_instance.connect_mcp_servers.return_value = None
        mock_instance.chat_stream_with_workflow.return_value = iter([
            {'type': 'text', 'content': 'Test response'}
        ])
        mock_service.return_value = mock_instance
        yield mock_service


@pytest.fixture
def mock_openai_api():
    """OpenAI API 모킹"""
    with patch('openai.OpenAI') as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        yield mock_client


@pytest.fixture(autouse=True)
def mock_settings_check():
    """설정 파일 확인 모킹 (모든 테스트에 자동 적용)"""
    with patch('my_mcp.config.check_settings', return_value=True):
        yield


@pytest.fixture
def temp_output_dir():
    """임시 출력 디렉토리"""
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir) 