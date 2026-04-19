import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from version import __version__
from agents.background_analysis.repository import ensure_background_analysis_indexes
from dashboard.repository import ensure_candidate_ranking_indexes
from agents.data_arrangement.repository import ensure_resume_ingest_indexes
from agents.hr_strategy.repository import ensure_hr_strategy_indexes
from api.auth_repository import ensure_auth_indexes
from db.mongo import get_database
from graph.workflow import build_graph

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(name)s - %(message)s")

# Role-based routers
from api.routes_auth import router as auth_router
from api.routes_candidate import router as candidate_router
from api.routes_recruiter import router as recruiter_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_auth_indexes()
    ensure_hr_strategy_indexes()
    ensure_resume_ingest_indexes()
    ensure_background_analysis_indexes()
    ensure_candidate_ranking_indexes()
    db = get_database()
    db.jobs.create_index("id", unique=True)
    yield


app = FastAPI(title="Hiring Agent API", version=__version__, lifespan=lifespan)

# Main API router
api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(candidate_router)
api_router.include_router(recruiter_router)

app.include_router(api_router)

_graph = build_graph()

_FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
_DIST_DIR = _FRONTEND_DIR / "dist"

if _DIST_DIR.is_dir():
    _UI_INDEX = _DIST_DIR / "index.html"
else:
    _UI_INDEX = _FRONTEND_DIR / "index.html"


def _read_index():
    if not _UI_INDEX.is_file():
        return f"<p>Frontend index not found at {_UI_INDEX}</p>"
    return _UI_INDEX.read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def serve_resume_analyze_ui():
    return HTMLResponse(_read_index())


# Mount static files
if _DIST_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(_DIST_DIR / "assets")), name="assets")
elif _FRONTEND_DIR.is_dir():
    app.mount("/src", StaticFiles(directory=str(_FRONTEND_DIR / "src")), name="frontend-src")
    assets_path = _FRONTEND_DIR / "src" / "assets"
    if assets_path.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_path)), name="frontend-assets")


@app.get("/health")
def health():
    return {"status": "ok", "version": __version__}


@app.post("/api/graph/invoke")
def invoke_graph(payload: dict):
    """Placeholder: invoke compiled LangGraph over HTTP."""
    result = _graph.invoke(payload)
    return {"result": result}


# Catch-all route to serve index.html for frontend routing
@app.get("/{full_path:path}", include_in_schema=False)
def catch_all(request: Request, full_path: str):
    if "." in full_path.split("/")[-1]:
        return HTMLResponse(f"Not Found: {full_path}", status_code=404)
    return HTMLResponse(_read_index())
