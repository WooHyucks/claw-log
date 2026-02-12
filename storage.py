import re
import datetime
from pathlib import Path
import os

LOG_FILENAME = "career_logs.md"


def read_recent_logs(n=5, filename=LOG_FILENAME):
    """최근 N개의 로그 엔트리를 반환합니다. 각 엔트리는 '## 📅' 헤더로 구분."""
    file_path = Path.cwd() / filename

    if not file_path.exists():
        return None, "로그 파일이 없습니다. 먼저 'claw-log'를 실행하세요."

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return None, f"로그 파일 읽기 실패: {e}"

    if not content.strip():
        return None, "로그 파일이 비어있습니다."

    # ## 📅 날짜 헤더로 엔트리 분할
    parts = re.split(r"(?=^## 📅 )", content, flags=re.MULTILINE)
    entries = [p.rstrip().rstrip("-").rstrip() for p in parts if p.strip()]

    if not entries:
        return None, "로그 엔트리를 찾을 수 없습니다."

    return entries[:n], None


def prepend_to_log_file(summary, filename=LOG_FILENAME, date_label=None):
    """
    현재 작업 디렉토리(CWD) 기준의 로그 파일 최상단에 새로운 로그를 추가합니다. (최신순)
    date_label: 커스텀 날짜 레이블 (예: "2026-02-06 ~ 2026-02-12"). None이면 오늘 날짜.
    """
    file_path = Path.cwd() / filename
    existing_content = ""

    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                existing_content = f.read()
        except Exception as e:
            print(f"⚠️ 기존 로그 파일 읽기 실패: {e}")

    label = date_label if date_label else datetime.date.today().strftime("%Y-%m-%d")
    header = f"## 📅 {label}\n\n"
    separator = "\n---\n\n"
    
    # 최신 내용이 뒤에 오는 것이 아니라 앞에 오도록 (Prepend)
    final_content = header + summary + separator + existing_content
    
    # 파일 쓰기
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_content)
        return file_path
    except Exception as e:
        print(f"❌ 로그 파일 저장 실패: {e}")
        return None
