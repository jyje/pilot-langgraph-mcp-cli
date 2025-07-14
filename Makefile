# Makefile for my-mcp CLI E2E Testing

.PHONY: help test test-e2e test-smoke test-chat test-agent test-basic install-test-deps clean-test

# 기본 타겟
help:
	@echo "Available commands:"
	@echo "  test              - 모든 E2E 테스트 실행"
	@echo "  test-e2e          - E2E 테스트만 실행"
	@echo "  test-smoke        - 스모크 테스트만 실행"
	@echo "  test-chat         - chat 명령어 테스트만 실행"
	@echo "  test-agent        - agent 명령어 테스트만 실행"
	@echo "  test-basic        - 기본 명령어 테스트만 실행"
	@echo "  install-test-deps - 테스트 의존성 설치"
	@echo "  clean-test        - 테스트 임시 파일 정리"

# 테스트 의존성 설치
install-test-deps:
	@echo "테스트 의존성 설치 중..."
	uv add --dev pytest pytest-asyncio pytest-mock pyyaml

# 모든 E2E 테스트 실행
test: test-e2e

# E2E 테스트 실행
test-e2e:
	@echo "E2E 테스트 실행 중..."
	pytest tests/e2e/ -m "not slow" --tb=short

# 스모크 테스트만 실행 (빠른 기본 기능 확인)
test-smoke:
	@echo "스모크 테스트 실행 중..."
	pytest tests/e2e/test_basic_commands.py::TestAllCommandsSmoke -v

# chat 명령어 테스트만 실행
test-chat:
	@echo "Chat 명령어 테스트 실행 중..."
	pytest tests/e2e/test_chat_command.py -v

# agent 명령어 테스트만 실행
test-agent:
	@echo "Agent 명령어 테스트 실행 중..."
	pytest tests/e2e/test_agent_export_command.py -v

# 기본 명령어 테스트만 실행
test-basic:
	@echo "기본 명령어 테스트 실행 중..."
	pytest tests/e2e/test_basic_commands.py -v

# 전체 테스트 (느린 테스트 포함)
test-all:
	@echo "모든 테스트 실행 중 (느린 테스트 포함)..."
	pytest tests/e2e/ --tb=short

# 커버리지와 함께 테스트 실행
test-coverage:
	@echo "커버리지와 함께 테스트 실행 중..."
	pytest tests/e2e/ --cov=src --cov-report=html --cov-report=term

# 병렬 테스트 실행 (pytest-xdist 필요)
test-parallel:
	@echo "병렬 테스트 실행 중..."
	pytest tests/e2e/ -n auto --tb=short

# 상세한 출력으로 테스트 실행
test-verbose:
	@echo "상세한 출력으로 테스트 실행 중..."
	pytest tests/e2e/ -vvv --tb=long

# 특정 테스트 패턴 실행
test-pattern:
	@read -p "테스트 패턴을 입력하세요 (예: test_chat_*): " pattern; \
	pytest tests/e2e/ -k "$$pattern" -v

# 실패한 테스트만 재실행
test-failed:
	@echo "실패한 테스트만 재실행 중..."
	pytest tests/e2e/ --lf --tb=short

# 테스트 임시 파일 정리
clean-test:
	@echo "테스트 임시 파일 정리 중..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf htmlcov/ .coverage 2>/dev/null || true
	@echo "정리 완료!"

# 개발 모드 - 파일 변경 시 자동 테스트 (pytest-watch 필요)
test-watch:
	@echo "파일 변경 감시 모드 (Ctrl+C로 종료)..."
	ptw tests/e2e/ -- --tb=short

# 테스트 통계 보고서
test-stats:
	@echo "테스트 통계 생성 중..."
	pytest tests/e2e/ --tb=no --quiet --collect-only | grep "test session starts" -A 20 