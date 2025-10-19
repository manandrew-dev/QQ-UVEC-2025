# main.py
from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from test_backend import SingleFileModularityAnalyzer
import tempfile, os

app = FastAPI(title="Code Analyzer API")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

@app.post("/analyze")
async def analyze(code: str = Form(...)):
    code_str = (code or "").strip()
    if not code_str:
        raise HTTPException(status_code=400, detail="Empty code.")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as tmp:
            tmp.write(code_str)
            tmp_path = tmp.name
        analyzer = SingleFileModularityAnalyzer(tmp_path)
        result = analyzer.analyze_file()
        return {"results": result}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
