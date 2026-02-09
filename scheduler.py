
import os
import sys
import subprocess
import platform
from pathlib import Path

SCHEDULER_LOG = "scheduler.log"

def install_schedule():
    """
    OS별 스케줄러 등록 (매일 23:30 실행)
    라이브러리로 실행되므로 'python -m claw_log.main' 명령어를 등록합니다.
    """
    system = platform.system()
    python_executable = sys.executable
    
    # 현재 작업 디렉토리 (사용자가 스케줄링을 등록한 위치)
    cwd = os.getcwd()
    log_file_path = os.path.join(cwd, SCHEDULER_LOG)
    
    # 실행할 명령어 구성: 해당 디렉토리로 이동 후 모듈 실행
    # 이렇게 하면 .env나 career_logs.md를 해당 디렉토리에서 찾을 수 있음
    cmd_str = f"cd {cwd} && {python_executable} -m claw_log.main >> {log_file_path} 2>&1"
    
    print(f"\n🕒 [{system}] 스케줄러 등록 작업 시작...")
    print(f"   - 실행 경로: {cwd}")
    print(f"   - 로그 파일: {log_file_path}")

    if system == "Windows":
        task_name = "ClawLog_Daily"
        # Windows schtasks 명령어
        # 리다이렉션을 위해 cmd /c 사용
        win_cmd = f'cmd /c "{cmd_str}"'
        
        try:
            subprocess.run([
                "schtasks", "/Create", "/SC", "DAILY", "/TN", task_name,
                "/TR", win_cmd, "/ST", "23:30", "/F"
            ], check=True)
            print(f"✅ Windows 작업 스케줄러에 '{task_name}' 등록 완료!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Windows 스케줄러 등록 실패: {e}")

    else:  # Mac / Linux
        # Crontab 명령어 구성
        cron_job = f"30 23 * * * {cmd_str}"
        comment = "# ClawLog Daily Schedule"
        
        try:
            # 기존 크론탭 읽기
            current_cron = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
            
            # 기존 스케줄 제거 (업데이트를 위해)
            lines = current_cron.splitlines()
            new_lines = [line for line in lines if "claw_log.main" not in line and comment not in line]
            
            # 새 스케줄 추가
            new_cron = "\n".join(new_lines) + f"\n{comment}\n{cron_job}\n"
            
            # 새 크론탭 적용
            process = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate(input=new_cron)
            
            if process.returncode == 0:
                print("✅ Crontab에 스케줄 등록/업데이트 완료! (매일 23:30)")
            else:
                print(f"❌ Crontab 등록 실패: {stderr}")
                
        except Exception as e:
            print(f"❌ Crontab 접근 실패: {e}")
