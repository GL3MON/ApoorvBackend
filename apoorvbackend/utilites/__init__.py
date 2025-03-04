from apoorvbackend.src.logger import logger
import os


def load_prompt(level: str, agent_name: str) -> str:
    '''
    Load the prompt from the given path.
    '''
    try:
        with open(os.path.join('apoorvbackend/storage/prompts', level, agent_name +'.txt'), 'r') as file:
            return file.read()
        
    except FileNotFoundError:
        logger.error(f"Prompt not found for agent {agent_name}")
        return None
    
    except Exception as e:
        logger.error(f"Error loading prompt for agent {agent_name}: {e}")
        return None