import logging
import sys

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
logger.info("Settings loaded successfully")
from app.routers import feed, outfit, onboarding, reaction, item, tone, top_pick, compare, saved, auth, feedback

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI 퍼스널컬러 기반 패션 의사결정 API",
)

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(feed.router)
app.include_router(outfit.router)
app.include_router(onboarding.router)
app.include_router(reaction.router)
app.include_router(item.router)
app.include_router(tone.router)
app.include_router(top_pick.router)
app.include_router(compare.router)
app.include_router(saved.router)
app.include_router(auth.router)
app.include_router(feedback.router)


logger.info("All routers registered, app ready")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.app_version}
