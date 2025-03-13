
from fastapi import FastAPI
from calculator import Calculator

app = FastAPI()
calculator = Calculator()

@app.post("/push_data/")
def push_data(data: list[int]):
    calculator.push_data(data)
    return {"message": "Data pushed successfully"}

@app.get("/get_kcalc/{k}")
def get_kcalc(k: int):
    kcalc = calculator.get_kcalc(k)
    if kcalc:
        return {
            "amount": kcalc.amount,
            "avg": kcalc.avg,
            "min": kcalc.min,
            "max": kcalc.max,
            "variance": kcalc.variance
        }
    return {"message": "kcalc not found"}

@app.post("/recalculate/")
def recalculate(data: list[int]):
    calculator.recalculate(data)
    return {"message": "Recalculation done"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



if __name__ == "__main__":
    pass