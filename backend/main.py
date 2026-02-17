from fastapi import FastAPI
from schemas.query import Query

app = FastAPI()


@app.post("/query")
async def query(request: Query):
    return {}
