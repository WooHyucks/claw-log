# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claw-Log는 Git 변경사항을 AI로 분석하여 커리어 로그를 자동 생성하는 Python CLI 도구입니다. 매일의 개발 기록을 이력서에 활용 가능한 마크다운으로 변환합니다.

## Commands

```bash
# 개발 설치
pip install -e .

# 실행
claw-log                     # 메인 워크플로우 (diff 수집 → AI 요약 → 저장)
claw-log --reset             # 설정 초기화 후 위자드 재실행
claw-log --days 7            # 과거 N일치 커밋 한꺼번에 요약

# 설정 조회/변경
claw-log --status            # 엔진, 프로젝트, 스케줄, 로그파일 상태 한눈에 조회
claw-log --engine            # AI 엔진/모델만 변경 (프로젝트·스케줄 유지)
claw-log --dry-run           # API 호출 없이 수집될 diff 크기/토큰 미리보기

# 프로젝트 관리
claw-log --projects          # 프로젝트 추가/선택/해제 (인터랙티브)
claw-log --projects-show     # 등록된 프로젝트 목록 조회

# 스케줄 관리
claw-log --schedule 23:30    # 매일 자동 실행 스케줄 등록/변경
claw-log --schedule-show     # 현재 스케줄 조회
claw-log --schedule-remove   # 스케줄 삭제

# 로그 조회
claw-log --log               # 최근 5개 엔트리 출력
claw-log --log 20            # 최근 20개 엔트리 출력

# 패키지 빌드
python -m build
```

테스트 프레임워크와 린터는 아직 설정되어 있지 않습니다.

## Architecture

```
main.py (CLI 진입점, 위자드, Git diff 수집)
    │
    ├── engine.py (AI 요약 엔진)
    │     BaseSummarizer (ABC)
    │       ├── GeminiSummarizer    → google.genai (gemini-2.5-flash)
    │       ├── OpenAISummarizer    → OpenAI API (gpt-4o-mini)
    │       └── CodexOAuthSummarizer → ChatGPT Backend (gpt-5.1/5.2)
    │                                   └── oauth.py (OAuth 2.0 PKCE 인증)
    │
    ├── scheduler.py (OS별 스케줄링: Windows schtasks / Unix crontab)
    │
    └── storage.py (career_logs.md에 결과 prepend)
```

**데이터 플로우**: CLI 실행 → Git 저장소 탐색 → diff 추출 → AI 요약 → career_logs.md에 저장

## Key Design Decisions

- **Abstract Base Class 패턴**: `engine.py`의 `BaseSummarizer`를 상속하여 LLM 백엔드 확장. 새 백엔드 추가 시 `summarize()` 메서드만 구현하면 됨
- **AI 프롬프트 출력**: 한국어 설명 + 영어 기술용어 혼합 형식, 최대 2000자, 이력서 bullet point 포함
- **Git diff 수집**: `main.py`의 `get_git_diff_for_path(days=0)`에서 당일(또는 N일치) 커밋 + 미커밋 변경사항을 합산, lock 파일/빌드 산출물 제외. per-project 15,000자 truncation
- **엔진 선택 분리**: `select_engine()`을 `run_wizard()`에서 추출하여 `--engine`과 위자드 양쪽에서 재사용
- **로그 파싱**: `storage.py`의 `read_recent_logs()`는 `## 📅` 날짜 헤더 패턴으로 엔트리 경계 분할 (`---` 구분자가 엔트리 내부에도 있으므로 naive split 불가)
- **OAuth**: `oauth.py`에서 PKCE 플로우 구현, 토큰은 `~/.claw-log/oauth_tokens.json`에 저장

## Configuration

`.env` 파일 (위자드가 자동 생성):
- `LLM_TYPE`: `gemini` | `openai` | `openai-oauth`
- `API_KEY`: API 키 또는 `__OAUTH__` (OAuth 사용 시)
- `PROJECT_PATHS`: 쉼표 구분 프로젝트 경로
- `CODEX_MODEL`: `gpt-5.1` | `gpt-5.2` (OAuth 전용)

## Dependencies

- `google-genai>=0.3.0`, `openai`, `python-dotenv`, `questionary>=2.0.0`
- Python >= 3.7
- 표준 라이브러리: `subprocess` (Git), `http.server` (OAuth 콜백), `hashlib`/`secrets` (PKCE)
