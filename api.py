from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
import os

import createEmbeddings

app = FastAPI()

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    sql: str
    context: str

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.post("/api/generate-sql", response_model=QueryResponse)
async def api_generate_sql(request: QueryRequest):
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    try:
        # Running synchronously on the main thread
        print("API route hit. Passing to generate_sql...", flush=True)
        result = createEmbeddings.generate_sql(request.query)
        return QueryResponse(sql=result["sql"], context=result["context"])
    except Exception as e:
        print(f"Error generating SQL: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
