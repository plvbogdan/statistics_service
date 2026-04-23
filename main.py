from fastapi import FastAPI
from database import init_db
from routers.users import router as users_router
from routers.devices import router as devices_router
from routers.analytics import router as analytics_router

app = FastAPI(title="Device Stats Service")

app.include_router(users_router)
app.include_router(devices_router)
app.include_router(analytics_router)


@app.on_event("startup")
async def startup():
    await init_db()
