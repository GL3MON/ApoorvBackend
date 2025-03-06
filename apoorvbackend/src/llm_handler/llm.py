from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv
import os
from apoorvbackend.src.llm_handler.load_balancer import LoadBalancer

load_dotenv()


class LLM:

    @staticmethod
    def get_ollama_llm(temperature=0.5, timeout=10):
        return ChatOpenAI(
            base_url=os.getenv("OLLAMA_BASE_URL"),
            api_key='ollama',
            model=os.getenv("OLLAMA_MODEL_NAME"),
            temperature=temperature,
            request_timeout=timeout
        )

    @staticmethod
    def get_gemini_llm(temperature=0.5, timeout=10, max_retries=4):
        lb = LoadBalancer(n=10, ct=10)
        key = lb.StdDev()
        return ChatGoogleGenerativeAI(
            model=os.getenv("MODEL_NAME"),
            api_key=key,
            temperature=temperature,
            timeout=timeout,
            max_retries=max_retries,
        )