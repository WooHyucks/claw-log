"""
Claw-Log OAuth Module
ChatGPT Plus/Pro 구독자를 위한 OAuth 2.0 PKCE 인증 흐름.
OpenAI Codex CLI와 동일한 공식 OAuth 엔드포인트를 사용합니다.
"""

import json
import os
import sys
import time
import hashlib
import secrets
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, urlparse, parse_qs
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from pathlib import Path
from threading import Thread

# --- OAuth 설정 (OpenAI Codex CLI 공식 값) ---
CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
AUTH_URL = "https://auth.openai.com/oauth/authorize"
TOKEN_URL = "https://auth.openai.com/oauth/token"
REDIRECT_URI = "http://localhost:1455/auth/callback"
CALLBACK_PORT = 1455
AUDIENCE = "https://api.openai.com/v1"
SCOPE = "openid profile email offline_access"

# 토큰 저장 경로
TOKEN_DIR = Path.home() / ".claw-log"
TOKEN_FILE = TOKEN_DIR / "oauth_tokens.json"


# =============================================================================
#  PKCE 유틸리티
# =============================================================================

def _generate_pkce():
    """PKCE code_verifier / code_challenge 쌍 생성"""
    verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = (
        digest.hex()  # fallback
    )
    # base64url 인코딩 (패딩 제거)
    import base64
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def _generate_state():
    """CSRF 방지용 state 값 생성"""
    return secrets.token_urlsafe(16)


# =============================================================================
#  OAuth 콜백 서버
# =============================================================================

class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    """로컬 콜백 서버 핸들러 - OAuth redirect를 수신합니다."""
    
    authorization_code = None
    received_state = None
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == "/auth/callback":
            params = parse_qs(parsed.query)
            _OAuthCallbackHandler.authorization_code = params.get("code", [None])[0]
            _OAuthCallbackHandler.received_state = params.get("state", [None])[0]
            
            # 성공 페이지 응답
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            success_html = """
            <html><body style="font-family:sans-serif;text-align:center;padding:60px;">
            <h1>✅ 인증 완료!</h1>
            <p>Claw-Log에 성공적으로 로그인되었습니다.</p>
            <p>이 창을 닫고 터미널로 돌아가세요.</p>
            </body></html>
            """
            self.wfile.write(success_html.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """HTTP 서버 로그 억제"""
        pass


# =============================================================================
#  토큰 관리
# =============================================================================

def save_tokens(tokens: dict):
    """토큰을 로컬 파일에 저장"""
    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    tokens["saved_at"] = int(time.time())
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2)
    # 권한 제한 (Unix 계열)
    try:
        os.chmod(TOKEN_FILE, 0o600)
    except OSError:
        pass


def load_tokens() -> dict | None:
    """저장된 토큰 로드"""
    if not TOKEN_FILE.exists():
        return None
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def refresh_if_needed(tokens: dict) -> dict:
    """토큰 만료 5분 전이면 자동 갱신"""
    expires_at = tokens.get("expires_at", 0)
    if time.time() + 300 < expires_at:
        return tokens  # 아직 유효
    
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        print("⚠️  Refresh token이 없습니다. 재로그인이 필요합니다.")
        return tokens
    
    print("🔄 OAuth 토큰 갱신 중...")
    try:
        new_tokens = _exchange_token({
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "refresh_token": refresh_token,
        })
        if new_tokens:
            # refresh_token이 응답에 없으면 기존 것 유지
            if "refresh_token" not in new_tokens:
                new_tokens["refresh_token"] = refresh_token
            save_tokens(new_tokens)
            print("   ✅ 토큰 갱신 완료")
            return new_tokens
    except Exception as e:
        print(f"   ⚠️ 토큰 갱신 실패: {e}")
    
    return tokens


def _exchange_token(params: dict) -> dict | None:
    """토큰 엔드포인트에 요청을 보내 토큰 교환"""
    data = urlencode(params).encode("utf-8")
    req = Request(
        TOKEN_URL,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        # expires_at 계산
        if "expires_in" in result:
            result["expires_at"] = int(time.time()) + result["expires_in"]
        return result
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"   ❌ 토큰 교환 실패 ({e.code}): {body[:200]}")
        return None


# =============================================================================
#  메인 로그인 흐름
# =============================================================================

def run_oauth_login() -> dict | None:
    """
    OAuth 2.0 PKCE 로그인 흐름 실행.
    1. 로컬 콜백 서버 시작
    2. 브라우저에서 auth.openai.com 로그인 페이지 열기
    3. 콜백으로 authorization code 수신
    4. code → access_token 교환
    5. 토큰 저장
    """
    verifier, challenge = _generate_pkce()
    state = _generate_state()
    
    # 인증 URL 구성
    auth_params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "audience": AUDIENCE,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    auth_url = f"{AUTH_URL}?{urlencode(auth_params)}"
    
    # 콜백 서버 초기화
    _OAuthCallbackHandler.authorization_code = None
    _OAuthCallbackHandler.received_state = None
    
    try:
        server = HTTPServer(("localhost", CALLBACK_PORT), _OAuthCallbackHandler)
    except OSError as e:
        print(f"   ❌ 포트 {CALLBACK_PORT}이 이미 사용 중입니다.")
        print(f"      Codex CLI가 실행 중이라면 먼저 종료해주세요.")
        return None
    
    # 서버를 백그라운드에서 실행
    server_thread = Thread(target=server.handle_request, daemon=True)
    server_thread.start()
    
    # 브라우저 열기
    print(f"\n   🌐 브라우저에서 ChatGPT 로그인 페이지를 엽니다...")
    print(f"   (자동으로 열리지 않으면 아래 URL을 직접 복사해서 열어주세요)")
    print(f"   {auth_url[:80]}...")
    webbrowser.open(auth_url)
    
    # 콜백 대기 (최대 120초)
    print(f"\n   ⏳ 브라우저에서 로그인 완료를 기다리는 중... (최대 2분)")
    server_thread.join(timeout=120)
    server.server_close()
    
    code = _OAuthCallbackHandler.authorization_code
    received_state = _OAuthCallbackHandler.received_state
    
    if not code:
        print("   ❌ 시간 초과 또는 인증 코드를 받지 못했습니다.")
        return None
    
    if received_state != state:
        print("   ❌ State 불일치 - CSRF 공격 가능성. 로그인을 중단합니다.")
        return None
    
    # Authorization code → Token 교환
    print("   🔑 토큰 교환 중...")
    tokens = _exchange_token({
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": verifier,
    })
    
    if not tokens or "access_token" not in tokens:
        print("   ❌ 토큰 교환에 실패했습니다.")
        return None
    
    save_tokens(tokens)
    return tokens