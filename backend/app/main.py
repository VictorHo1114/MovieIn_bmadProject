from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

app = FastAPI(title="BMAD_PROJECT API", version="0.1.0")

# Allow frontend requests
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok"}

class SearchIntent(BaseModel):
    keyword: str
    year: int | None = None

@app.post("/api/search")
def search_movies(intent: SearchIntent):
    return {"echo": intent.model_dump(), "results": []}
