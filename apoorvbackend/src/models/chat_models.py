from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str
    level: str
    actor: str
    user_input: str

class LLMResponse(BaseModel):
    '''Actors response format'''

    content: str = Field(
        description="Response from the actor",
    )

    flag: bool = Field(
        description="Flag to check if any condition that needs to be met by the user to procceed. Set only true if the user manages to meet the condition that is required by the actor to perform the next action.",
    )
