import asyncio
import math
import logging
import secrets
from pathlib import Path
from datetime import datetime, time as datetime_time, timedelta, timezone
from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

from pydantic import BaseModel

from auth import (
    generate_session_token,
    hash_password,
    hash_session_token,
    normalize_email,
    password_needs_rehash,
    verify_password,
)
from config import settings
from llm import SiliconflowLLM, OpenRouterLLM, StepLLM, ArkPlanLLM
from migrations import apply_migrations
from utils import get_or_cache_paper_content, get_openreview_info, ReaderError, OpenReviewError, truncate_content_for_llm
from hf_daily import sync_hf_daily_papers
from database import (
    DatabaseError,
    count_active_admins,
    create_chat_session,
    create_invitation_code,
    create_user_session,
    create_user_with_invitation,
    delete_chat_session,
    delete_invitation_code,
    delete_user,
    delete_last_chat_message_pair,
    ensure_admin_user,
    get_chat_messages,
    get_chat_session,
    get_chat_sessions_for_account,
    get_conference_papers,
    get_hf_daily_papers,
    get_paper,
    get_paper_marks,
    get_presence_counts,
    get_presence_trend,
    get_user_by_email,
    get_user_by_id,
    get_user_by_session_token_hash,
    has_hf_daily_papers_for_date,
    list_invitation_codes,
    list_marked_papers,
    list_users,
    migrate_anonymous_data,
    record_presence,
    record_presence_snapshot,
    revoke_session,
    revoke_user_sessions,
    save_chat_message,
    save_paper,
    search_all_papers,
    set_paper_mark,
    update_llm_response,
    update_invitation_code_max_uses,
    update_user_admin_fields,
    update_user_last_login,
    update_user_password,
)
from chat import ChatSession
from background_tasks import BackgroundAnalyzer
from markdown_utils import normalize_llm_markdown

logger = logging.getLogger(__name__)
INVITATION_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

llm = StepLLM()
chat_sessions: dict[str, ChatSession] = {}
background_analyzer = BackgroundAnalyzer(llm, check_interval=settings.background_analysis.check_interval_seconds)
background_task = None
presence_snapshot_task = None
hf_daily_task = None
hf_daily_analysis_tasks: set[asyncio.Task] = set()


async def run_presence_snapshots():
    while True:
        try:
            await asyncio.to_thread(
                record_presence_snapshot,
                settings.presence.online_timeout_seconds,
                settings.presence.retention_days,
            )
        except DatabaseError as exc:
            logger.warning("在线人数快照写入失败: %s", exc)
        await asyncio.sleep(settings.presence.snapshot_interval_seconds)


def get_hf_daily_timezone() -> ZoneInfo:
    try:
        return ZoneInfo(settings.hf_daily.timezone)
    except ZoneInfoNotFoundError:
        logger.warning("HF Daily timezone 无效，回退到 UTC: %s", settings.hf_daily.timezone)
        return ZoneInfo("UTC")


def get_hf_daily_fetch_time() -> datetime_time:
    raw_value = settings.hf_daily.fetch_time.strip()
    try:
        hour_text, minute_text = raw_value.split(":", 1)
        hour = int(hour_text)
        minute = int(minute_text)
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return datetime_time(hour=hour, minute=minute)
    except (ValueError, AttributeError):
        pass

    logger.warning("HF Daily fetch_time 无效，回退到 22:00: %s", raw_value)
    return datetime_time(hour=22, minute=0)


async def analyze_hf_daily_papers(paper_ids: list[str]) -> None:
    if not paper_ids:
        return
    if not llm.is_configured():
        logger.warning("HF Daily 已入库，但 LLM 未配置，跳过自动分析")
        return

    seen: set[str] = set()
    for paper_id in paper_ids:
        if paper_id in seen:
            continue
        seen.add(paper_id)
        await background_analyzer.analyze_paper(paper_id)
        await asyncio.sleep(1)


def schedule_hf_daily_analysis(paper_ids: list[str]) -> None:
    if not paper_ids:
        return
    task = asyncio.create_task(analyze_hf_daily_papers(paper_ids))
    hf_daily_analysis_tasks.add(task)

    def finalize(completed_task: asyncio.Task) -> None:
        hf_daily_analysis_tasks.discard(completed_task)
        try:
            completed_task.result()
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.warning("HF Daily 自动分析任务失败: %s", exc)

    task.add_done_callback(finalize)


async def sync_hf_daily_once() -> dict:
    tz = get_hf_daily_timezone()
    daily_date = datetime.now(tz).date()
    result = await asyncio.to_thread(
        sync_hf_daily_papers,
        settings.hf_daily.api_url,
        settings.hf_daily.top_n,
        daily_date,
    )
    schedule_hf_daily_analysis(result.get("analyzable_paper_ids", []))
    return result


async def run_hf_daily_scheduler():
    logger.info(
        "HF Daily 定时任务启动: enabled=%s time=%s timezone=%s top_n=%s",
        settings.hf_daily.enabled,
        settings.hf_daily.fetch_time,
        settings.hf_daily.timezone,
        settings.hf_daily.top_n,
    )
    while True:
        tz = get_hf_daily_timezone()
        fetch_time = get_hf_daily_fetch_time()
        now = datetime.now(tz)
        today_run_at = datetime.combine(now.date(), fetch_time, tzinfo=tz)

        try:
            if now >= today_run_at:
                already_synced = await asyncio.to_thread(has_hf_daily_papers_for_date, now.date())
                if not already_synced:
                    logger.info("开始补抓今日 HF Daily Papers: %s", now.date().isoformat())
                    await sync_hf_daily_once()
                    now = datetime.now(tz)

            next_run_date = now.date()
            if now >= datetime.combine(next_run_date, fetch_time, tzinfo=tz):
                next_run_date = next_run_date + timedelta(days=1)
            next_run_at = datetime.combine(next_run_date, fetch_time, tzinfo=tz)
            await asyncio.sleep(max((next_run_at - now).total_seconds(), 60))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("HF Daily 定时任务失败，1 小时后重试: %s", exc)
            await asyncio.sleep(3600)


def bootstrap_admin_user() -> None:
    if not settings.admin.email or not settings.admin.initial_password:
        logger.info("未配置 admin.email/admin.initial_password，跳过初始管理员创建")
        return

    normalized = normalize_email(settings.admin.email)
    ensure_admin_user(
        settings.admin.email.strip(),
        normalized,
        hash_password(settings.admin.initial_password),
    )
    logger.info("初始管理员已确认: %s", normalized)


def ensure_llm_configured() -> None:
    if not llm.is_configured():
        raise HTTPException(status_code=503, detail="LLM API key is not configured in config.yaml")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global background_task, presence_snapshot_task, hf_daily_task
    try:
        await asyncio.to_thread(apply_migrations)
    except Exception as exc:
        logger.error("数据库 migration 失败: %s", exc)
        raise

    try:
        await asyncio.to_thread(bootstrap_admin_user)
    except DatabaseError as exc:
        logger.warning("初始管理员创建失败: %s", exc)

    if settings.background_analysis.enabled and llm.is_configured():
        background_task = asyncio.create_task(background_analyzer.run())
        logger.info("后台分析任务已启动")
    elif settings.background_analysis.enabled:
        logger.warning("已启用后台分析，但 config.yaml 未配置有效 LLM API key，跳过后台分析")
    else:
        logger.info("后台分析任务未启用")

    presence_snapshot_task = asyncio.create_task(run_presence_snapshots())
    if settings.hf_daily.enabled:
        hf_daily_task = asyncio.create_task(run_hf_daily_scheduler())
    else:
        logger.info("HF Daily 定时任务未启用")

    yield

    background_analyzer.stop()
    for task in (background_task, presence_snapshot_task, hf_daily_task, *hf_daily_analysis_tasks):
        if not task:
            continue
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    logger.info("后台分析任务已停止")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors.allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: str | None = None


class AuthRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(AuthRequest):
    invitation_code: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class PaperMarkPayload(BaseModel):
    viewed: bool | None = None
    liked: bool | None = None


class AnonymousMigrationRequest(BaseModel):
    anonymous_user_id: str | None = None
    paper_marks: dict[str, PaperMarkPayload] = {}


class PresenceRequest(BaseModel):
    client_id: str | None = None
    user_id: str | None = None


class AdminUserUpdateRequest(BaseModel):
    role: str | None = None
    is_active: bool | None = None


class ResetPasswordRequest(BaseModel):
    password: str


class InvitationCodeCreateRequest(BaseModel):
    max_uses: int = 1


class InvitationCodeUpdateRequest(BaseModel):
    max_uses: int


def public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "is_active": user["is_active"],
        "email_verified": user["email_verified"],
        "created_at": user.get("created_at"),
        "last_login_at": user.get("last_login_at"),
    }


def validate_email_and_password(email: str, password: str) -> str:
    normalized = normalize_email(email)
    if "@" not in normalized or "." not in normalized.split("@")[-1]:
        raise HTTPException(status_code=400, detail="邮箱格式不正确")
    if len(password) < settings.auth.password_min_length:
        raise HTTPException(
            status_code=400,
            detail=f"密码至少需要 {settings.auth.password_min_length} 个字符",
        )
    return normalized


def normalize_invitation_code(code: str | None) -> str:
    return (code or "").strip().upper()


def generate_invitation_code() -> str:
    groups = [
        "".join(secrets.choice(INVITATION_CODE_ALPHABET) for _ in range(4))
        for _ in range(4)
    ]
    return f"PI-{'-'.join(groups)}"


def get_request_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else None


def set_session_cookie(response: Response, token: str) -> None:
    max_age = settings.auth.session_ttl_days * 24 * 3600
    response.set_cookie(
        key=settings.auth.session_cookie_name,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=settings.auth.cookie_secure,
        samesite=settings.auth.cookie_samesite,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.auth.session_cookie_name,
        path="/",
        samesite=settings.auth.cookie_samesite,
        secure=settings.auth.cookie_secure,
        httponly=True,
    )


def current_session_token(request: Request) -> str | None:
    return request.cookies.get(settings.auth.session_cookie_name)


def get_current_user_optional(request: Request) -> dict | None:
    token = current_session_token(request)
    if not token:
        return None
    return get_user_by_session_token_hash(hash_session_token(token))


def require_current_user(request: Request) -> dict:
    try:
        user = get_current_user_optional(request)
    except DatabaseError as exc:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from exc
    if not user:
        raise HTTPException(status_code=401, detail="请先登录")
    return user


def require_admin_user(user: dict = Depends(require_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


def create_login_session(user: dict, request: Request, response: Response) -> None:
    token = generate_session_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.auth.session_ttl_days)
    create_user_session(
        user["id"],
        hash_session_token(token),
        expires_at,
        request.headers.get("user-agent"),
        get_request_ip(request),
    )
    set_session_cookie(response, token)
    update_user_last_login(user["id"])


def assert_chat_owner(session_id: str, user_id: str) -> dict | None:
    session_row = get_chat_session(session_id)
    if session_row and session_row.get("account_user_id") != user_id:
        raise HTTPException(status_code=403, detail="无权访问该会话")
    return session_row


@app.post("/auth/register")
async def register(req: RegisterRequest, request: Request, response: Response):
    if not settings.auth.public_registration_enabled:
        raise HTTPException(status_code=403, detail="当前不开放注册")
    normalized = validate_email_and_password(req.email, req.password)
    invitation_code = normalize_invitation_code(req.invitation_code)
    if not invitation_code:
        raise HTTPException(status_code=400, detail="请填写邀请码")
    try:
        user, error = create_user_with_invitation(
            req.email.strip(),
            normalized,
            hash_password(req.password),
            hash_session_token(invitation_code),
            role="user",
            email_verified=not settings.auth.require_email_verification,
        )
        if error == "email_exists":
            raise HTTPException(status_code=409, detail="该邮箱已注册")
        if error == "invalid_invitation_code":
            raise HTTPException(status_code=400, detail="邀请码无效")
        if error == "invitation_code_exhausted":
            raise HTTPException(status_code=400, detail="邀请码使用次数已用完")
        if not user:
            raise HTTPException(status_code=400, detail="注册失败")
        create_login_session(user, request, response)
        return {"user": public_user(user)}
    except DatabaseError as exc:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from exc


@app.post("/auth/login")
async def login(req: AuthRequest, request: Request, response: Response):
    normalized = validate_email_and_password(req.email, req.password)
    try:
        user = get_user_by_email(normalized)
        if not user or not verify_password(user["password_hash"], req.password):
            raise HTTPException(status_code=401, detail="邮箱或密码错误")
        if not user["is_active"]:
            raise HTTPException(status_code=403, detail="账号已被停用")
        if password_needs_rehash(user["password_hash"]):
            update_user_password(user["id"], hash_password(req.password))
            user = get_user_by_id(user["id"]) or user
        create_login_session(user, request, response)
        return {"user": public_user(user)}
    except DatabaseError as exc:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from exc


@app.post("/auth/logout")
async def logout(request: Request, response: Response):
    token = current_session_token(request)
    if token:
        try:
            revoke_session(hash_session_token(token))
        except DatabaseError as exc:
            raise HTTPException(status_code=502, detail="Database temporarily unavailable") from exc
    clear_session_cookie(response)
    return {"ok": True}


@app.get("/auth/me")
async def me(user: dict = Depends(require_current_user)):
    return {"user": public_user(user)}


@app.post("/auth/change-password")
async def change_password(
    req: ChangePasswordRequest,
    request: Request,
    user: dict = Depends(require_current_user),
):
    validate_email_and_password(user["email"], req.new_password)
    if not verify_password(user["password_hash"], req.current_password):
        raise HTTPException(status_code=400, detail="当前密码错误")
    token = current_session_token(request)
    token_hash = hash_session_token(token) if token else None
    try:
        update_user_password(user["id"], hash_password(req.new_password))
        revoke_user_sessions(user["id"], except_token_hash=token_hash)
        return {"ok": True}
    except DatabaseError as exc:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from exc


@app.post("/auth/migrate-anonymous")
async def migrate_anonymous(
    req: AnonymousMigrationRequest,
    user: dict = Depends(require_current_user),
):
    marks = {
        paper_id: mark.model_dump(exclude_none=True)
        for paper_id, mark in req.paper_marks.items()
    }
    try:
        return migrate_anonymous_data(user["id"], req.anonymous_user_id, marks)
    except DatabaseError as exc:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from exc


@app.post("/online/heartbeat")
async def heartbeat(req: PresenceRequest, request: Request):
    client_id = req.client_id or req.user_id
    if not client_id:
        raise HTTPException(status_code=400, detail="client_id is required")
    try:
        user = get_current_user_optional(request)
        record_presence(
            client_id,
            user["id"] if user else None,
            request.headers.get("user-agent"),
            get_request_ip(request),
        )
    except DatabaseError as exc:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from exc
    return {"status": "ok"}


@app.get("/online/count")
async def get_online_count():
    try:
        return get_presence_counts(settings.presence.online_timeout_seconds)
    except DatabaseError as exc:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from exc


@app.get("/me/paper-marks")
async def list_my_paper_marks(request: Request, paper_ids: str = ""):
    ids = [paper_id for paper_id in paper_ids.split(",") if paper_id]
    try:
        user = get_current_user_optional(request)
        if not user:
            return {"marks": {}}
        return {"marks": get_paper_marks(user["id"], ids)}
    except DatabaseError as exc:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from exc


@app.get("/me/papers")
async def list_my_papers(
    page: int = 1,
    limit: int = 12,
    filter: str = "all",
    sort: str = "viewed_at",
    user: dict = Depends(require_current_user),
):
    if filter not in {"all", "viewed", "liked"}:
        raise HTTPException(status_code=400, detail="filter must be all, viewed, or liked")
    if sort not in {"viewed_at", "liked_at", "liked_first", "updated_at", "title"}:
        raise HTTPException(status_code=400, detail="unsupported sort")

    safe_page = max(page, 1)
    safe_limit = min(max(limit, 1), 50)
    offset = (safe_page - 1) * safe_limit
    try:
        items, total = list_marked_papers(user["id"], filter, sort, offset, safe_limit)
    except DatabaseError as exc:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from exc

    return {
        "items": items,
        "total": total,
        "page": safe_page,
        "pages": math.ceil(total / safe_limit) if total > 0 else 1,
    }


@app.put("/papers/{paper_id}/mark")
async def update_my_paper_mark(
    paper_id: str,
    req: PaperMarkPayload,
    user: dict = Depends(require_current_user),
):
    try:
        return set_paper_mark(user["id"], paper_id, viewed=req.viewed, liked=req.liked)
    except DatabaseError as exc:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from exc


@app.get("/admin/metrics/online")
async def admin_online_metrics(range: str = "24h", admin: dict = Depends(require_admin_user)):
    if range not in {"24h", "7d"}:
        raise HTTPException(status_code=400, detail="range must be 24h or 7d")
    try:
        return {
            "current": get_presence_counts(settings.presence.online_timeout_seconds),
            "trend": get_presence_trend(range),
        }
    except DatabaseError as exc:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from exc


@app.post("/admin/hf-daily-papers/sync")
async def admin_sync_hf_daily_papers(admin: dict = Depends(require_admin_user)):
    try:
        return await sync_hf_daily_once()
    except DatabaseError as exc:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from exc
    except Exception as exc:
        logger.warning("管理员手动同步 HF Daily Papers 失败: %s", exc)
        raise HTTPException(status_code=502, detail="HF Daily Papers sync failed") from exc


@app.get("/admin/users")
async def admin_list_users(
    search: str = "",
    page: int = 1,
    limit: int = 20,
    admin: dict = Depends(require_admin_user),
):
    safe_page = max(page, 1)
    safe_limit = min(max(limit, 1), 100)
    offset = (safe_page - 1) * safe_limit
    try:
        users, total = list_users(search.strip() or None, offset, safe_limit)
        return {
            "users": users,
            "total": total,
            "page": safe_page,
            "pages": math.ceil(total / safe_limit) if total > 0 else 1,
        }
    except DatabaseError as exc:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from exc


@app.get("/admin/invitation-codes")
async def admin_list_invitation_codes(admin: dict = Depends(require_admin_user)):
    try:
        return {"codes": list_invitation_codes()}
    except DatabaseError as exc:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from exc


@app.post("/admin/invitation-codes")
async def admin_create_invitation_code(
    req: InvitationCodeCreateRequest,
    admin: dict = Depends(require_admin_user),
):
    if req.max_uses < 1 or req.max_uses > 10000:
        raise HTTPException(status_code=400, detail="可使用次数必须在 1 到 10000 之间")
    code = generate_invitation_code()
    try:
        invitation = create_invitation_code(
            hash_session_token(normalize_invitation_code(code)),
            code,
            code[:7],
            req.max_uses,
            admin["id"],
        )
        return {"code": code, "invitation": invitation}
    except DatabaseError as exc:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from exc


@app.patch("/admin/invitation-codes/{code_id}")
async def admin_update_invitation_code(
    code_id: str,
    req: InvitationCodeUpdateRequest,
    admin: dict = Depends(require_admin_user),
):
    if req.max_uses < 1 or req.max_uses > 10000:
        raise HTTPException(status_code=400, detail="可使用次数必须在 1 到 10000 之间")
    try:
        invitation, error = update_invitation_code_max_uses(code_id, req.max_uses)
        if error == "not_found":
            raise HTTPException(status_code=404, detail="邀请码不存在")
        if error == "below_used_count":
            raise HTTPException(status_code=400, detail="可使用次数不能小于已使用次数")
        return invitation
    except DatabaseError as exc:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from exc


@app.delete("/admin/invitation-codes/{code_id}")
async def admin_delete_invitation_code(
    code_id: str,
    admin: dict = Depends(require_admin_user),
):
    try:
        if not delete_invitation_code(code_id):
            raise HTTPException(status_code=404, detail="邀请码不存在")
        return {"ok": True}
    except DatabaseError as exc:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from exc


@app.patch("/admin/users/{user_id}")
async def admin_update_user(
    user_id: str,
    req: AdminUserUpdateRequest,
    admin: dict = Depends(require_admin_user),
):
    if req.role is not None and req.role not in {"user", "admin"}:
        raise HTTPException(status_code=400, detail="role must be user or admin")
    try:
        target = get_user_by_id(user_id)
        if not target:
            raise HTTPException(status_code=404, detail="用户不存在")
        disabling_active_admin = (
            target["role"] == "admin"
            and target["is_active"]
            and (req.is_active is False or req.role == "user")
        )
        if disabling_active_admin and count_active_admins() <= 1:
            raise HTTPException(status_code=400, detail="不能停用最后一个管理员")
        updated = update_user_admin_fields(user_id, role=req.role, is_active=req.is_active)
        if req.is_active is False:
            revoke_user_sessions(user_id)
        return updated
    except DatabaseError as exc:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from exc


@app.post("/admin/users/{user_id}/reset-password")
async def admin_reset_user_password(
    user_id: str,
    req: ResetPasswordRequest,
    admin: dict = Depends(require_admin_user),
):
    validate_email_and_password("admin@example.com", req.password)
    try:
        if not get_user_by_id(user_id):
            raise HTTPException(status_code=404, detail="用户不存在")
        update_user_password(user_id, hash_password(req.password))
        revoke_user_sessions(user_id)
        return {"ok": True}
    except DatabaseError as exc:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from exc


@app.delete("/admin/users/{user_id}")
async def admin_delete_user(
    user_id: str,
    admin: dict = Depends(require_admin_user),
):
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="不能删除当前登录管理员")
    try:
        target = get_user_by_id(user_id)
        if not target:
            raise HTTPException(status_code=404, detail="用户不存在")
        if target["role"] == "admin" and target["is_active"] and count_active_admins() <= 1:
            raise HTTPException(status_code=400, detail="不能删除最后一个管理员")
        if not delete_user(user_id):
            raise HTTPException(status_code=404, detail="用户不存在")
        return {"ok": True}
    except DatabaseError as exc:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from exc


def get_or_fetch_paper_info(paper_id: str) -> dict:
    """Get paper from database, or fetch from OpenReview if not exists."""
    cached = get_paper(paper_id)
    if cached:
        return cached

    # Fetch from OpenReview and save basic info
    paper_info = get_openreview_info(paper_id)
    if not paper_info:
        raise OpenReviewError("Paper not found")

    save_paper(paper_info, llm_response=None)
    return paper_info


@app.get("/paper/{paper_id}/info")
async def get_paper_info(paper_id: str):
    """获取论文基本信息"""
    try:
        paper_info = get_or_fetch_paper_info(paper_id)
    except OpenReviewError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from e

    if not paper_info:
        raise HTTPException(status_code=404, detail="Paper not found")

    return paper_info


@app.get("/paper/{paper_id}")
async def get_paper_analysis(paper_id: str, reanalyze: bool = False):
    async def generate():
        if not llm.is_configured():
            yield {"event": "error", "data": "config.yaml 未配置有效 LLM API key"}
            return

        # Ensure paper exists in database
        yield {"event": "status", "data": "正在获取论文信息..."}
        try:
            paper_info = await asyncio.to_thread(get_or_fetch_paper_info, paper_id)
        except OpenReviewError as e:
            yield {"event": "error", "data": str(e)}
            return
        except DatabaseError:
            yield {"event": "error", "data": "数据库暂时不可用，请稍后重试"}
            return

        # Check if we can return cached analysis
        if not reanalyze and paper_info.get("llm_response"):
            normalized_response = normalize_llm_markdown(paper_info["llm_response"], analysis_mode=True)
            if normalized_response != paper_info["llm_response"]:
                await asyncio.to_thread(update_llm_response, paper_id, normalized_response)
            yield {"data": normalized_response}
            yield {"event": "done", "data": ""}
            return

        # Perform AI analysis
        yield {"event": "status", "data": "正在读取 PDF 内容..."}
        try:
            paper_content = await asyncio.to_thread(
                get_or_cache_paper_content,
                paper_id,
                paper_info["pdf"],
            )
            paper_content = truncate_content_for_llm(paper_content)
        except ReaderError as e:
            yield {"event": "error", "data": str(e)}
            return

        yield {"event": "status", "data": "正在分析论文..."}

        user_prompt = f"以下是论文内容：\n{paper_content}"

        full_response = []
        async for chunk in llm.get_response_stream(user_prompt):
            full_response.append(chunk)
            yield {"data": chunk}

        normalized_response = normalize_llm_markdown("".join(full_response), analysis_mode=True)
        await asyncio.to_thread(update_llm_response, paper_id, normalized_response)
        yield {"event": "done", "data": ""}

    return EventSourceResponse(generate())


@app.post("/paper/{paper_id}/chat")
async def chat_with_paper(
    paper_id: str,
    req: ChatRequest,
    user: dict = Depends(require_current_user),
):
    ensure_llm_configured()
    session_row = assert_chat_owner(req.session_id, user["id"])
    session = chat_sessions.get(req.session_id)
    is_new_session = session_row is None

    if not session:
        try:
            paper_info = await asyncio.to_thread(get_or_fetch_paper_info, paper_id)
        except OpenReviewError as e:
            raise HTTPException(status_code=502, detail=str(e))
        except DatabaseError as e:
            raise HTTPException(status_code=502, detail="Database temporarily unavailable") from e

        context_parts = []
        if paper_info.get("pdf"):
            paper_content = await asyncio.to_thread(
                get_or_cache_paper_content,
                paper_id,
                paper_info["pdf"],
            )
            paper_content = truncate_content_for_llm(paper_content)
            context_parts.append(f"论文全文：\n{paper_content}")
        if paper_info.get("llm_response"):
            context_parts.append(f"论文分析：\n{paper_info['llm_response']}")

        history_rows = get_chat_messages(req.session_id) if session_row else []
        if history_rows:
            history = [{"role": r["role"], "content": r["content"]} for r in history_rows]
        else:
            history = None

        session = ChatSession(llm, context="\n\n".join(context_parts), history=history)
        chat_sessions[req.session_id] = session

    async def generate():
        try:
            if is_new_session:
                create_chat_session(
                    req.session_id,
                    user["id"],
                    paper_id,
                    req.message[:50],
                    account_user_id=user["id"],
                )

            chunks = []
            async for chunk in session.send_stream(req.message):
                chunks.append(chunk)
                yield {"data": chunk}

            # Persist messages
            save_chat_message(req.session_id, "user", req.message)
            save_chat_message(req.session_id, "assistant", normalize_llm_markdown("".join(chunks)))

            yield {"event": "done", "data": ""}
        except DatabaseError:
            yield {"event": "error", "data": "数据库暂时不可用，请稍后重试"}

    return EventSourceResponse(generate())


@app.get("/paper/{paper_id}/chat/sessions")
async def list_chat_sessions(paper_id: str, request: Request):
    try:
        user = get_current_user_optional(request)
        if not user:
            return []
        return get_chat_sessions_for_account(user["id"], paper_id)
    except DatabaseError as e:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from e


@app.get("/chat/{session_id}/messages")
async def list_chat_messages(session_id: str, user: dict = Depends(require_current_user)):
    try:
        assert_chat_owner(session_id, user["id"])
        return get_chat_messages(session_id)
    except DatabaseError as e:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from e


@app.delete("/chat/{session_id}")
async def delete_session(session_id: str, user: dict = Depends(require_current_user)):
    chat_sessions.pop(session_id, None)
    try:
        assert_chat_owner(session_id, user["id"])
        delete_chat_session(session_id)
    except DatabaseError as e:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from e
    return {"ok": True}


@app.post("/paper/{paper_id}/chat/regenerate")
async def regenerate_chat(
    paper_id: str,
    req: ChatRequest,
    user: dict = Depends(require_current_user),
):
    """Delete last message pair, then re-send the user message."""
    ensure_llm_configured()
    session_row = assert_chat_owner(req.session_id, user["id"])
    if not session_row:
        raise HTTPException(status_code=404, detail="会话不存在")

    session = chat_sessions.get(req.session_id)
    if session and len(session.history) >= 2:
        session.history = session.history[:-2]
    else:
        chat_sessions.pop(req.session_id, None)
        session = None

    try:
        delete_last_chat_message_pair(req.session_id)
    except DatabaseError as e:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from e

    if not session:
        try:
            paper_info = await asyncio.to_thread(get_or_fetch_paper_info, paper_id)
        except OpenReviewError as e:
            raise HTTPException(status_code=502, detail=str(e))
        except DatabaseError as e:
            raise HTTPException(status_code=502, detail="Database temporarily unavailable") from e

        context_parts = []
        if paper_info.get("pdf"):
            paper_content = await asyncio.to_thread(
                get_or_cache_paper_content,
                paper_id,
                paper_info["pdf"],
            )
            paper_content = truncate_content_for_llm(paper_content)
            context_parts.append(f"论文全文：\n{paper_content}")
        if paper_info.get("llm_response"):
            context_parts.append(f"论文分析：\n{paper_info['llm_response']}")
        history_rows = get_chat_messages(req.session_id)
        history = [{"role": r["role"], "content": r["content"]} for r in history_rows] if history_rows else None
        session = ChatSession(llm, context="\n\n".join(context_parts), history=history)
        chat_sessions[req.session_id] = session

    async def generate():
        try:
            chunks = []
            async for chunk in session.send_stream(req.message):
                chunks.append(chunk)
                yield {"data": chunk}

            save_chat_message(req.session_id, "user", req.message)
            save_chat_message(req.session_id, "assistant", "".join(chunks))

            yield {"event": "done", "data": ""}
        except DatabaseError:
            yield {"event": "error", "data": "数据库暂时不可用，请稍后重试"}

    return EventSourceResponse(generate())


@app.get("/conference/{venue}/papers")
async def get_conference_papers_endpoint(
    venue: str,
    page: int = 1,
    limit: int = 8,
    search: str = "",
    search_title: bool = True,
    search_abstract: bool = True,
    search_keywords: bool = True
):
    venue_map = {"neurips_2025": "NeurIPS 2025", "iclr_2026": "ICLR 2026", "icml_2025": "ICML 2025"}
    venue_name = venue_map.get(venue)
    if not venue_name:
        raise HTTPException(status_code=404, detail="Conference not found")

    offset = (page - 1) * limit
    try:
        papers, total = get_conference_papers(
            venue_name, offset, limit,
            search if search else None,
            search_title, search_abstract, search_keywords
        )
    except DatabaseError as e:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from e

    return {
        "papers": papers,
        "total": total,
        "page": page,
        "pages": math.ceil(total / limit) if total > 0 else 1
    }


@app.get("/hf-daily-papers")
async def get_hf_daily_papers_endpoint(
    page: int = 1,
    limit: int = 8,
    search: str = "",
    search_title: bool = True,
    search_abstract: bool = True,
    search_keywords: bool = True
):
    safe_page = max(page, 1)
    safe_limit = min(max(limit, 1), 100)
    offset = (safe_page - 1) * safe_limit
    try:
        papers, total = get_hf_daily_papers(
            offset,
            safe_limit,
            search if search else None,
            search_title,
            search_abstract,
            search_keywords,
        )
    except DatabaseError as e:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from e

    return {
        "papers": papers,
        "total": total,
        "page": safe_page,
        "pages": math.ceil(total / safe_limit) if total > 0 else 1
    }


@app.get("/search/papers")
async def search_all_papers_endpoint(
    page: int = 1,
    limit: int = 8,
    search: str = "",
    search_title: bool = True,
    search_abstract: bool = True,
    search_keywords: bool = True
):
    offset = (page - 1) * limit
    try:
        papers, total = search_all_papers(
            offset, limit,
            search if search else None,
            search_title, search_abstract, search_keywords
        )
    except DatabaseError as e:
        raise HTTPException(status_code=502, detail="Database temporarily unavailable") from e

    return {
        "papers": papers,
        "total": total,
        "page": page,
        "pages": math.ceil(total / limit) if total > 0 else 1
    }


# 静态文件服务
REACT_FRONTEND_DIST_DIR = Path(__file__).parent.parent / "frontend-react" / "dist"
IMAGES_DIR = Path(__file__).parent.parent / "images"


def get_frontend_index() -> Path:
    react_index = REACT_FRONTEND_DIST_DIR / "index.html"
    if react_index.exists():
        return react_index
    raise HTTPException(
        status_code=503,
        detail="Frontend build not found. Run `cd frontend-react && npm run build` first.",
    )


app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")
app.mount("/assets", StaticFiles(directory=REACT_FRONTEND_DIST_DIR / "assets", check_dir=False), name="assets")


@app.get("/")
async def serve_frontend():
    return FileResponse(get_frontend_index())


@app.get("/search")
async def serve_search_frontend():
    return FileResponse(get_frontend_index())


@app.get("/login")
async def serve_login_frontend():
    return FileResponse(get_frontend_index())


@app.get("/register")
async def serve_register_frontend():
    return FileResponse(get_frontend_index())


@app.get("/admin")
async def serve_admin_frontend():
    return FileResponse(get_frontend_index())


@app.get("/me")
async def serve_me_frontend():
    return FileResponse(get_frontend_index())


@app.get("/hf-daily")
async def serve_hf_daily_frontend():
    return FileResponse(get_frontend_index())


@app.get("/conference/{venue}")
async def serve_conference_frontend(venue: str):
    return FileResponse(get_frontend_index())


@app.get("/papers/{paper_id}")
async def serve_paper_frontend(paper_id: str):
    return FileResponse(get_frontend_index())
