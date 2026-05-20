from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api import auth, reviews, github

settings = get_settings()

app = FastAPI(
    title="CodeSentinel API",
    description="Autonomous GitHub PR code review agent powered by Claude AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(reviews.router)
app.include_router(github.router)


@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    return {"status": "ok", "mock_mode": settings.AI_MOCK}


@app.get("/")
async def root():
    return {"message": "CodeSentinel API", "docs": "/docs"}
