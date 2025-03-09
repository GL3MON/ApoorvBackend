from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, Header, HTTPException
import uvicorn
from dotenv import load_dotenv  
from fastapi.middleware.cors import CORSMiddleware
import os
import httpx
import math
import time
from datetime import datetime
import pytz

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
    allow_origins=["https://enigma.iiitkottayam.ac.in", "http://localhost:3000", "http://192.168.136.131:8080/", "*"],  # Specific origins
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
    
@app.post("/submit-score")
async def submit_score(request: dict):
    """
    Submit a score to the leaderboard with time-based calculation.
    
    1. Authenticates the user with LootLocker guest login
    2. Calculates a delta score based on time difference
    3. Gets the current score from leaderboard
    4. Submits the updated score (current + delta)
    """
    player_identifier = request.get("player_identifier", "")
    if not player_identifier:
        raise HTTPException(status_code=400, detail="Player identifier is required")
    
    # Step 1: Guest login to get session token
    login_url = "https://api.lootlocker.io/game/v2/session/guest"
    login_payload = {
        "game_key": GAME_KEY,
        "game_version": "0.10.0.0",
        "player_identifier": "username_1"
    }
    login_headers = {"Content-Type": "application/json"}
    
    async with httpx.AsyncClient() as client:
        try:
            login_response = await client.post(login_url, json=login_payload, headers=login_headers)
            login_response.raise_for_status()
            login_data = login_response.json()
            session_token = login_data.get("session_token", "")
            
            if not session_token:
                raise HTTPException(status_code=500, detail="Failed to obtain session token")
                
            # player_id = login_data.get("player_id", "")
            
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=login_response.status_code if login_response is not None else 500,
                detail=f"Login error: {str(exc)}"
            )
    
    # Step 2: Calculate time-based delta score    
    
    # Set reference time (11:30 AM 9th March 2025 IST)
    ist = pytz.timezone('Asia/Kolkata')
    reference_time = datetime(2025, 3, 9, 11, 30, 0, tzinfo=ist)
    reference_epoch = reference_time.timestamp()
    
    # Get current time in epoch
    current_epoch = time.time()
    
    # Calculate time difference
    tdelta = abs(current_epoch - reference_epoch)
    
    # Calculate delta score using e^(-alpha * tdelta)
    # Using alpha = 0.0001 as an example - adjust as needed
    alpha = 0.0001
    delta_score = math.exp(-alpha * tdelta)
    # Scale the score to make it more meaningful
    delta_score = round(delta_score * 1000)
    
    # Step 3: Get current score from leaderboard
    get_member_url = f"https://api.lootlocker.io/game/leaderboards/twistedtalesleaderboardidtest/member/{player_identifier}"
    headers = {"x-session-token": session_token}
    
    current_score = 0
    async with httpx.AsyncClient() as client:
        try:
            member_response = await client.get(get_member_url, headers=headers)
            # If the player exists on the leaderboard, get their current score
            if member_response.status_code == 200:
                member_data = member_response.json()
                current_score = member_data.get("score", 0)
        except httpx.HTTPError:
            # If there's an error or player doesn't exist yet, assume score is 0
            logger.info(f"Player {player_identifier} not found on leaderboard, using score 0")
    
    # Step 4: Submit updated score
    new_score = current_score + delta_score
    submit_url = "https://api.lootlocker.io/game/leaderboards/twistedtalesleaderboardidtest/submit"
    submit_payload = {
        "member_id": player_identifier,
        "score": new_score,
        "metadata": "test_run"
    }
    async with httpx.AsyncClient() as client:
        try:
            submit_response = await client.post(submit_url, json=submit_payload, headers=headers)
            submit_response.raise_for_status()
            submit_data = submit_response.json()
            return {
                "success": True, 
                "previous_score": current_score,
                "delta_score": delta_score,
                "new_score": new_score,
                "leaderboard_data": submit_data
            }
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=submit_response.status_code if submit_response is not None else 500,
                detail=f"Score submission error: {str(exc)}"
            )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)