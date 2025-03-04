from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage
from apoorvbackend.src.llm_handler.llm import LLM
from apoorvbackend.src.logger import logger
from typing import List, Union


class Handler:

    def __init__(self, llm: Union[None, ChatGoogleGenerativeAI] = None): 
        self.llm = llm if llm else LLM.get_llm()
        self.prompt = None
        self.chat_history = None
        self.chain = None

    
    def _get_chain(self,  prompt: ChatPromptTemplate):
        self.prompt = prompt
        return self.prompt | self.llm


    def get_response(self, user_input: str, prompt: ChatPromptTemplate, chat_history: List[BaseMessage]) -> List[BaseMessage]:
        
        self.chain = self._get_chain(prompt)
        self.chat_history = chat_history + [HumanMessage(content=user_input)]

        response = self.chain.invoke(
            {
                "messages": self.chat_history
            }
        )
        
        return response
    
