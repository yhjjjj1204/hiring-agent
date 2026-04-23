import logging
import json
import time
import pymongo
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, APIRouter, WebSocket, WebSocketDisconnect, Query, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from version import __version__
from agents.background_analysis.repository import ensure_background_analysis_indexes
from dashboard.repository import ensure_candidate_ranking_indexes
from agents.data_arrangement.repository import ensure_resume_ingest_indexes
from agents.hr_strategy.repository import ensure_hr_strategy_indexes
from api.auth_repository import ensure_auth_indexes
from db.mongo import get_database, create_vector_index
from graph.workflow import build_graph

# Role-based routers
from api.routes_auth import router as auth_router
from api.routes_candidate import router as candidate_router
from api.routes_recruiter import router as recruiter_router
from api.routes_chat import run_chat_logic
from api.websockets import manager
from api.auth_repository import get_user as get_user_from_db
from api.auth_models import User

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(name)s - %(message)s")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Retry logic for DB connection/indexing during startup
    max_retries = 10
    retry_interval = 3
    db = get_database()
    
    for i in range(max_retries):
        try:
            logging.info(f"Ensuring database indexes (attempt {i+1}/{max_retries})...")
            ensure_auth_indexes()
            ensure_hr_strategy_indexes()
            ensure_resume_ingest_indexes()
            ensure_background_analysis_indexes()
            ensure_candidate_ranking_indexes()
            db.jobs.create_index("id", unique=True)
            
            # Ensure vector indexes for FerretDB
            try:
                logging.info("Ensuring vector indexes for jobs...")
                create_vector_index("jobs", "desc_embedding", 1536, "job_desc_vector_idx")
                create_vector_index("jobs", "summary_embedding", 1536, "job_summary_vector_idx")
            except Exception as ve:
                logging.warning(f"Could not create vector indexes (might already exist or FerretDB not supporting it yet): {ve}")

            logging.info("Database indexes ensured successfully.")
            break
        except (pymongo.errors.ServerSelectionTimeoutError, pymongo.errors.AutoReconnect) as e:
            if i == max_retries - 1:
                logging.error("Failed to connect to MongoDB after multiple retries.")
                raise
            logging.warning(f"MongoDB not ready, retrying in {retry_interval}s... ({e})")
            time.sleep(retry_interval)
    yield


app = FastAPI(title="Hiring Agent API", version=__version__, lifespan=lifespan)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(None)):
    if not token:
        await websocket.close(code=1008) # Policy Violation
        return

    user_db = get_user_from_db(token)
    if not user_db:
        await websocket.close(code=1008)
        return

    user = User(username=user_db.username, role=user_db.role)
    await manager.connect(websocket, user.username)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle subscriptions
            if message.get("type") == "subscribe" and message.get("job_id"):
                job_id = message["job_id"]
                if user.role == "recruiter":
                    await manager.subscribe(websocket, f"job:{job_id}")
                    await websocket.send_text(json.dumps({"type": "subscribed", "job_id": job_id}))
                else:
                    await websocket.send_text(json.dumps({"type": "error", "message": "Only recruiters can subscribe to jobs"}))
            
            # Handle chat messages
            elif message.get("type") == "chat_message":
                msg_text = message.get("message")
                ctx = message.get("context")
                ctx_labels = message.get("context_labels")
                
                async def send_ws_chat_update(data: dict):
                    await websocket.send_text(json.dumps({
                        "type": "chat_update",
                        **data
                    }))

                bt = BackgroundTasks()
                await run_chat_logic(
                    msg_text,
                    ctx,
                    ctx_labels,
                    user,
                    bt,
                    send_ws_chat_update
                )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user.username)
    except Exception as e:
        logging.error(f"WebSocket error for {user.username}: {e}")
        manager.disconnect(websocket, user.username)

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
    # Skip if it looks like an API call (already handled by router if valid)
    if full_path.startswith("api/"):
        return HTMLResponse(f"API Route Not Found: {full_path}", status_code=404)
        
    # If the path looks like a file (has an extension), don't serve index.html
    if "." in full_path.split("/")[-1]:
        return HTMLResponse(f"File Not Found: {full_path}", status_code=404)
        
    return HTMLResponse(_read_index())
