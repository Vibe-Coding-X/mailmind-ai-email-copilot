from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.emails import router as emails_router
from app.api.gmail_auth import router as gmail_auth_router
from app.api.mailboxes import router as mailboxes_router
from app.core.config import get_settings


app = FastAPI(title="MailMind Backend")

# Local-dev CORS for the Next.js frontend (T010a). Credentialed requests
# (Cookie session) require explicit origins, so origins are listed rather than
# wildcarded. Origins are configurable via the CORS_ALLOWED_ORIGINS env var.
_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(gmail_auth_router)
app.include_router(mailboxes_router)
app.include_router(emails_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        return JSONResponse(status_code=exc.status_code, content={"error": detail})
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "INVALID_REQUEST",
                "message": str(detail),
                "retryable": False,
                "details": {},
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "INVALID_REQUEST",
                "message": "Invalid request.",
                "retryable": False,
                "details": {"errors": exc.errors()},
            }
        },
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "mailmind-backend"}
