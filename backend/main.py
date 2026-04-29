import json
import os
import sys
from pathlib import Path

# allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.models import (
    SimulateTextRequest,
    SimulateJsonRequest,
    WhatIfRequest,
    SimulationResponse,
)
from backend.pipeline import run_from_text, run_from_scene, run_whatif

app = FastAPI(title="Physics Reasoning Engine", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SCENES_DIR = Path(__file__).resolve().parent.parent / "scenes"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/simulate", response_model=SimulationResponse)
def simulate_from_text(body: SimulateTextRequest):
    """Natural language → scene JSON → simulation → explanation."""
    try:
        scene, result, explanation = run_from_text(body.description)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return SimulationResponse(scene=scene, result=result, explanation=explanation)


@app.post("/simulate/json", response_model=SimulationResponse)
def simulate_from_json(body: SimulateJsonRequest):
    """Scene JSON directly → simulation → explanation."""
    try:
        scene, result, explanation = run_from_scene(body.scene)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return SimulationResponse(scene=scene, result=result, explanation=explanation)


@app.post("/whatif", response_model=SimulationResponse)
def whatif(body: WhatIfRequest):
    """Apply parameter changes to a scene, re-simulate, re-explain."""
    try:
        scene, result, explanation = run_whatif(body.scene, body.changes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return SimulationResponse(scene=scene, result=result, explanation=explanation)


@app.get("/scenes")
def list_scenes():
    """List available saved scene files."""
    if not SCENES_DIR.exists():
        return {"scenes": []}
    files = sorted(p.stem for p in SCENES_DIR.glob("*.json"))
    return {"scenes": files}


@app.get("/scenes/{scene_id}")
def get_scene(scene_id: str):
    """Return a saved scene JSON by filename stem."""
    path = SCENES_DIR / f"{scene_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Scene '{scene_id}' not found")
    with open(path) as f:
        return json.load(f)


# ── Dev entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
