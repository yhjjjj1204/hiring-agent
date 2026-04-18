from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from version import __version__
from agents.background_analysis.repository import ensure_background_analysis_indexes
from dashboard.repository import ensure_candidate_ranking_indexes
from agents.data_arrangement.repository import ensure_resume_ingest_indexes
from agents.hr_strategy.repository import ensure_hr_strategy_indexes
from api.routes_background import router as background_router
from api.routes_dashboard import router as dashboard_router
from api.routes_monitor import router as monitor_router
from api.routes_pipeline import router as pipeline_router
from api.routes_analyze import router as analyze_router
from api.routes_data import router as data_router
from api.routes_hr_strategy import router as hr_strategy_router
from graph.workflow import build_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_hr_strategy_indexes()
    ensure_resume_ingest_indexes()
    ensure_background_analysis_indexes()
    ensure_candidate_ranking_indexes()
    yield


app = FastAPI(title="Hiring Agent API", version=__version__, lifespan=lifespan)
app.include_router(hr_strategy_router)
app.include_router(analyze_router)
app.include_router(data_router)
app.include_router(background_router)
app.include_router(pipeline_router)
app.include_router(monitor_router)
app.include_router(dashboard_router)
_graph = build_graph()

_FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
_UI_INDEX = _FRONTEND_DIR / "index.html"


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def serve_resume_analyze_ui():
    """Single-page UI: upload resume and job description, call /analyze/resume."""
    if not _UI_INDEX.is_file():
        return HTMLResponse("<p>frontend/index.html not found</p>", status_code=404)
    return HTMLResponse(_UI_INDEX.read_text(encoding="utf-8"))


# Mount the entire frontend directory for development (scripts, components, styles)
if _FRONTEND_DIR.is_dir():
    app.mount("/src", StaticFiles(directory=str(_FRONTEND_DIR / "src")), name="frontend-src")
    app.mount("/assets", StaticFiles(directory=str(_FRONTEND_DIR / "src" / "assets"), check_dir=False), name="frontend-assets")


@app.get("/health")
def health():
    return {"status": "ok", "version": __version__}


@app.post("/graph/invoke")
def invoke_graph(payload: dict):
    """Placeholder: invoke compiled LangGraph over HTTP (replace with typed I/O later)."""
    result = _graph.invoke(payload)
    return {"result": result}
