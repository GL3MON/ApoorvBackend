from fastapi import FastAPI, Query
import uvicorn
from dotenv import load_dotenv  
from fastapi.middleware.cors import CORSMiddleware

from apoorvbackend.src.logger import logger
from apoorvbackend.src.llm_handler.handler import Handler as LLMHandler
from apoorvbackend.src.llm_handler.llm import LLM
from apoorvbackend.src.models.chat_models import ChatRequest
from apoorvbackend.src.prompt_loader.loader import PromptLoader
from langchain_core.messages import AIMessage, HumanMessage
from apoorvbackend.src.redis.redis_handlers import RedisChatHandler

load_dotenv()

app = FastAPI()

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

#Test Function
@app.post("/ask/")
def ask(question : ChatRequest):
    ques = question.user_input
    llm = LLM.get_llama_llm()
    response = llm.invoke(ques)
    logger.info(f"Response: {response.content}")
    return response.content

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
