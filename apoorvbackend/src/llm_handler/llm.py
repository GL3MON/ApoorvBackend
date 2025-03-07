from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from apoorvbackend.src.llm_handler.load_balancer import LoadBalancer

load_dotenv()


class LLM:

    @staticmethod
    def get_llama_llm(temperature=0.5, timeout=10):
        return ChatOpenAI(
            model=os.getenv("LLAMA_MODEL_NAME"),
            api_key=os.getenv("LLAMA_API_KEY"),
            temperature=temperature,
            base_url=os.getenv("LLAMA_BASE_URL"),
            timeout=timeout
        )

    @staticmethod
    def get_gemini_llm(temperature=0.5, timeout=10, max_retries=4):
        lb = LoadBalancer(n=1, ct=1)
        key = lb.StdDev()
        return ChatGoogleGenerativeAI(
            model=os.getenv("MODEL_NAME"),
            api_key=key,
            temperature=temperature,
            timeout=timeout,
            max_retries=max_retries,
        )
