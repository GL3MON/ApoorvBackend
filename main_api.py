from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, Header, HTTPException
import uvicorn
from dotenv import load_dotenv  
from fastapi.middleware.cors import CORSMiddleware
import os
import httpx

from apoorvbackend.src.logger import logger
from apoorvbackend.src.llm_handler.handler import Handler as LLMHandler
from apoorvbackend.src.llm_handler.llm import LLM
from apoorvbackend.src.models.chat_models import ChatRequest
from apoorvbackend.src.models.lootlocker_models import GuestLoginRequest
from apoorvbackend.src.prompt_loader.loader import PromptLoader
from langchain_core.messages import AIMessage, HumanMessage
from apoorvbackend.src.redis.redis_handlers import RedisChatHandler
from apoorvbackend.src.database.postgres_backup import PostgresBackupService

load_dotenv()

postgres_backup_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize services
    global postgres_backup_service
    postgres_backup_service = PostgresBackupService(interval_minutes=5)
    postgres_backup_service.start()
    logger.info("Backup scheduler started")
    
    yield
    
    # Shutdown: cleanup
    if postgres_backup_service:
        postgres_backup_service.stop()
        logger.info("Backup scheduler stopped")

# Create the FastAPI app with the lifespan
app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

handler = LLMHandler()
redis_handler = RedisChatHandler()  

# @TODO: Add game key to .env
GAME_KEY = os.getenv("GAME_KEY", "your_game_key_here")

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/chat/")
def chat_with_actor(chat_request: ChatRequest):
    user_id = chat_request.user_id
    level = chat_request.level
    actor = chat_request.actor
    user_input = chat_request.user_input

    chat_history = redis_handler.load_chat_history(user_id, level, actor)
    chat_history = [] if chat_history is None else chat_history

    prompt = PromptLoader.get_prompt_template(level, actor)

    chat_history.append(HumanMessage(content=user_input))
    response = handler.get_response(user_input, prompt, chat_history)
    chat_history.append(response)

    redis_handler.save_chat_history(user_id, level, actor, chat_history)

    logger.info(f"Response: {response.content} Flag: {response.additional_kwargs['flag']}")
    return {"message": response.content, "flag": response.additional_kwargs["flag"]}

# Test Function
@app.post("/ask/")
def ask(question: ChatRequest):
    ques = question.user_input
    llm = LLM.get_llama_llm()
    response = llm.invoke(ques)
    logger.info(f"Response: {response.content}")
    return response.content

# --- New Endpoints for LootLocker Proxy Calls ---

@app.post("/guest-login")
async def guest_login(request: GuestLoginRequest):
    """
    Proxy endpoint for LootLocker's guest login.
    Receives the player's identifier from the client, 
    then sends a secure request to LootLocker.
    """
    url = f"https://api.lootlocker.io/game/v2/session/guest"
    payload = {
        "game_key": GAME_KEY,
        "player_identifier": request.player_identifier,
        "game_version": "0.10.0.0"
    }
    headers = {"Content-Type": "application/json"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=response.status_code if response is not None else 500,
                detail=str(exc)
            )
    return response.json()

@app.post("/leaderboard")
async def get_leaderboard(x_session_token: str = Header(...)):
    """
    Proxy endpoint to fetch leaderboard data from LootLocker.
    Requires the client to pass the session token in the header.
    """
    url = f"https://api.lootlocker.io/game/leaderboards/twistedtalesleaderboardidtest/list"
    headers = {"x-session-token": x_session_token}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=response.status_code if response is not None else 500,
                detail=str(exc)
            )
    return response.json()

# Add a manual backup endpoint for triggering backups on demand
@app.post("/admin/backup")
async def trigger_backup():
    """Manually trigger a backup of Redis data to PostgreSQL."""
    global postgres_backup_service
    if not postgres_backup_service:
        raise HTTPException(status_code=500, detail="Backup service not initialized")
    
    try:
        postgres_backup_service.backup_now()
        return {"message": "Backup process initiated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)