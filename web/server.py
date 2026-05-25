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

# Add src to path so we can import horse_algos
repo_root = Path(__file__).resolve().parents[1]
sys.path.append(str(repo_root / "src"))

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
# ... (rest of discover_algorithms remains the same)
    algorithms = {"python": {}, "cpp": {}}
    
    # Discover Python algorithms
    algo_dir = repo_root / "src" / "horse_algos" / "algorithms"
    for file in os.listdir(algo_dir):
        if file.endswith(".py") and file not in ["__init__.py", "algorithm.py", "cpp_algorithms.py"]:
            module_name = f"horse_algos.algorithms.{file[:-3]}"
            try:
                module = importlib.import_module(module_name)
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, Algorithm) and obj != Algorithm:
                        instance = obj()
                        algorithms["python"][instance.name] = instance
            except Exception:
                continue
    
    # Discover C++ algorithms if available
    try:
        from horse_algos.algorithms.cpp_algorithms import (
            CppNaive, 
            CppImportantSeparators, 
            CppMILP, 
            CPP_AVAILABLE
        )
        if CPP_AVAILABLE:
            algorithms["cpp"]["Brute Force"] = CppNaive()
            algorithms["cpp"]["Important Separators"] = CppImportantSeparators()
            algorithms["cpp"]["MILP (OR-Tools)"] = CppMILP()
    except ImportError:
        pass
        
    return algorithms

def discover_maps() -> List[str]:
    return [f for f in os.listdir(DATA_DIR) if f.endswith(".txt")]

@app.get("/api/config")
async def get_config():
    algos = discover_algorithms()
    maps = discover_maps()
    return {
        "algorithms": list(algos["python"].keys()), # Names are the same for both
        "maps": maps,
        "languages": ["python", "cpp"] if algos["cpp"] else ["python"]
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
