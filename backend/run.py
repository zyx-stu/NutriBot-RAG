"""
run.py — Entry-point to start the NutriBot FastAPI backend with uvicorn.

Usage (from project root, with .venv active):
  python backend/run.py

Or directly:
  uvicorn backend.src.main:app --host 0.0.0.0 --port 8000 --reload
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.src.main:app",   # updated: backend/src/ (was backend/app/)
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
