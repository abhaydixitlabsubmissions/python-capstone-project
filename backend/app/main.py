from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from app.core.config import settings
from app.db.session import init_db, AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.api.auth import router as auth_router
from app.api.books import router as books_router
from app.api.chat import router as chat_router
from app.api.summaries import router as summaries_router
from app.api.notes import router as notes_router
from app.api.search import router as search_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database extensions & tables
    try:
        await init_db()
        # Seed a demo user if none exists
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.email == "demo@bookmind.ai")
            existing = (await session.execute(stmt)).scalar_one_or_none()
            if not existing:
                demo_user = User(
                    email="demo@bookmind.ai",
                    name="BookMind Demo User",
                    password_hash=get_password_hash("demo123456"),
                    is_active=True,
                )
                session.add(demo_user)
                await session.commit()
    except Exception as e:
        print(f"[Warning] Database initialization notice: {e}")
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-user AI Book & Knowledge Platform API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers under /api
app.include_router(auth_router, prefix="/api")
app.include_router(books_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(summaries_router, prefix="/api")
app.include_router(notes_router, prefix="/api")
app.include_router(search_router, prefix="/api")

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }
