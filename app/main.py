from fastapi import FastAPI
from app.api.v1 import router as v1_router

app = FastAPI()
app.include_router(v1_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
