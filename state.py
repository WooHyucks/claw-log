"""
Claw-Log State Module
커밋 추적 상태를 관리하는 모듈. Atomic write + 단일 인스턴스 PID 락으로 안전하게 저장.
"""

import json
import os
import datetime
import time
from pathlib import Path

# oauth.py:30 패턴 재사용
STATE_DIR = Path.home() / ".claw-log"
STATE_FILE = STATE_DIR / "commit_state.json"
RUN_LOCK_FILE = STATE_DIR / "claw_log.pid"  # 단일 인스턴스 보호용 PID 파일


def load_state():
    """상태 파일을 로드. 파일 없으면 빈 구조체 반환. 손상 시 .bak 백업 + 경고."""
    if not STATE_FILE.exists():
        return {"version": 1, "projects": {}}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "projects" not in data:
            raise ValueError("Invalid state structure")
        return data
    except (json.JSONDecodeError, ValueError):
        # .bak 백업 + 경고
        bak = STATE_FILE.with_suffix(f".bak.{int(time.time())}")
        try:
            os.replace(str(STATE_FILE), str(bak))
            print(f"  ⚠️  상태 파일 손상 → 백업: {bak}")
        except OSError:
            pass
        return {"version": 1, "projects": {}}


def save_state(pending_hashes):
    """pending_hashes를 상태 파일에 원자적으로 병합 저장.

    Args:
        pending_hashes: {repo_key: commit_hash} 딕셔너리 — 이번 실행에서 처리 완료된 해시
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    current = load_state()
    now = datetime.datetime.now().isoformat()
    for repo_key, commit_hash in pending_hashes.items():
        current["projects"][repo_key] = {
            "last_commit_hash": commit_hash,
            "last_run_at": now,
        }
    tmp_path = STATE_FILE.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(str(tmp_path), str(STATE_FILE))


def get_last_hash(state, repo_key):
    """repo_key에 해당하는 마지막 처리 커밋 해시 반환. 없으면 None."""
    entry = state.get("projects", {}).get(repo_key)
    return entry["last_commit_hash"] if entry else None


def acquire_run_lock():
    """단일 인스턴스 보장. 이미 실행 중이면 에러 메시지 반환, 성공 시 None 반환."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(RUN_LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return None  # 성공
    except FileExistsError:
        # stale 락 체크: PID가 살아있는지 확인
        try:
            pid_str = RUN_LOCK_FILE.read_text(encoding="utf-8").strip()
            pid = int(pid_str)
            os.kill(pid, 0)  # 신호 없이 프로세스 존재만 확인
            return f"claw-log가 이미 실행 중입니다 (PID: {pid}). 잠시 후 다시 시도하세요."
        except (OSError, ValueError):
            # 프로세스가 죽었거나 PID 파싱 실패 → stale 락 제거 후 재시도
            try:
                os.remove(str(RUN_LOCK_FILE))
            except OSError:
                pass
            return acquire_run_lock()


def release_run_lock():
    """PID 락 파일 제거."""
    try:
        os.remove(str(RUN_LOCK_FILE))
    except OSError:
        pass
