from apoorvbackend.src.logger import logger
import importlib
from fastapi import FastAPI
import uvicorn
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/{level}/{actor}")
def chat_with_actor(level: str, actor: str):
    logger.info(f"Chatting with actor {actor} at level {level}")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1")

