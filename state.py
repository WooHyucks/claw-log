"""
Claw-Log State Module
커밋 추적 상태를 관리하는 모듈. Atomic write + cross-process 파일 락으로 안전하게 저장.
"""

import json
import os
import datetime
import time
from pathlib import Path

# oauth.py:30 패턴 재사용
STATE_DIR = Path.home() / ".claw-log"
STATE_FILE = STATE_DIR / "commit_state.json"
LOCK_FILE = STATE_DIR / "commit_state.lock"
LOCK_TIMEOUT = 10  # seconds


def _acquire_lock():
    """cross-process 파일 락 획득. 타임아웃 시 stale 락 제거."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + LOCK_TIMEOUT
    while True:
        try:
            fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return
        except FileExistsError:
            # stale 락 체크
            try:
                age = time.time() - os.path.getmtime(str(LOCK_FILE))
                if age > LOCK_TIMEOUT * 3:
                    os.remove(str(LOCK_FILE))
                    continue
            except OSError:
                pass
            if time.time() > deadline:
                # timeout 초과 → 강제 해제
                try:
                    os.remove(str(LOCK_FILE))
                except OSError:
                    pass
                continue
            time.sleep(0.1)


def _release_lock():
    try:
        os.remove(str(LOCK_FILE))
    except OSError:
        pass


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
        # R2-#4: .bak 백업 + 경고
        bak = STATE_FILE.with_suffix(f".bak.{int(time.time())}")
        try:
            os.replace(str(STATE_FILE), str(bak))
            print(f"  ⚠️  상태 파일 손상 → 백업: {bak}")
        except OSError:
            pass
        return {"version": 1, "projects": {}}


def save_state(state):
    """파일 락 + Atomic write로 상태 저장."""
    _acquire_lock()
    try:
        # 락 내에서 최신 상태 재로드 후 merge (R2-#2: concurrent update 방지)
        current = load_state()
        for key, val in state.get("projects", {}).items():
            current["projects"][key] = val
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        tmp_path = STATE_FILE.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(str(tmp_path), str(STATE_FILE))
    finally:
        _release_lock()


def get_last_hash(state, repo_key):
    """repo_key에 해당하는 마지막 처리 커밋 해시 반환. 없으면 None."""
    entry = state.get("projects", {}).get(repo_key)
    return entry["last_commit_hash"] if entry else None


def update_last_hash(state, repo_key, commit_hash):
    """repo_key의 마지막 처리 해시와 실행 시각 업데이트."""
    if "projects" not in state:
        state["projects"] = {}
    state["projects"][repo_key] = {
        "last_commit_hash": commit_hash,
        "last_run_at": datetime.datetime.now().isoformat()
    }
    return state
