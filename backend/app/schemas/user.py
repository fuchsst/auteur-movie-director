"""
User schema definitions
"""

from pydantic import BaseModel, Field
from typing import Optional


class User(BaseModel):
    """Basic user model"""
    id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(None, description="User email")
    display_name: Optional[str] = Field(None, description="Display name")
    
    class Config:
        from_attributes = True