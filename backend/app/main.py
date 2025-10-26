from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.home import router as home_router
from app.routers.profile import router as profile_router
from app.routers.search import router as search_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# 掛載各 router
app.include_router(home_router, prefix="/home", tags=["home"])
app.include_router(profile_router, prefix="/profile", tags=["profile"])
app.include_router(search_router, prefix="/search", tags=["search"])