import sys
from pathlib import Path

print("Diagnostic script starting...")

repo_root = Path(__file__).resolve().parents[1]
src_dir = repo_root / "src"

print(f"Repo root: {repo_root}")
print(f"Src dir: {src_dir}")

sys.path.append(str(repo_root))
sys.path.append(str(src_dir))

print("Attempting to import modules...")

try:
    import horse_algos
    print("Imported horse_algos")
except Exception as e:
    print(f"Failed to import horse_algos: {e}")

try:
    from horse_algos.tools.map_loader import load_graph_from_map
    print("Imported load_graph_from_map")
except Exception as e:
    print(f"Failed to import load_graph_from_map: {e}")

try:
    from horse_algos.algorithms.cpp_algorithms import CPP_AVAILABLE
    print(f"Imported cpp_algorithms, CPP_AVAILABLE: {CPP_AVAILABLE}")
except Exception as e:
    print(f"Failed to import cpp_algorithms: {e}")

try:
    from data.generate import TEST_SIZES
    print(f"Imported data.generate, TEST_SIZES: {TEST_SIZES}")
except Exception as e:
    print(f"Failed to import data.generate: {e}")

print("Diagnostic script finished.")
