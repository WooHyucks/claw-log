<p align="center">
  <img src="https://github.com/user-attachments/assets/53c127d0-a66b-47da-afe0-70560046f595" alt="Claw-Log Banner" width="600" />
  <br>

</p>

> **Fork**: 이 저장소는 [WooHyucks/claw-log](https://github.com/WooHyucks/claw-log)에서 Fork된 프로젝트입니다.

> **"오늘의 기록이 내일의 이력서가 됩니다."**

**Claw-Log**는 매일 밤 AI가 당신의 변경 사항을 스캔하여 기술적 의사결정과 트러블슈팅 과정을 마크다운 형식으로 자동 기록하는 CLI 도구입니다.

---

## 🧐 왜 기록해야 하나요?

매일 치열하게 코딩하지만, 정작 성과 공유나 이력서를 업데이트할 때 커밋 로그만 뒤적거리며 머리를 쥐어짜고 있지는 않나요? 

`fix: bug`, `refactor: code` 같은 파편화된 기록으로는 당신의 진짜 고민과 실력을 보여줄 수 없습니다. **Claw-Log**는 LLM(Large Language Model)이 `git diff`를 직접 분석해 당신이 고민한 흔적을 추출합니다. 매일 조금씩 쌓인 이 기록들은 훗날 **이력서 정리나 기술 면접 시 가장 강력한 데이터**가 됩니다.

---

## ✨ 핵심 기능

- **AI 기반 자동 요약**: 단순 커밋 메시지가 아닌, 실제 코드 변화에서 기술적 맥락을 AI가 파악합니다.
- **3종 AI 엔진 지원**: Google Gemini, OpenAI API, ChatGPT 구독 OAuth (GPT-5.1/5.2) 중 선택할 수 있습니다.
- **인터랙티브 프로젝트 탐색**: 상위 폴더 입력 시 하위 Git 저장소를 자동 탐색하고, 체크박스 UI로 선택할 수 있습니다.
- **통합 프로젝트 관리**: 여러 폴더에 흩어진 프로젝트 성과를 한 곳에 모아 관리합니다.
- **기록의 자산화**: 매일 기록된 로그는 로컬에 누적됩니다. 나중에 한 번에 모아 이력서나 기술 블로그의 초안으로 활용하세요.
- **프라이버시 보장**: 소스코드를 외부 서버에 저장하지 않습니다. 모든 분석은 로컬 환경에서 수행됩니다.
- **유연한 설정**: `claw-log --reset` 명령으로 언제든 프로젝트 경로나 API 설정을 변경할 수 있습니다.

---

## 🛠 설치 및 설정

### 1. 설치 (Recommended)
파이썬 환경 격리를 위해 `pipx` 사용을 권장합니다.

```bash
pipx install git+https://github.com/sanghyun-io/claw-log.git
```

### 2. 초기 설정 및 실행
터미널에서 명령어를 입력하면 설정 마법사가 시작됩니다.

```bash
claw-log
```

### 3. 주요 CLI 명령어

```bash
# 실행
claw-log                     # 메인 워크플로우 (diff 수집 → AI 요약 → 저장)
claw-log --reset             # 설정 초기화 후 마법사 재실행
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

# 로그 조회/편집
claw-log --log               # 최근 5개 엔트리 출력
claw-log --log 20            # 최근 20개 엔트리 출력
claw-log --log-edit          # 로그 파일을 기본 편집기로 열기

# 대시보드
claw-log --serve             # 로컬 웹 대시보드 (기본 포트: 8080)
claw-log --serve 3000        # 커스텀 포트로 대시보드 실행
```

---

## 📦 요약 샘플 (Output Sample)

AI 특유의 과장된 표현을 배제하고, 실제 개발 과정에서의 의사결정을 담백하게 기록합니다.

```markdown
### 📂 [my-frontend] - 2026-02-10
> **Summary**: 전역 에러 핸들링 구조 설계 및 런타임 보안 강화

- **상세 내역**
  - `ServerErrorBoundary` 및 Axios 인터셉터를 결합한 전역 에러 처리 시스템 구축.
  - 5xx 서버 에러 및 네트워크 장애 발생 시 전역 에러 페이지 리다이렉션 로직 구현.
  - API BaseURL, 보안 키 등 민감 정보를 `process.env`로 분리하여 관리.
  - Axios 타임아웃(30s) 설정을 통해 지연 응답으로 인한 좀비 커넥션 방지.

- **핵심 불렛 포인트 (Resume Point)**
  - Error Boundary와 Axios Interceptor를 활용한 전역 에러 핸들링 아키텍처 설계로 서비스 안정성 개선.
  - 민감 정보 환경 변수화 및 타임아웃 정책 수립을 통한 애플리케이션 보안 최적화.
```

---

## 🛡 트러블슈팅

명령어를 찾을 수 없거나 라이브러리 충돌이 발생하나요? 최신 Python 버전 환경에서 기존 패키지 잔재가 남아있을 때 생기는 문제입니다. 아래 명령어로 깨끗하게 재설치하세요.

```bash
pipx install claw-log --force --no-cache-dir
```

---

## 🔀 Fork 이후 변경사항

원본 [WooHyucks/claw-log](https://github.com/WooHyucks/claw-log) 대비 추가된 기능:

- **ChatGPT OAuth 인증**: ChatGPT Plus/Pro 구독자가 별도 API 키 없이 OAuth 로그인으로 GPT-5.1/5.2 사용 가능
- **인터랙티브 프로젝트 탐색**: 상위 폴더에서 하위 Git 저장소를 재귀 탐색하고 체크박스 UI로 선택
- **프로젝트 관리 CLI**: `--projects`, `--projects-show` 명령으로 등록된 프로젝트 관리
- **스케줄러 강화**: 사용자 지정 시각 설정, 스케줄 조회(`--schedule-show`), 삭제(`--schedule-remove`)
- **과거 N일 요약**: `--days 7`로 과거 커밋을 한꺼번에 요약
- **설정/로그 조회**: `--status`, `--engine`, `--dry-run`, `--log` 명령어 추가
- **로컬 웹 대시보드**: `--serve`로 설정/프로젝트/스케줄/로그를 브라우저에서 조회

---

## 💡 한마디

**"이력서는 이직할 때 쓰는 것이 아닙니다. 매일의 기록을 모아 정리하는 것입니다."**
