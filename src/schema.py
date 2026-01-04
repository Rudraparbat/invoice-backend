from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator
import uuid
from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass

class UserCreate(schemas.BaseUserCreate):
    pass

class UserUpdate(schemas.BaseUserUpdate):
    pass



class BaseResponseSchema(BaseModel):
    success : bool
    data : dict
    error : Optional[str] = None
    
    class Config:
        from_attributes = True


class TruckInvoiceRequest(BaseModel):
    sl_no: int  # Serial number
    date_time: datetime
    car_number: str  # e.g., "WB 33A 3212"
    wheels: int  # Number of wheels
    cargo_type: str  # e.g., "Sand"
    cft: float  # Cubic feet (weight/volume)