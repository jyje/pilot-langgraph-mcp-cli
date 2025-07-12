# pilot-langchain-mcp-cli

MCP(Model Context Protocol) 관련 CLI 도구입니다.

**Typer** 기반으로 구축되어 현대적이고 사용하기 쉬운 CLI 인터페이스를 제공합니다.

## 기능

- ✨ 아름다운 도움말 출력 (Typer + Rich)
- 🎯 타입 안전성 (Python 타입 힌트 활용)
- 🚀 자동 완성 지원
- 📦 uv 기반 의존성 관리
- 🔧 모든 명령어에 공통 옵션 적용
- 📊 다양한 출력 형식 지원 (text, json, yaml)
- 🌏 다국어 인사 지원 (한국어, 영어, 일본어, 중국어, 스페인어)
- 🎨 다양한 인사 스타일 및 이모지 지원

## 설치

```bash
# 의존성 설치
uv sync

# 가상환경 활성화
source .venv/bin/activate

# 또는 개발 모드로 설치
uv pip install -e .
```

## 사용법

### 기본 명령어

```bash
# 도움말 확인
my-mcp --help

# 인사 메시지
my-mcp hello --name "홍길동"

# 정보 확인
my-mcp info

# 버전 확인
my-mcp version
```

### Hello 명령어 고급 옵션

`hello` 명령어는 다양한 옵션을 제공합니다:

#### 기본 사용법
```bash
# 기본 인사
my-mcp hello --name "홍길동"

# 단축 옵션 사용
my-mcp hello -n "홍길동"
```

#### 다국어 지원
```bash
# 영어 인사
my-mcp hello --name "John" --language english

# 일본어 인사
my-mcp hello --name "田中" --language japanese

# 중국어 인사
my-mcp hello --name "李明" --language chinese

# 스페인어 인사
my-mcp hello --name "Maria" --language spanish

# 단축 옵션
my-mcp hello -n "John" -l english
```

#### 인사 스타일
```bash
# 정중한 스타일
my-mcp hello --name "홍길동" --style formal

# 캐주얼 스타일
my-mcp hello --name "홍길동" --style casual

# 친근한 스타일 (기본값)
my-mcp hello --name "홍길동" --style friendly

# 전문적인 스타일
my-mcp hello --name "홍길동" --style professional

# 단축 옵션
my-mcp hello -n "홍길동" -s formal
```

#### 특수 효과
```bash
# 이모지 추가
my-mcp hello --name "홍길동" --emoji

# 대문자로 출력
my-mcp hello --name "John" --language english --uppercase

# 이모지 + 대문자
my-mcp hello --name "Sarah" --language english --emoji --uppercase
```

#### 반복 및 구분자
```bash
# 3번 반복
my-mcp hello --name "홍길동" --count 3

# 구분자 변경
my-mcp hello --name "홍길동" --count 2 --separator " | "

# 이모지 구분자
my-mcp hello --name "Maria" --language spanish --emoji --count 2 --separator " 🎉 "
```

#### 옵션 조합 예시
```bash
# 모든 옵션 조합
my-mcp hello -n "Alice" -l english -s professional --emoji --uppercase --count 2 --separator " ✨ "

# 한국어 정중한 인사 + 이모지
my-mcp hello -n "김철수" -l korean -s formal --emoji

# 일본어 캐주얼 + 반복
my-mcp hello -n "田中" -l japanese -s casual --count 3 --separator " 😊 "
```

### 공통 옵션

모든 명령어에서 사용할 수 있는 공통 옵션들:

```bash
# 상세 출력 모드
my-mcp --verbose hello --name "홍길동"
my-mcp -v info

# 조용한 모드 (출력 없음)
my-mcp --quiet hello --name "홍길동"
my-mcp -q version

# 출력 형식 변경
my-mcp --output json info
my-mcp --output yaml version
my-mcp -o json hello --name "홍길동"

# 설정 파일 지정
my-mcp --config /path/to/config.toml info
my-mcp -c ./config.conf --verbose hello

# 옵션 조합
my-mcp -v -o json hello -n "테스트" -l english -s professional
```

### 출력 형식

지원되는 출력 형식:

- **text** (기본값): 사람이 읽기 쉬운 텍스트 형식
- **json**: 구조화된 JSON 형식
- **yaml**: YAML 형식

```bash
# 텍스트 출력 (기본)
my-mcp info

# JSON 출력
my-mcp --output json info
{
  "name": "My MCP CLI",
  "version": "0.1.0",
  "description": "MCP(Model Context Protocol) 관련 CLI 도구입니다."
}

# YAML 출력
my-mcp --output yaml version
message: My MCP CLI v0.1.0
status: success
```

## 지원 언어 및 스타일

### 지원 언어
- **korean**: 한국어
- **english**: 영어
- **japanese**: 일본어
- **chinese**: 중국어
- **spanish**: 스페인어

### 지원 스타일
- **formal**: 정중한 스타일 (🎩)
- **casual**: 캐주얼 스타일 (😄)
- **friendly**: 친근한 스타일 (😊) - 기본값
- **professional**: 전문적인 스타일 (💼)

각 스타일은 고유한 이모지와 색상을 가지고 있습니다.

## 자동 완성

Typer는 자동 완성을 지원합니다:

```bash
# 자동 완성 설치
my-mcp --install-completion

# 자동 완성 확인
my-mcp --show-completion
```

## 개발

```bash
# 개발 의존성 설치
uv sync --dev

# 테스트 실행
python -m pytest

# 코드 포맷팅
black src/

# 타입 검사
mypy src/

# 직접 실행
python src/main.py --help
```

## 기술 스택

- **CLI 프레임워크**: Typer
- **출력 스타일링**: Rich
- **패키지 관리**: uv
- **Python 버전**: 3.12+
- **아키텍처**: 공통 옵션 기반 설계

## 프로젝트 구조

```
src/
├── main.py              # CLI 실행 파일
└── my_mcp/
    ├── __init__.py      # 패키지 초기화
    └── cli.py           # 메인 CLI 로직
```
