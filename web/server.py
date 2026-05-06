import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import importlib
import inspect
from typing import List, Dict

# Add src to path so we can import horse_algos
repo_root = Path(__file__).resolve().parents[1]
sys.path.append(str(repo_root / "src"))

from horse_algos.algorithms.algorithm import Algorithm
from horse_algos.tools.map_loader import load_graph_from_map

app = FastAPI()

# Data and Web paths
DATA_DIR = repo_root / "data"
WEB_DIR = repo_root / "web"

class SolveRequest(BaseModel):
    algorithm: str
    map_file: str
    k: int

def discover_algorithms() -> Dict[str, Algorithm]:
    algorithms = {}
    algo_dir = repo_root / "src" / "horse_algos" / "algorithms"
    for file in os.listdir(algo_dir):
        if file.endswith(".py") and file != "__init__.py" and file != "algorithm.py":
            module_name = f"horse_algos.algorithms.{file[:-3]}"
            module = importlib.import_module(module_name)
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, Algorithm) and obj != Algorithm:
                    instance = obj()
                    algorithms[instance.name] = instance
    return algorithms

def discover_maps() -> List[str]:
    return [f for f in os.listdir(DATA_DIR) if f.endswith(".txt")]

@app.get("/api/config")
async def get_config():
    algos = discover_algorithms()
    maps = discover_maps()
    return {
        "algorithms": list(algos.keys()),
        "maps": maps
    }

@app.post("/api/solve")
async def solve(request: SolveRequest):
    algos = discover_algorithms()
    if request.algorithm not in algos:
        raise HTTPException(status_code=400, detail="Algorithm not found")
    
    map_path = DATA_DIR / request.map_file
    if not map_path.exists():
        raise HTTPException(status_code=400, detail="Map file not found")
    
    try:
        graph, s, t = load_graph_from_map(str(map_path))
        algo = algos[request.algorithm]
        result = algo.run(graph, s, t, request.k)
        return {"result": str(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        return "Frontend not implemented yet."
    return index_path.read_text(encoding="utf-8")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
