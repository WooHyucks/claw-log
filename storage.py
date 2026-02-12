
import datetime
from pathlib import Path
import os

def prepend_to_log_file(summary, filename="career_logs.md", date_label=None):
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
