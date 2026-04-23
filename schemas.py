from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    name: str


class UserResponse(BaseModel):
    id: int
    name: str
    created_at: datetime



class DeviceCreate(BaseModel):
    name: str
    user_id: int


class DeviceResponse(BaseModel):
    device_id: int
    device_name: str
    user_id: int


class MeasurementData(BaseModel):
    x: float
    y: float
    z: float


class MeasurementResponse(BaseModel):
    message: str
    device_id: int
    device_name: str
    timestamp: str
    values: dict



class TaskResponse(BaseModel):
    task_id: str
    status: str


class TaskResult(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None
