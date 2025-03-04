from pydantic import BaseModel


class ChatRequest(BaseModel):
    user_id: str
    level: str
    actor: str
    user_input: str
