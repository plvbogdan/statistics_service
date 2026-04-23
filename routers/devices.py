from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from database import get_db, User, Device, Measurement
from schemas import DeviceCreate, DeviceResponse, MeasurementData, MeasurementResponse

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post("/", response_model=DeviceResponse)
async def create_device(
    data: DeviceCreate,
    db: AsyncSession = Depends(get_db)
):
    
    user = await db.get(User, data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    device = Device(name=data.name, user_id=data.user_id)
    db.add(device)
    await db.commit()
    await db.refresh(device)
    
    return DeviceResponse(device_id=device.id, device_name=device.name, user_id=device.user_id)


@router.post("/{device_id}/data", response_model=MeasurementResponse)
async def add_measurement(
    device_id: int,
    data: MeasurementData,
    db: AsyncSession = Depends(get_db)
):
    
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device with id '{device_id}' not found")
    
    measurement = Measurement(
        device_id=device_id,
        x=data.x,
        y=data.y,
        z=data.z,
        timestamp=datetime.utcnow()
    )
    db.add(measurement)
    await db.commit()
    
    return MeasurementResponse(
        message="Data added",
        device_id=device_id,
        device_name=device.name,
        timestamp=measurement.timestamp.isoformat(),
        values={"x": data.x, "y": data.y, "z": data.z}
    )


@router.get("/{device_id}")
async def get_device(device_id: int, db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"id": device.id, "name": device.name, "user_id": device.user_id, "created_at": device.created_at}