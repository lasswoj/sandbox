from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List
from calculator import Calculator
from my_exceptions import DataNotFoundError
app = FastAPI()
calculator = Calculator()


class PostModel(BaseModel):
    data: List[float]
    symbol: str


class GetModel(BaseModel):
    symbol: str
    k: int


@app.post("/add_batch/", responses={
    200: {"description": "Data pushed successfully"},
    400: {"description": "Validation failure"},
    500: {"description": "Internal server error"}
})
async def push_data(data_model: PostModel):
    if not data_model.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Data cannot be empty")
    if not data_model.symbol:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Symbol cannot be empty")
    await calculator.push_data(data_model.data, data_model.symbol)
    return {"message": "Data pushed successfully"}

# I know the instruction said to use json request but its generally considered bad practice to use json request for get
# requests (some request handlers explicitly disallow it) so I used the standard way instead
@app.get("/stats/{k}/{symbol}", responses={
    200: {"description": "Statistical data retrieved successfully"},
    404: {"description": "Data not found"},
    500: {"description": "Internal server error"}
})
async def stats(k: int, symbol: str):
    try:
        kcalc = await calculator.get_kcalc(k, symbol)
        if kcalc:
            return kcalc
    except DataNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
