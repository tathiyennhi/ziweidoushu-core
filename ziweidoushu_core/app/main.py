from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from ziweidoushu_core.calendar.lunar import solar_to_lunar, lunar_to_solar

app = FastAPI(title="ZiWei Core API", version="0.1.0")

@app.get("/v1/healthz")
def healthz():
    return {"ok": True}

class SolarReq(BaseModel):
    dob: str                 # "YYYY-MM-DD"
    tz: str = "Asia/Ho_Chi_Minh"

class LunarReq(BaseModel):
    year: int
    month: int
    day: int
    is_leap: bool = False
    tz: str = "Asia/Ho_Chi_Minh"

@app.post("/v1/solar-to-lunar")
def api_solar_to_lunar(req: SolarReq):
    # time-of-day không ảnh hưởng tới lịch âm; chỉ cần ngày + tz
    dt = datetime.strptime(req.dob, "%Y-%m-%d")
    lunar = solar_to_lunar(dt, req.tz)
    return {"input": req.model_dump(), "result": lunar}

@app.post("/v1/lunar-to-solar")
def api_lunar_to_solar(req: LunarReq):
    d = lunar_to_solar(req.year, req.month, req.day, req.is_leap, req.tz)
    return {"input": req.model_dump(), "result": d.isoformat()}
