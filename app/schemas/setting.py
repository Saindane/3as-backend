from pydantic import BaseModel
from typing import List


class SettingResponse(BaseModel):
    key:   str
    value: str
    model_config = {"from_attributes": True}


class SettingUpdateRequest(BaseModel):
    value: str


class SettingsListResponse(BaseModel):
    items: List[SettingResponse]
