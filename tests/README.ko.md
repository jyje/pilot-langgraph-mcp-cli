# CLI E2E 테스트

*상위 문서: [English README](../README.md), [한국어 README](../README.ko.md)*

`my-mcp` CLI 명령어와 옵션 조합을 위한 완전한 E2E 테스트 시스템입니다.

## 목표

- **100% CLI 옵션 커버리지** - 모든 CLI 옵션과 조합 테스트
- **회귀 방지** - 새 기능이 기존 기능을 깨뜨리지 않도록 보장
- **안정성 보장** - 모든 CLI 명령이 예상대로 동작

## 디렉토리 구조

```
tests/
├── __init__.py              # 테스트 패키지
├── conftest.py              # pytest 설정 및 픽스처
├── e2e/                     # E2E 테스트 디렉토리
│   ├── __init__.py
│   ├── test_chat_command.py         # chat 명령어 테스트
│   ├── test_agent_export_command.py # agent export 테스트
│   └── test_basic_commands.py       # info, version, setup 테스트
└── README.md                # 영어 문서
└── README.ko.md             # 이 파일 (한글 문서)
```

## 빠른 시작

### 의존성 설치

```bash
make install-test-deps
```

### 테스트 실행

```bash
# 모든 E2E 테스트
make test

# 특정 명령어만
make test-chat      # chat 명령어만
make test-agent     # agent 명령어만
make test-basic     # info, version, setup

# 빠른 스모크 테스트
make test-smoke
```

## 테스트 명령어

| 명령어 | 설명 |
|---------|-------------|
| `make test` | 모든 E2E 테스트 실행 |
| `make test-smoke` | 빠른 스모크 테스트 |
| `make test-chat` | chat 명령어 테스트만 |
| `make test-agent` | agent export 테스트만 |
| `make test-basic` | 기본 명령어 테스트 |
| `make test-coverage` | 커버리지 포함 테스트 |
| `make test-parallel` | 병렬 실행 |
| `make test-failed` | 실패한 테스트만 재실행 |

## 테스트 커버리지

### 테스트되는 명령어
- `my-mcp chat` - 모든 옵션 조합 (30+ 테스트 케이스)
- `my-mcp agent export` - 모든 옵션 조합 (20+ 테스트 케이스)
- `my-mcp info/version/setup` - 기본 및 전역 옵션 조합

### 테스트되는 옵션
- 개별 옵션: `--once`, `--no-stream`, `--debug`, `--save`, `--format`, `--output`
- 단축 옵션: `-f`, `-o`, `-v`, `-q`, `-c`
- 옵션 조합: 2개, 3개, 4개 이상 옵션 함께 사용
- 전역 옵션: `--verbose`, `--quiet`, `--output`, `--config`
- 에러 케이스: 잘못된 값, 존재하지 않는 파일
- 엣지 케이스: 빈 값, 특수문자, 유니코드

## 새 기능 추가 시

새로운 CLI 명령어나 옵션을 추가할 때는 **E2E 테스트가 필수**입니다.

### 새 명령어 체크리스트
- [ ] `tests/e2e/test_[명령어]_command.py` 생성
- [ ] 모든 개별 옵션 테스트
- [ ] 모든 옵션 조합 테스트
- [ ] 전역 옵션과의 조합 테스트
- [ ] 에러 케이스 테스트
- [ ] `make test-e2e` 실행하여 검증

### 기존 명령어 업데이트
- [ ] 해당 테스트 파일 업데이트
- [ ] 새 옵션 조합 테스트 추가
- [ ] 회귀 테스트 실행

자세한 요구사항은 `.cursor/rules/debug-rules.mdc`를 참조하세요.

## 픽스처

`conftest.py`의 공통 픽스처:
- `cli_runner` - Typer CLI 테스트 러너
- `temp_config_file` - 임시 설정 파일
- `mock_mcp_servers` - MCP 서버 모킹
- `mock_agent_service` - Agent 서비스 모킹
- `temp_output_dir` - 임시 출력 디렉토리

자동 모킹:
- 설정 파일 확인 (`check_settings`)
- OpenAI API 호출
- MCP 서버 연결

---

**핵심 원칙: 새 기능 추가 → E2E 테스트 필수** 