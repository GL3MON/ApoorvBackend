from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.messages import SystemMessage
from apoorvbackend.src.logger import logger
from apoorvbackend.utilites import load_prompt

class PromptLoader:

    @staticmethod
    def get_prompt_template(level: str, agent_name: str) -> ChatPromptTemplate:
        logger.info(f"Loading prompt for agent {agent_name}")
        try:
            prompt = load_prompt(level, agent_name)
            prompt_template = ChatPromptTemplate.from_messages(
                [
                    SystemMessage(
                        content=prompt
                    ),
                    MessagesPlaceholder(variable_name="messages"),
                ]
            )

            return prompt_template
        
        except Exception as e:
            logger.error(f"Error loading prompt for agent {agent_name}: {e}")
            return None