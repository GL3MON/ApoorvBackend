from apoorvbackend.src.logger import logger
import importlib
from fastapi import FastAPI
import uvicorn

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/{level}/{actor}")
def chat_with_actor(level: str, actor: str):
    logger.info(f"Chatting with actor {actor} at level {level}")
    try:
        actor_worflow = importlib.import_module(f"apoorvbackend.src.agents.{level}.{actor}.workflow")
        actor_class = getattr(actor_worflow, f"{actor.capitalize()}Agent")
        actor = actor_class().complie()
    

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1")

