from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
from load_balancer import LoadBalancer

load_dotenv()


class LLM:

    @staticmethod
    def get_llm(temperature = 0.5, timeout=10, max_retries=4):
        lb = LoadBalancer(n=10,ct=10)
        key = lb.StdDev()
        llm = ChatGoogleGenerativeAI(
            model=os.getenv("MODEL_NAME"),
            api_key=key,
            temperature=temperature,           
            timeout=timeout,
            max_retries=max_retries,
        )
        
        return llm

l = LLM()
print(l.get_llm())