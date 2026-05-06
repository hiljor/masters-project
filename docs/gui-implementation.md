# Plan: Web-based GUI for Algorithm Selection and Execution

This plan outlines the creation of a modern, web-based GUI to interact with the horse algorithm project. It will allow users to select an algorithm, a data file, and a 'k' value to find the optimal solution.

## Architecture
- **Backend:** FastAPI (Python)
- **Frontend:** React + Tailwind CSS (served as a single-page application)
- **Location:** All GUI-related files will be located in the `/web` directory at the project root.
- **Documentation:** The finalized plan will be stored in `/docs/gui-implementation.md`.

## Components

### 1. Backend (`web/server.py`)
- **Dynamic Discovery:**
  - Algorithms: Scans `horse_algos.algorithms` for subclasses of `Algorithm`.
  - Maps: Scans the `data/` directory for `.txt` files.
- **Endpoints:**
  - `GET /api/config`: Returns lists of available algorithms and map files.
  - `POST /api/solve`: Executes the selected algorithm and returns the result.
- **Static Serving:** Serves the frontend HTML from `web/index.html`.

### 2. Frontend (`web/index.html`)
- **UI Design:**
  - Modern, centered card layout.
  - Dropdowns for algorithm and map selection.
  - Input field for 'k'.
  - Large "Solve" button with loading state.
  - Results display area with success/error indicators.
- **Tech Stack:**
  - React (via CDN) for reactive UI.
  - Tailwind CSS (via CDN) for styling.

## Implementation Steps

### Phase 0: Documentation
1. Create the `docs/` directory.
2. Save this plan to `docs/gui-implementation.md`.

### Phase 1: Backend Setup
1. Create the `web/` directory.
2. Create `web/server.py`.
3. Implement `discover_algorithms()` using `pkgutil` to find available `Algorithm` implementations in the `horse_algos` package.
4. Implement `discover_maps()` to list files in the `data/` folder.
5. Set up FastAPI app to serve `index.html` at the root.

### Phase 2: Frontend Setup
1. Create `web/index.html` with a modern design using Tailwind.
2. Implement the React component to fetch config and handle form submission.

### Phase 3: Verification
1. Verify the backend starts correctly: `python web/server.py`.
2. Manually test the API endpoints.
3. Verify the frontend renders and communicates with the backend.

## Requirements
- `fastapi`
- `uvicorn`

## Usage
Users will run the GUI using:
```bash
python web/server.py
```
Then open `http://localhost:8000` in their browser.
