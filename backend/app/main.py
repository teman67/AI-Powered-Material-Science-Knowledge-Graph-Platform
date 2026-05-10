from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import get_settings
from app.core.rate_limit import SimpleRateLimitMiddleware
from app.core.request_tracing import RequestTracingMiddleware, configure_application_logging
from app.db.session import init_db

settings = get_settings()
configure_application_logging(settings.log_level)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SimpleRateLimitMiddleware,
    requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
    enabled=settings.rate_limit_enabled,
)

app.add_middleware(
    RequestTracingMiddleware,
    header_name=settings.request_id_header_name,
    enabled=settings.request_tracing_enabled,
)


@app.on_event("startup")
def startup_event() -> None:
    init_db()


app.include_router(api_router)
