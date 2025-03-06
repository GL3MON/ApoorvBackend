from fastapi import FastAPI, Query
import uvicorn
from dotenv import load_dotenv

from apoorvbackend.src.logger import logger
from apoorvbackend.src.llm_handler.handler import Handler as LLMHandler
from apoorvbackend.src.models.chat_models import ChatRequest
from apoorvbackend.src.prompt_loader.loader import PromptLoader
from langchain_core.messages import AIMessage, HumanMessage
from apoorvbackend.src.redis.redis_handlers import RedisChatHandler

load_dotenv()

app = FastAPI()

handler = LLMHandler()
redis_handler = RedisChatHandler()  

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/chat/")
def chat_with_actor(chat_request: ChatRequest):
    user_id = chat_request.user_id
    level = chat_request.level
    actor = chat_request.actor
    user_input = chat_request.user_input

    logger.info(f"Chatting with actor {actor} at level {level} for user {user_id}")

    chat_history = redis_handler.load_chat_history(user_id, level, actor)
    chat_history = [] if chat_history is None else chat_history

    prompt = PromptLoader.get_prompt_template(level, actor)

    chat_history.append(HumanMessage(content=user_input))
    response = handler.get_response(user_input, prompt, chat_history)
    chat_history.append(response)

    redis_handler.save_chat_history(user_id, level, actor, chat_history)

    logger.info(f"Response: {response.content}")
    return response.content

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1")
