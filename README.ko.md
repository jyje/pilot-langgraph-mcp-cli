# pilot-langgraph-mcp-cli

*다른 언어로 읽기: [English](README.md), [한국어](README.ko.md)*

OpenAI API를 이용한 LangGraph 기반 챗봇 CLI 도구로 MCP (Model Context Protocol) 지원을 포함합니다.

## 주요 기능

- **대화형 챗봇**: AI와 실시간 대화
- **스트리밍 응답**: 실시간 도구 사용 추적이 포함된 실시간 응답 출력
- **MCP 서버 지원**: Model Context Protocol을 통한 확장 가능한 도구 시스템
- **도구 레지스트리 시스템**: 중앙 집중식 도구 관리 및 등록
- **강화된 날짜/시간 도구**: 보안 검증 기능이 있는 내장 날짜/시간 도구
- **워크플로우 시각화**: 도구 정보를 포함한 LangGraph 워크플로우를 Mermaid 다이어그램으로 출력
- **실시간 도구 추적**: 디버그 모드 지원과 함께 도구 실행 상황을 실시간으로 표시
- **설정 관리**: 유연한 설정 관리
- **완전한 E2E 테스트**: 자동화된 테스트를 통한 모든 CLI 옵션 커버리지

## 설치 및 설정

**요구사항**: Python 3.12+

### 1. 패키지 설치

```bash
# 개발 환경에서 설치
pip install -e .

# 또는 uv 사용 (권장)
uv pip install -e .
```

### 2. 설정 파일 생성

```bash
# 설정 파일 템플릿 생성
my-mcp setup

# 또는 수동으로 생성
cp settings.sample.yaml settings.yaml
```

### 3. OpenAI API 키 설정

`settings.yaml` 파일을 편집하여 OpenAI API 키를 설정합니다:

```yaml
openai:
  api_key: "your-actual-openai-api-key"
  model: "gpt-4o-mini"
  temperature: 0.7
  max_tokens: 1000
  streaming: true

# 선택적 MCP 서버 설정
mcp:
  servers:
    # 여기에 MCP 서버를 추가하세요
```

## 사용법

### 챗봇 시작

```bash
# 대화형 챗봇 시작
my-mcp chat

# 일회성 질문
my-mcp chat "안녕하세요, 오늘 날씨 어때요?"

# 스트리밍 비활성화
my-mcp chat --no-stream

# 디버그 모드 활성화 (도구 ID와 워크플로우 단계 표시)
my-mcp chat --debug

# 대화 내용 저장
my-mcp chat --save
```

### 워크플로우 시각화

```bash
# 그래프 구조를 Mermaid 다이어그램으로 출력
my-mcp agent export

# 도구 정보를 포함한 AI 자동 설명 포함
my-mcp agent export --ai-description

# JSON 형식으로 출력
my-mcp agent export --format json
```

### 기타 명령어

```bash
# 정보 확인
my-mcp info

# 버전 확인
my-mcp version

# 도움말
my-mcp --help
```

## 프로젝트 구조

```
pilot-langgraph-mcp-cli/
├── src/
│   ├── config.py              # 설정 관리
│   ├── main.py                # CLI 진입점
│   └── my_mcp/
│       ├── __init__.py
│       ├── logging.py         # 로깅 설정
│       ├── agent/
│       │   ├── __init__.py
│       │   └── service.py     # LangGraph 챗봇 서비스
│       ├── mcp/               # MCP (Model Context Protocol) 지원
│       │   ├── __init__.py
│       │   ├── client.py      # MCP 클라이언트 구현
│       │   ├── registry.py    # MCP 서버 레지스트리
│       │   └── server.py      # MCP 서버 인터페이스
│       ├── tools/             # 도구 시스템
│       │   ├── __init__.py
│       │   ├── datetime_tools.py  # 강화된 날짜/시간 도구
│       │   └── registry.py    # 도구 레지스트리 관리
│       └── utils/
│           ├── __init__.py
│           ├── diagram_utils.py   # 도구 지원을 포함한 워크플로우 시각화
│           ├── markdown_utils.py
│           └── output_utils.py
├── settings.sample.yaml       # 설정 템플릿
├── settings.yaml             # 실제 설정
├── pyproject.toml            # 프로젝트 설정
└── README.md
```

## 테스트

이 프로젝트는 모든 CLI 명령어와 옵션 조합에 대한 완전한 E2E 테스트를 포함합니다.

### 테스트 실행

```bash
# 테스트 의존성 설치
make install-test-deps

# 모든 E2E 테스트 실행
make test

# 빠른 스모크 테스트
make test-smoke

# 특정 명령어 테스트
make test-chat      # chat 명령어 테스트
make test-agent     # agent 명령어 테스트
make test-basic     # 기본 명령어 테스트
```

자세한 테스트 문서는 [`tests/README.ko.md`](tests/README.ko.md) (한글) 또는 [`tests/README.md`](tests/README.md) (영어)를 참조하세요.

## 개발

### 주요 의존성

- `typer`: CLI 프레임워크
- `rich`: 터미널 UI
- `dynaconf`: 설정 관리
- `openai`: OpenAI API 클라이언트
- `langgraph`: LangGraph 워크플로우
- `langchain`: LangChain 프레임워크
- `langchain-mcp-adapters`: LangChain용 MCP 통합
- `mcp`: Model Context Protocol 구현
- `httpx`: MCP 통신용 HTTP 클라이언트
- `loguru`: 로깅 라이브러리
- `jsonschema`: JSON 스키마 검증

### 로깅 설정

`settings.yaml`에서 로깅을 구성할 수 있습니다:

```yaml
logging:
  level: "INFO"
  format: "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>"
  file_enabled: false
  file_path: "logs/app.log"
```

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
