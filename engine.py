from abc import ABC, abstractmethod
from openai import OpenAI
import os
import sys

try:
    import google.genai as genai
except ImportError:
    print("❌ [Import Error] 필수 라이브러리 로드 실패.")
    print("   'google-generativeai'와 'google-genai' 간의 충돌일 수 있습니다.")
    print("   👉 아래 명령어로 의존성을 재설치해주세요:")
    print("      pipx install claw-log --force")
    sys.exit(1)

# --- 프롬프트 정의 ---
SYSTEM_PROMPT = """
당신은 수석 테크니컬 라이터이자 기술 채용 전문가입니다.
아래 Git 데이터를 분석하여, 경력기술서에 즉시 반영 가능한 수준의 **[성과 중심 데일리 리포트]**를 작성하세요.

[핵심 작성 원칙]
1. **언어 규칙**: 모든 설명은 **한국어**로 작성하세요. 단, 기술 용어(API, 라이브러리, 클래스명 등)는 원어(영어)를 그대로 사용해도 됩니다.
2. **전문적 어휘**: 단순한 서술 대신 '구현함', '최적화함', '설계함', '해결함' 등 전문적인 태도로 문장을 끝맺으세요.
3. **Context 통합**: 이미 커밋된 내용(Past Commits)과 수정 중인 내용(Uncommitted)을 하나의 연속된 작업으로 간주하여 '기능 단위'로 통합 요약하세요.
4. **데이터 기반**: 가능한 경우 구체적인 파일명, 함수명, 라이브러리, 디자인 패턴을 명시하여 기술적 실체를 드러내세요.
5. **분량 제한**: 전체 리포트는 공백 포함 2,000자 이내로 작성하세요.

[출력 형식]
### 📂 [Project Name]
> **핵심 성과**: (오늘 이룬 가장 중요한 기술적 진보를 비즈니스/사용자 가치 관점에서 1문장 요약 - 한국어)

- **🛠 상세 내역**
  - **기능 구현 및 통합**: (주요 파일/클래스명을 포함하여 오늘 완성하거나 진행한 핵심 로직 요약 - 한국어)
  - **기술적 의사결정**: (적용한 라이브러리, 패턴, 혹은 직면한 기술적 문제를 해결한 구체적인 방법 - 한국어)

- **💡 Career Insight**
  - (이 작업을 통해 증명된 본인의 핵심 역량 - 예: 유지보수성 향상, 보안 강화, 확장성 고려 등 - 한국어)

- **📝 Resume Bullet Point**
  - (성과와 기술 스택이 포함된 경력기술서용 핵심 문장. 예: "GitHub Actions 기반의 CI/CD 파이프라인 구축으로 배포 시간 50% 단축")

---
"""

class BaseSummarizer(ABC):
    @abstractmethod
    def summarize(self, text_data):
        pass

class GeminiSummarizer(BaseSummarizer):
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'gemini-2.5-flash' # 최신 모델 사용


    def summarize(self, text_data):
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=f"{SYSTEM_PROMPT}\n\n[전체 개발 내역 데이터]\n{text_data}"
            )
            return response.text
        except Exception as e:
            error_msg = str(e)
            if "400" in error_msg or "API_KEY_INVALID" in error_msg:
                return (
                    "❌ [API Key Error] 유효하지 않은 API 키입니다.\n"
                    "   👉 'claw-log --reset' 명령어로 키를 다시 설정하거나,\n"
                    "      Google AI Studio(https://aistudio.google.com/app/apikey)에서 키 상태를 확인해주세요."
                )
            elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                return (
                    "🌐 [Quota Error] API 사용량이 초과되었습니다.\n"
                    "   👉 잠시 후 다시 시도하거나, 할당량을 확인해주세요."
                )
            elif "404" in error_msg:
                return (
                     "⚠️ [Model Error] 모델을 찾을 수 없습니다.\n"
                     "   👉 지원되지 않는 리전이거나 모델명이 변경되었을 수 있습니다."
                )
            else:
                return f"❌ [Unknown Error] Gemini 요약 실패:\n   {error_msg}\n   👉 네트워크 연결을 확인해주세요."

class OpenAISummarizer(BaseSummarizer):
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        self.model_name = "gpt-4o-mini"

    def summarize(self, text_data):
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"[전체 개발 내역 데이터]\n{text_data}"}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            if "AuthenticationError" in error_msg or "401" in error_msg:
                return (
                    "❌ [API Key Error] 유효하지 않은 API 키입니다.\n"
                    "   👉 'claw-log --reset' 명령어로 키를 다시 설정하거나,\n"
                    "      OpenAI Platform(https://platform.openai.com/api-keys)에서 키를 확인해주세요."
                )
            elif "RateLimitError" in error_msg or "429" in error_msg:
                return (
                    "🌐 [Quota Error] API 사용량이 초과되었거나 너무 많은 요청이 발생했습니다.\n"
                    "   👉 잠시 후 다시 시도하거나, 크레딧 잔액을 확인해주세요."
                )
            else:
                 return f"❌ [Unknown Error] OpenAI 요약 실패:\n   {error_msg}\n   👉 네트워크 상태를 확인해주세요."
