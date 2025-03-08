from pydantic import BaseModel


class GuestLoginRequest(BaseModel):
    player_identifier: str