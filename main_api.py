from apoorvbackend.src.logger import logger
from apoorvbackend.src.llm_handler.handler import Handler as LLMHandler
from apoorvbackend.src.prompt_loader.loader import PromptLoader
from langchain_core.messages import AIMessage, HumanMessage
from fastapi import FastAPI
import uvicorn
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

handler = LLMHandler()

global test_chat_history
test_chat_history = [
    HumanMessage(content="Hello, how are you?"),
    AIMessage(content="I'm good, thank you! How can I assist you today?"),
    HumanMessage(content="Can you tell me a joke?"),
    AIMessage(content="Sure! Why don't scientists trust atoms? Because they make up everything!")
]

@app.get("/")
async def root():
    return {"message": "Hello World"}

# TODO: Change it to POST Request.
@app.get("/chat/")
def chat_with_actor(level: str, actor: str, user_input: str):
    global test_chat_history
    logger.info(f"Chatting with actor {actor} at level {level}")
    prompt = PromptLoader.get_prompt_template(level, actor)
    response = handler.get_response(user_input, prompt, test_chat_history)
    test_chat_history = response

    logger.info(f"Response: {response[-1].content}")

    return response[-1].content

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1")
