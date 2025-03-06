from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage
from langchain.schema import HumanMessage, SystemMessage, BaseMessage
from langchain.chat_models import ChatOpenAI  # For Ollama
from apoorvbackend.src.llm_handler.llm import LLM
from apoorvbackend.src.logger import logger
from typing import List, Union
import openai
import requests

    
class Handler:

    def __init__(self):
        self.ollama_llm = LLM.get_ollama_llm()
        self.gemini_llm = LLM.get_gemini_llm()
        self.prompt = None
        self.chat_history = None
        self.chain = None

    def _get_chain(self, prompt: ChatPromptTemplate, llm):
        self.prompt = prompt
        return self.prompt | llm

    def get_response(self, user_input: str, prompt: ChatPromptTemplate, chat_history: List[BaseMessage]) -> List[BaseMessage]:

        self.chat_history = chat_history + [HumanMessage(content=user_input)]

        try:
            # Try Ollama
            self.chain = self._get_chain(prompt, self.ollama_llm)
            response = self.chain.invoke(
                {
                    "messages": self.chat_history
                }
            )
            return response

        except (openai.error.OpenAIError, requests.exceptions.RequestException) as e:
            # Fallback to Gemini
            try:
                self.chain = self._get_chain(prompt, self.gemini_llm) # Pass Gemini LLM to the chain
                response = self.chain.invoke(
                    {
                        "messages": 
                        self.chat_history
                    }
                )
                return response

            except Exception as e:
                logger.error(f"Gemini error: {e}")
                raise  

        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise 