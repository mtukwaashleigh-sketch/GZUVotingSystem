"""Admin authentication for the GZU Voting System."""

import os
import time
import secrets
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from urllib.parse import urlsplit

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

logger = logging.getLogger("gzu.admin.audit")

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 15 * 60

_attempts = {}
_attempts_lock = Lock()


# =========================================================
# Login attempt protection
# =========================================================

def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _login_locked(request: Request) -> bool:
    now = time.time()
    key = _client_key(request)

    with _attempts_lock:
        record = _attempts.get(key)

        if not record:
            return False

        start_time, count = record

        if count >= MAX_FAILED_ATTEMPTS:
            if now - start_time < LOCKOUT_SECONDS:
                return True

            _attempts.pop(key, None)

        elif now - start_time >= LOCKOUT_SECONDS:
            _attempts.pop(key, None)

    return False


def _record_failed_login(request: Request) -> None:
    now = time.time()
    key = _client_key(request)

    with _attempts_lock:
        record = _attempts.get(key)

        if not record or now - record[0] >= LOCKOUT_SECONDS:
            _attempts[key] = (now, 1)
        else:
            _attempts[key] = (record[0], record[1] + 1)


def _clear_failed_logins(request: Request) -> None:
    with _attempts_lock:
        _attempts.pop(_client_key(request), None)


# =========================================================
# Verify administrator credentials
# =========================================================

def verify_admin_credentials(
    username: str,
    password: str,
    request: Request,
) -> bool:
    if _login_locked(request):
        logger.warning(
            "admin_login_throttled ip=%s",
            _client_key(request),
        )
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Try again later.",
        )

    configured_username = os.getenv("ADMIN_USERNAME", "")
    password_hash = os.getenv("ADMIN_PASSWORD_HASH", "")

    if not configured_username or not password_hash:
        logger.error("Admin credentials are not configured.")
        raise HTTPException(
            status_code=503,
            detail="Admin login is not configured.",
        )

    try:
        username_ok = secrets.compare_digest(
            username,
            configured_username,
        )
        password_ok = bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except (ValueError, TypeError):
        logger.exception("Invalid admin password hash configuration.")
        raise HTTPException(
            status_code=503,
            detail="Admin authentication is misconfigured.",
        )

    if not (username_ok and password_ok):
        _record_failed_login(request)
        logger.warning(
            "admin_login_failed ip=%s",
            _client_key(request),
        )
        return False

    _clear_failed_logins(request)
    logger.info(
        "admin_login_success ip=%s",
        _client_key(request),
    )
    return True


# =========================================================
# Same-origin / CSRF protection
# =========================================================

def _normalized_origin(value: str):
    """Normalize an HTTP(S) URL into (scheme, hostname, port)."""
    try:
        parsed = urlsplit(value.strip())

        if parsed.scheme.lower() not in ("http", "https"):
            return None

        if not parsed.hostname or parsed.username or parsed.password:
            return None

        scheme = parsed.scheme.lower()
        hostname = parsed.hostname.lower().rstrip(".")
        port = parsed.port

        if port is None:
            port = 443 if scheme == "https" else 80

        return scheme, hostname, port

    except (ValueError, AttributeError):
        return None


def _allowed_admin_origins(request: Request) -> set:
    """
    Read explicitly trusted origins from ADMIN_ALLOWED_ORIGINS.
    Example:
    ADMIN_ALLOWED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
    """
    configured = os.getenv("ADMIN_ALLOWED_ORIGINS", "")
    allowed = set()

    for value in configured.split(","):
        value = value.strip()
        if value:
            normalized = _normalized_origin(value)
            if normalized:
                allowed.add(normalized)

    # Trust the origin used to reach this application as well.
    own_origin = _normalized_origin(str(request.base_url))
    if own_origin:
        allowed.add(own_origin)

    return allowed


def _same_origin(request: Request) -> bool:
    """Allow only requests from configured or application origins."""
    allowed = _allowed_admin_origins(request)

    origin = request.headers.get("origin", "").strip()
    referer = request.headers.get("referer", "").strip()

    # Prefer Origin when the browser provides a usable value.
    if origin and origin.lower() != "null":
        actual = _normalized_origin(origin)
        return actual is not None and actual in allowed

    # Use Referer only when Origin is absent or opaque.
    if referer:
        actual = _normalized_origin(referer)
        return actual is not None and actual in allowed

    # Fail closed if the browser provides no verifiable origin.
    logger.warning(
        "origin_check_failed path=%s reason=missing_origin_and_referer",
        request.url.path,
    )
    return False


# =========================================================
# Browser session authentication
# =========================================================

async def require_admin(request: Request) -> str:
    if not request.session.get("admin_authenticated"):
        raise HTTPException(
            status_code=303,
            detail="Administrator login required",
            headers={"Location": "/admin/login"},
        )

    # Keep a session-bound token available to every admin HTML page.
    # HTML forms must include this value as a hidden csrf_token field.
    if request.method.upper() in {"GET", "HEAD"}:
        request.session.setdefault("admin_review_csrf", secrets.token_urlsafe(32))

    if request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
        # Require the session-bound token for every state-changing browser request,
        # regardless of whether the browser sent Origin/Referer headers.
        expected_token = request.session.get("admin_review_csrf", "")
        try:
            form = await request.form()
            supplied_token = str(form.get("csrf_token", ""))
        except Exception:
            supplied_token = ""

        if (
            not expected_token
            or not supplied_token
            or not secrets.compare_digest(supplied_token, expected_token)
        ):
            logger.warning(
                "csrf_check_failed path=%s reason=missing_or_invalid_token",
                request.url.path,
            )
            raise HTTPException(
                status_code=403,
                detail="Request security token missing or invalid. Reload the page and try again.",
            )

        # A valid session-bound CSRF token is always required above. If the
        # browser supplies Origin/Referer, additionally enforce same-origin.
        # Some local/proxy/browser form submissions omit both headers; do not
        # reject those solely for missing headers after the CSRF token passed.
        origin = request.headers.get("origin", "").strip()
        referer = request.headers.get("referer", "").strip()
        if ((origin and origin.lower() != "null") or referer) and not _same_origin(request):
            logger.warning(
                "origin_check_failed path=%s reason=origin_mismatch",
                request.url.path,
            )
            raise HTTPException(
                status_code=403,
                detail="Cross-origin request rejected.",
            )

    return str(request.session.get("admin_username", "admin"))


# =========================================================
# Admin API login and bearer-token authentication
# =========================================================

api_router = APIRouter()


class AdminApiLogin(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=256)


@api_router.post("/admin/api/login")
def admin_api_login(
    payload: AdminApiLogin,
    request: Request,
):
    if not verify_admin_credentials(
        payload.username,
        payload.password,
        request,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid admin username or password",
        )

    token_secret = os.getenv("ADMIN_TOKEN_SECRET", "")

    if len(token_secret) < 32:
        raise HTTPException(
            status_code=503,
            detail="Admin API authentication is not configured securely.",
        )

    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": os.getenv("ADMIN_USERNAME"),
            "role": "admin",
            "iat": now,
            "exp": now + timedelta(minutes=30),
        },
        token_secret,
        algorithm="HS256",
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 1800,
    }


_bearer = HTTPBearer(auto_error=False)


def require_admin_api(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Admin bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_secret = os.getenv("ADMIN_TOKEN_SECRET", "")

    if len(token_secret) < 32:
        raise HTTPException(
            status_code=503,
            detail="Admin API authentication is not configured securely.",
        )

    try:
        claims = jwt.decode(
            credentials.credentials,
            token_secret,
            algorithms=["HS256"],
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired admin token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if (
        claims.get("role") != "admin"
        or claims.get("sub") != os.getenv("ADMIN_USERNAME")
    ):
        raise HTTPException(
            status_code=403,
            detail="Administrator privileges required",
        )

    return claims


# =========================================================
# Admin login page
# =========================================================

auth_router = APIRouter()


def _login_page(error: str = "", csrf_token: str = "") -> str:
    escaped_error = (
        error.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#039;")
    )

    error_html = (
        f'<p role="alert" style="color:#b91c1c">'
        f'{escaped_error}</p>'
        if error
        else ""
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Admin Login | GZU Voting</title>
<style>
body {{
    font-family: Arial, sans-serif;
    background: #f3f6f4;
    margin: 0;
    min-height: 100vh;
    display: grid;
    place-items: center;
    color: #1f2937;
}}
main {{
    background: white;
    width: min(92vw, 390px);
    padding: 30px;
    border-radius: 14px;
    box-shadow: 0 10px 35px #0001;
}}
h1 {{ font-size: 24px; margin-top: 0; }}
label {{ display: block; font-weight: 600; margin: 16px 0 6px; }}
input {{
    width: 100%;
    box-sizing: border-box;
    padding: 12px;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
}}
button {{
    width: 100%;
    margin-top: 22px;
    padding: 12px;
    background: #087f3e;
    color: white;
    border: 0;
    border-radius: 8px;
    font-weight: 700;
    cursor: pointer;
}}
.hint {{ color: #64748b; font-size: 13px; }}
</style>
</head>
<body>
<main>
<h1>Administrator sign in</h1>
<p class="hint">Great Zimbabwe University Voting System</p>
{error_html}
<form method="post" action="/admin/login" autocomplete="on">
<input type="hidden" name="csrf_token" value="{csrf_token}">
<label for="username">Admin username</label>
<input id="username" name="username" required
       maxlength="120" autocomplete="username">
<label for="password">Password</label>
<input id="password" name="password" type="password"
       required autocomplete="current-password">
<button type="submit">Sign in</button>
</form>
</main>
</body>
</html>"""


@auth_router.get("/admin/login", response_class=HTMLResponse)
def admin_login_page(request: Request):
    if request.session.get("admin_authenticated"):
        return RedirectResponse("/admin", status_code=303)

    # Generate a one-time CSRF token and store it in the signed session.
    csrf_token = secrets.token_urlsafe(32)
    request.session["admin_login_csrf"] = csrf_token
    return HTMLResponse(_login_page(csrf_token=csrf_token))


@auth_router.post("/admin/login", response_class=HTMLResponse)
def admin_login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
):
    expected_token = request.session.get("admin_login_csrf", "")

    if (
        not expected_token
        or not secrets.compare_digest(csrf_token, expected_token)
    ):
        raise HTTPException(
            status_code=403,
            detail="Login form expired or invalid. Reload the login page and try again.",
        )

    # Validate browser origin when the browser supplies usable headers.
    origin = request.headers.get("origin", "").strip()
    referer = request.headers.get("referer", "").strip()

    if (origin and origin.lower() != "null") or referer:
        if not _same_origin(request):
            raise HTTPException(
                status_code=403,
                detail="Cross-origin login rejected.",
            )

    # Consume the token before checking credentials.
    request.session.pop("admin_login_csrf", None)

    if not verify_admin_credentials(username.strip(), password, request):
        new_token = secrets.token_urlsafe(32)
        request.session["admin_login_csrf"] = new_token
        return HTMLResponse(
            _login_page(
                "Invalid username or password.",
                csrf_token=new_token,
            ),
            status_code=401,
        )

    # Rotate session contents after successful authentication.
    request.session.clear()
    request.session["admin_authenticated"] = True
    request.session["admin_username"] = os.getenv("ADMIN_USERNAME")
    request.session["admin_login_time"] = int(time.time())
    return RedirectResponse("/admin", status_code=303)


# =========================================================
# Admin logout
# =========================================================

@auth_router.get("/admin/logout")
def admin_logout_get(request: Request):
    """End the current admin browser session from the dashboard logout link."""
    username = request.session.get("admin_username", "unknown")
    request.session.clear()
    logger.info(
        "admin_logout username=%s ip=%s",
        username,
        _client_key(request),
    )
    return RedirectResponse("/admin/login", status_code=303)


@auth_router.post("/admin/logout")
def admin_logout(request: Request):
    if not request.session.get("admin_authenticated"):
        return RedirectResponse("/admin/login", status_code=303)

    if not _same_origin(request):
        raise HTTPException(
            status_code=403,
            detail="Cross-origin logout rejected.",
        )

    username = request.session.get("admin_username", "unknown")
    request.session.clear()

    logger.info(
        "admin_logout username=%s ip=%s",
        username,
        _client_key(request),
    )

    return RedirectResponse("/admin/login", status_code=303)
