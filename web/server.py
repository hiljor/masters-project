import os
import sys
import uvicorn
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from pathlib import Path
import importlib
import inspect
from typing import List, Dict, Any

# Add src to path so we can import horse_algos from the workspace first
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "src"))

from horse_algos.algorithms.algorithm import Algorithm
from horse_algos.tools.map_loader import load_map_with_metadata

app = FastAPI()

# Data and Web paths
DATA_DIR = repo_root / "data"
WEB_DIR = repo_root / "web"

class SolveRequest(BaseModel):
    algorithm: str
    map_file: str
    k: int
    language: str = "python"
    task_id: str = None

def discover_algorithms() -> Dict[str, Dict[str, Any]]:
    """Discover available algorithms for both Python and C++."""
    algorithms = {"python": {}, "cpp": {}}
    
    # 1. Manually add Python algorithms to ensure they are always present
    from horse_algos.algorithms.naive import Naive
    from horse_algos.algorithms.important_separator import ImportantSeparators
    from horse_algos.algorithms.milp_ortools import MILP_OR
    
    py_algos = [Naive(), ImportantSeparators(), MILP_OR()]
    for algo in py_algos:
        algorithms["python"][algo.name] = algo
    
    # 2. Discover C++ algorithms if the extension is built
    try:
        from horse_algos.algorithms.cpp_algorithms import (
            CppNaive, 
            CppImportantSeparators, 
            CPP_AVAILABLE
        )
        if CPP_AVAILABLE:
            algorithms["cpp"]["Brute Force (C++)"] = CppNaive()
            algorithms["cpp"]["Important Separators (C++)"] = CppImportantSeparators()
    except ImportError as e:
        print(f"C++ algorithms not available: {e}")
        
    return algorithms

def discover_maps() -> List[str]:
    return [f for f in os.listdir(DATA_DIR) if f.endswith(".txt")]

@app.get("/api/config")
async def get_config():
    algos = discover_algorithms()
    maps = discover_maps()
    # Return available algorithms for each language
    available_algos = {lang: list(instances.keys()) for lang, instances in algos.items()}
    return {
        "algorithms": available_algos,
        "maps": maps,
        "languages": list(available_algos.keys())
    }

@app.get("/api/map/{filename}")
async def get_map(filename: str):
    map_path = DATA_DIR / filename
    if not map_path.exists():
        raise HTTPException(status_code=404, detail="Map not found")
    
    lines = map_path.read_text(encoding="utf-8").splitlines()
    return {"lines": lines}

@app.post("/api/solve")
async def solve(request: SolveRequest):
    algos = discover_algorithms()
    lang = request.language.lower()
    task_id = request.task_id
    
    if lang not in algos:
        raise HTTPException(status_code=400, detail=f"Language '{lang}' not supported")
    
    if request.algorithm not in algos[lang]:
        raise HTTPException(status_code=400, detail=f"Algorithm '{request.algorithm}' not found for {lang}")
    
    map_path = DATA_DIR / request.map_file
    if not map_path.exists():
        raise HTTPException(status_code=400, detail="Map file not found")
    
    try:
        # We need the graph and the ID-to-coords mapping
        graph, s, t, coords_to_id = load_map_with_metadata(str(map_path))
        id_to_coords = {v: k for k, v in coords_to_id.items()}
        
        algo = algos[lang][request.algorithm]
        
        # Track time
        start_time = time.time()
        result_value, cutset_ids = algo.run(graph, s, t, request.k)
        elapsed = time.time() - start_time
        
        # Map cutset node IDs back to coordinates
        cutset_coords = [id_to_coords[node_id] for node_id in cutset_ids if node_id in id_to_coords]
        
        return {
            "result": str(result_value),
            "time_ms": round(elapsed * 1000, 2),
            "cutset": cutset_coords
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        return "Frontend not implemented yet."
    return index_path.read_text(encoding="utf-8")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
