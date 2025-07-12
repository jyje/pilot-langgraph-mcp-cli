# pilot-langgraph-mcp-cli

OpenAI API를 이용한 LangGraph 기반 챗봇 CLI 도구입니다.

## 주요 기능

- **대화형 챗봇**: AI와 실시간 대화
- **스트리밍 응답**: 실시간 응답 출력
- **워크플로우 시각화**: LangGraph 워크플로우를 Mermaid 다이어그램으로 출력
- **설정 관리**: 유연한 설정 관리

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

# 대화 내용 저장
my-mcp chat --save
```

### 워크플로우 시각화

```bash
# 그래프 구조를 Mermaid 다이어그램으로 출력
my-mcp agent export

# AI 자동 설명 포함
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
│       └── agent/
│           ├── __init__.py
│           └── service.py     # LangGraph 챗봇 서비스
├── settings.sample.yaml       # 설정 템플릿
├── settings.yaml             # 실제 설정
├── pyproject.toml            # 프로젝트 설정
└── README.md
```

## 개발

### 주요 의존성

- `typer`: CLI 프레임워크
- `rich`: 터미널 UI
- `dynaconf`: 설정 관리
- `openai`: OpenAI API 클라이언트
- `langgraph`: LangGraph 워크플로우
- `langchain`: LangChain 프레임워크
- `loguru`: 로깅 라이브러리

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
