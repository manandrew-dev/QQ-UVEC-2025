
from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from test_backend import SingleFileModularityAnalyzer
import tempfile
import os

app = FastAPI(title="Code Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/analyze")
async def analyze(code: str = Form(...)):
    """
    Accepts a Python source code string, runs modularity analysis,
    and returns both summary metrics and detailed refactor suggestions.
    """
    code_str = (code or "").strip()
    if not code_str:
        raise HTTPException(status_code=400, detail="Empty code submitted.")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".py", mode="w", encoding="utf-8"
        ) as tmp:
            tmp.write(code_str)
            tmp_path = tmp.name

        analyzer = SingleFileModularityAnalyzer(tmp_path)
        suggestions = analyzer.analyze_file()

        complexity = getattr(analyzer, "complexity_scores", {}) or {}
        summary = {
            "total_functions": complexity.get("function_count", 0),
            "total_classes": complexity.get("class_count", 0),
            "average_complexity": complexity.get("average_complexity", 0),
            "max_complexity": complexity.get("max_complexity", 0),
            "maintainability": complexity.get("maintainability", 0),
            "sloc": complexity.get("size", 0),
        }

        cohesion_val = 0.0
        try:
            if hasattr(analyzer, "_calculate_file_cohesion"):
                cohesion_val = analyzer._calculate_file_cohesion() or 0.0
        except Exception:
            cohesion_val = 0.0
        summary["cohesion"] = cohesion_val

        summary["results"] = suggestions

        import json
        print(json.dumps(summary, indent=2))

        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
