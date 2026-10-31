from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field

Role = Literal["citizen", "supervisor", "collector", "admin"]
Category = Literal["Mixed Waste", "Plastic", "Construction Debris", "Organic", "Hazardous", "E-waste"]
Status = Literal["submitted", "review", "verified", "assigned", "accepted", "way", "arrived", "cleaning", "await", "resolved", "rejected"]

class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    # Public registration can never grant a privileged role.

class LoginIn(BaseModel): email: EmailStr; password: str
class UserOut(BaseModel): model_config = ConfigDict(from_attributes=True); id: int; name: str; email: EmailStr; role: str; created_at: datetime
class TokenOut(BaseModel): access_token: str; token_type: str = "bearer"; user: UserOut
class ReportOut(BaseModel):
    id: str; category: str; severity: str; description: str; latitude: float | None; longitude: float | None
    location_text: str | None; image_url: str; status: str; predicted_category: str | None
    confidence_score: float | None; ai_status: str; requires_human_review: bool; supervisor_remarks: str | None
    assigned_to: str | None; created_at: datetime; owner_id: int
class StatusIn(BaseModel): status: Status; remarks: str | None = Field(default=None, max_length=2000)
class AssignIn(BaseModel): collector_email: EmailStr
