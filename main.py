from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from calculator import Calculator

app = FastAPI()
calculator = Calculator()

class PostModel(BaseModel):
    data: List[float]
    symbol: str

class GetModel(BaseModel):
    symbol: str
    k: int

@app.post("/add_batch/")
async def push_data(data_model: PostModel):
    await calculator.push_data(data_model.data, data_model.symbol)
    return {"message": "Data pushed successfully"}

@app.get("/stats/{k}/{symbol}")
async def stats(k: int, symbol: str):
    kcalc = await calculator.get_kcalc(k, symbol)
    if kcalc:
        return kcalc
    return {"message": "kcalc not found"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)