# pilot-langchain-mcp-cli

OpenAI API를 이용한 LangGraph 기반 챗봇 CLI 도구입니다.

## 기능

- **대화형 챗봇**: `my-mcp chat` 명령어로 AI와 대화할 수 있습니다
- **실시간 스트리밍**: 기본적으로 스트리밍 모드로 AI 응답을 실시간으로 출력
- **설정 관리**: dynaconf를 사용한 유연한 설정 관리
- **LangGraph 워크플로우**: 구조화된 AI 응답 생성 프로세스
- **Rich UI**: 아름다운 CLI 인터페이스

## 설치 및 설정

### 1. 패키지 설치

```bash
# 개발 환경에서 설치
pip install -e .

# 또는 uv 사용
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

복사된 `settings.yaml` 파일을 편집하여 OpenAI API 키를 설정합니다:

```yaml
openai:
  api_key: "your-actual-openai-api-key"
  model: "gpt-4o-mini"
  temperature: 0.7
  max_tokens: 1000
  streaming: true  # 스트리밍 모드 (기본값: true)
```

## 사용법

### 챗봇 시작

```bash
my-mcp chat
```

### 대화 종료

대화 중 `/bye`를 입력하면 챗봇이 종료됩니다.

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
│   ├── config.py              # 설정 관리 (dynaconf)
│   ├── main.py                # CLI 진입점 및 라우터
│   └── my_mcp/
│       ├── __init__.py
│       ├── logging.py         # 로깅 설정 및 관리 (loguru)
│       └── service.py         # LangGraph 챗봇 서비스
├── settings.sample.yaml       # 설정 템플릿
├── settings.yaml             # 실제 설정 (gitignore)
├── pyproject.toml            # 프로젝트 설정
└── README.md
```

## 개발

### 요구사항

- Python 3.12+
- OpenAI API 키

### 의존성

- `typer`: CLI 프레임워크
- `rich`: 터미널 UI
- `dynaconf`: 설정 관리
- `openai`: OpenAI API 클라이언트
- `langgraph`: LangGraph 워크플로우
- `langchain`: LangChain 프레임워크
- `loguru`: 강력한 로깅 라이브러리

### 로깅 (loguru)

loguru 기반 로깅 설정은 `src/my_mcp/logging.py` 모듈에서 관리하며, `settings.yaml`에서 구성할 수 있습니다:

```yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
  file_enabled: false  # 파일 로깅 활성화 여부
  file_path: "logs/app.log"  # 로그 파일 경로
  rotation: "10 MB"  # 로그 파일 크기 제한
  retention: "10 days"  # 로그 파일 보관 기간
  compression: "zip"  # 로그 파일 압축 방식
  backtrace: true  # 에러 추적 활성화
  diagnose: true  # 상세 진단 정보 포함
```

로그 레벨별 설명:
- `DEBUG`: 상세한 디버깅 정보
- `INFO`: 일반적인 정보 메시지
- `WARNING`: 경고 메시지
- `ERROR`: 오류 메시지
- `CRITICAL`: 치명적인 오류 메시지

로깅 모듈 사용 방법:
```python
# 로깅 모듈 import
from my_mcp.logging import get_logger

# 로거 인스턴스 생성
logger = get_logger("module_name")

# 로그 메시지 출력
logger.info("정보 메시지")
logger.warning("경고 메시지")
logger.error("오류 메시지")
```

### 스트리밍 모드

기본적으로 스트리밍 모드가 활성화되어 AI 응답을 실시간으로 볼 수 있습니다:

```yaml
openai:
  streaming: true  # 스트리밍 활성화
```

스트리밍을 비활성화하려면 `false`로 설정하세요. 비활성화 시 전체 응답을 한 번에 출력합니다.

### 개발 모드

```yaml
development:
  debug: true
  verbose: true
```

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
