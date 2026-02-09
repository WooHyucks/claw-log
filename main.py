
import os
import sys
import argparse
import subprocess
import datetime
from pathlib import Path
from dotenv import load_dotenv

from claw_log.engine import GeminiSummarizer, OpenAISummarizer
from claw_log.storage import prepend_to_log_file
from claw_log.scheduler import install_schedule

# .env 파일은 현재 작업 디렉토리(CWD)에서 찾습니다.
ENV_PATH = Path(os.getcwd()) / ".env"

def run_wizard():
    print("\n🔮 Claw-Log 초기 설정 마법사 (Dual-LLM Edition)\n")
    
    print("1️⃣  사용할 AI 엔진을 선택하세요.")
    print("   [1] Google Gemini (무료 티어 제공)")
    print("   [2] OpenAI GPT-4o-mini (비용 효율적, 고성능)")
    choice = input("   👉 선택 (1/2): ").strip()
    
    llm_type = "gemini" if choice == "1" else "openai"
    
    print(f"\n2️⃣  API Key를 입력하세요.")
    if llm_type == "gemini":
        print("   (발급: https://aistudio.google.com/app/apikey)")
    else:
        print("   (발급: https://platform.openai.com/api-keys)")
        
    api_key = input("   👉 API Key: ").strip()
    if not api_key:
        print("❌ API Key가 필요합니다.")
        sys.exit(1)

    print("\n3️⃣  분석할 Git 프로젝트 경로들을 입력하세요 (쉼표 구분).")
    print("   (Tip: 터미널에서 각 프로젝트 폴더로 이동 후 'pwd'를 치면 경로를 알 수 있습니다.)")
    print("   (예시: /Users/kim/project-a, /Users/kim/workspace/backend)")
    paths_input = input("   👉 경로: ").strip()
    
    try:
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.write(f"LLM_TYPE={llm_type}\n")
            f.write(f"API_KEY={api_key}\n")
            f.write(f"PROJECT_PATHS={paths_input}\n")
        print(f"\n✅ 설정 저장 완료: {ENV_PATH.absolute()}")
    except Exception as e:
        print(f"❌ 설정 저장 실패: {e}")
        sys.exit(1)

    print("\n4️⃣  매일 밤 23:30 자동 기록 스케줄을 등록할까요? (y/n)")
    if input("   👉 입력: ").strip().lower() == 'y':
        install_schedule()

def get_git_diff_for_path(path_str):
    path = Path(path_str).resolve()
    
    if not path.exists():
        print(f"⚠️  경로를 찾을 수 없습니다: {path}")
        print("   👉 폴더 주소가 정확한지 확인해주세요.")
        return None
        
    if not (path / ".git").exists():
        print(f"⚠️  Git 저장소가 아닙니다 (건너뜀): {path}")
        print("   👉 해당 폴더에 .git 디렉토리가 있는지 확인해주세요.")
        return None

    exclude_patterns = [
        ":(exclude)package-lock.json", ":(exclude)yarn.lock", ":(exclude)pnpm-lock.yaml",
        ":(exclude)*.map", ":(exclude)dist/", ":(exclude)build/", 
        ":(exclude)node_modules/", ":(exclude).next/", ":(exclude).git/", ":(exclude).DS_Store"
    ]

    try:
        combined_result = ""
        today_midnight = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 1. 오늘자 커밋
        # git log가 실패하는 경우(커밋이 없는 새 레포 등)를 대비
        try:
            cmd_log = ["git", "-C", str(path), "log", f"--since={today_midnight.isoformat()}", "-p", "--", "."] + exclude_patterns
            log_output = subprocess.check_output(cmd_log, stderr=subprocess.STDOUT).decode("utf-8")
            if log_output.strip():
                combined_result += "=== [Past Commits (Today)] ===\n" + log_output + "\n\n"
        except subprocess.CalledProcessError:
            pass # 로그 없음 혹은 에러 무시

        # 2. 미커밋 변경사항
        try:
            cmd_diff = ["git", "-C", str(path), "diff", "HEAD", "--", "."] + exclude_patterns
            diff_output = subprocess.check_output(cmd_diff, stderr=subprocess.STDOUT).decode("utf-8")
            if diff_output.strip():
                combined_result += "=== [Uncommitted Current Work] ===\n" + diff_output + "\n"
        except subprocess.CalledProcessError:
            pass

        return combined_result if combined_result.strip() else None

    except Exception:
        return None


# 0. 런타임 환경 점검 함수 정의
def check_environment():
    """실행 전 필수 의존성 및 환경 점검"""
    try:
        import google.genai
        import openai
        import dotenv
    except ImportError as e:
        print(f"❌ [Critical Error] 필수 라이브러리가 설치되지 않았습니다: {e}")
        print("   👉 'pip install claw-log --force-reinstall'을 시도해보세요.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Claw-Log: 커리어 자동 기록 도구")
    parser.add_argument("--install-schedule", action="store_true", help="자동 스케줄러 등록")
    parser.add_argument("--reset", action="store_true", help="설정 초기화 및 마법사 재실행")
    args = parser.parse_args()

    # 0. 런타임 환경 점검 (Pre-flight Check)
    check_environment()

    # 1. Reset 요청 시 기존 설정 파일 삭제 (확실한 초기화)
    if args.reset and ENV_PATH.exists():
        try:
            ENV_PATH.unlink()
            print("🔄 기존 설정을 초기화했습니다.")
        except Exception as e:
            print(f"⚠️ 설정 파일 삭제 실패: {e}")

    # 2. 우선 환경변수 로드 시도 (override=True)
    load_dotenv(ENV_PATH, override=True)
    
    # 2. 마법사 실행 조건 체크
    # - 사용자가 --reset을 명시했거나
    # - .env 파일이 아예 없거나
    # - .env는 있는데 핵심 설정값(API_KEY, LLM_TYPE)이 비어있을 때
    required_vars_missing = not os.getenv("API_KEY") or not os.getenv("LLM_TYPE")
    should_run_wizard = args.reset or not ENV_PATH.exists() or required_vars_missing

    if should_run_wizard:
        run_wizard()
        # 마법사 종료 후, 방금 저장된 따끈따끈한 설정을 다시 메모리에 반영
        load_dotenv(ENV_PATH, override=True)

    # 3. 스케줄러 등록 모드면 여기서 종료
    if args.install_schedule:
        install_schedule()
        return

    # 4. 설정 로드 및 최종 검증
    llm_type = os.getenv("LLM_TYPE", "gemini").lower()
    api_key = os.getenv("API_KEY")
    paths_env = os.getenv("PROJECT_PATHS", "")

    if not api_key:
        print("❌ API Key가 설정되지 않았습니다. 마법사를 완료하거나 .env 파일을 확인해주세요.")
        return

    # Summarizer 초기화
    summarizer = None
    if llm_type == "openai":
        summarizer = OpenAISummarizer(api_key)
    else:
        summarizer = GeminiSummarizer(api_key)
    
    print(f"🚀 Claw-Log 분석 시작 (Engine: {llm_type.upper()})...")

    # Git 데이터 수집
    target_paths = [p.strip() for p in paths_env.split(",") if p.strip()]
    combined_diffs = ""
    
    for p_str in target_paths:
        diff = get_git_diff_for_path(p_str)
        if diff:
            p_name = os.path.basename(p_str)
            print(f"  ✅ [{p_name}] 데이터 수집 완료")
            combined_diffs += f"\n--- PROJECT: {p_name} ---\n{diff[:15000]}\n"

    if not combined_diffs:
        print("⚠️  오늘 변경사항이 발견되지 않았습니다. (종료)")
        return

    # 요약 및 저장
    print("🤖 AI 요약 생성 중...")
    summary = summarizer.summarize(combined_diffs)
    
    # 에러 체크 로직 개선 (실패 메시지로 시작하는 경우만 실패 처리)
    if summary and not summary.startswith(("Gemini 요약 생성 실패", "OpenAI 요약 생성 실패")):
        saved_file = prepend_to_log_file(summary)
        print(f"\n💾 기록 완료: {saved_file}")
        print("\n" + "="*60 + f"\n{summary}\n" + "="*60)
    else:
        print(f"❌ 요약 실패: {summary}")

if __name__ == "__main__":
    main()
