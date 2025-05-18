from fastapi import FastAPI
from app.api import router


import sys
print("Python running at:", sys.executable)


app = FastAPI(
    title="Agentic AI Microservice",
    description="Agentic LLM-powered microservice for IT request automation.",
    version="1.0.0"
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Agentic AI Microservice is running!"}