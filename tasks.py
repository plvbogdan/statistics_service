import os
from celery import Celery
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import Optional, List, Tuple
from stats_utils import calculate_metrics, empty_statistics

REDIS_URL = os.getenv("REDIS_URL")
DATABASE_URL = os.getenv("DATABASE_URL")

celery_app = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def get_measurements(device_id: int, from_ts: Optional[str], to_ts: Optional[str]) -> List[Tuple]:
    session = Session()
    try:
        sql = "SELECT x, y, z FROM measurements WHERE device_id = :device_id"
        params = {"device_id": device_id}
        
        if from_ts:
            sql += " AND timestamp >= :from_ts"
            params["from_ts"] = from_ts
        if to_ts:
            sql += " AND timestamp <= :to_ts"
            params["to_ts"] = to_ts
        
        return session.execute(text(sql), params).fetchall()
    finally:
        session.close()


def get_device_time_range(device_id: int) -> Tuple[Optional[str], Optional[str]]:
    session = Session()
    try:
        result = session.execute(
            text("""
                SELECT MIN(timestamp), MAX(timestamp) 
                FROM measurements 
                WHERE device_id = :device_id
            """),
            {"device_id": device_id}
        ).fetchone()
        first = result[0].isoformat() if result[0] else None
        last = result[1].isoformat() if result[1] else None
        return first, last
    finally:
        session.close()


def get_user_time_range(user_id: int) -> Tuple[Optional[str], Optional[str]]:
    session = Session()
    try:
        result = session.execute(
            text("""
                SELECT MIN(m.timestamp), MAX(m.timestamp)
                FROM measurements m
                JOIN devices d ON m.device_id = d.id
                WHERE d.user_id = :user_id
            """),
            {"user_id": user_id}
        ).fetchone()
        first = result[0].isoformat() if result[0] else None
        last = result[1].isoformat() if result[1] else None
        return first, last
    finally:
        session.close()


def get_user_devices(user_id: int) -> List[int]:
    session = Session()
    try:
        rows = session.execute(
            text("SELECT id FROM devices WHERE user_id = :user_id"),
            {"user_id": user_id}
        ).fetchall()
        return [row[0] for row in rows]
    finally:
        session.close()


def check_device_exists(device_id: int) -> bool:
    session = Session()
    try:
        result = session.execute(
            text("SELECT 1 FROM devices WHERE id = :device_id"),
            {"device_id": device_id}
        ).fetchone()
        return result is not None
    finally:
        session.close()


def check_user_exists(user_id: int) -> bool:
    session = Session()
    try:
        result = session.execute(
            text("SELECT 1 FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        ).fetchone()
        return result is not None
    finally:
        session.close()



def compute_device_stats(
    device_id: int,
    from_ts: Optional[str] = None,
    to_ts: Optional[str] = None
) -> dict:
    from datetime import datetime
    
    current_time = datetime.utcnow().isoformat()
    
    rows = get_measurements(device_id, from_ts, to_ts)
    
    session = Session()
    try:
        result = session.execute(
            text("SELECT name FROM devices WHERE id = :device_id"),
            {"device_id": device_id}
        ).fetchone()
        device_name = result[0] if result else None
    finally:
        session.close()
    
    if from_ts is None:
        first_ts, _ = get_device_time_range(device_id)
        period_from = first_ts if first_ts else "первое измерение"
    else:
        period_from = from_ts
    
    if to_ts is None:
        period_to = current_time
    else:
        period_to = to_ts
    
    period = {
        "from": period_from,
        "to": period_to
    }
    
    if not rows:
        return {
            "device_id": device_id,
            "device_name": device_name,
            "period": period,
            "measurements_count": 0,
            "statistics": empty_statistics()
        }
    
    x_vals = [r[0] for r in rows]
    y_vals = [r[1] for r in rows]
    z_vals = [r[2] for r in rows]
    
    return {
        "device_id": device_id,
        "device_name": device_name,
        "period": period,
        "measurements_count": len(rows),
        "statistics": calculate_metrics(x_vals, y_vals, z_vals)
    }




@celery_app.task(bind=True)
def compute_device_analytics(
    self,
    device_id: int,
    from_ts: Optional[str] = None,
    to_ts: Optional[str] = None
):
    try:
        if not check_device_exists(device_id):
            return {"error": f"Device with id '{device_id}' not found"}
        
        return compute_device_stats(device_id, from_ts, to_ts)
        
    except Exception as e:
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise


@celery_app.task(bind=True)
def compute_user_analytics(
    self,
    user_id: int,
    from_ts: Optional[str] = None,
    to_ts: Optional[str] = None
):
    from datetime import datetime
    session = Session()
    try:
        current_time = datetime.utcnow().isoformat()
        
        if from_ts is None:
            first_ts, _ = get_user_time_range(user_id)
            from_ts = first_ts if first_ts else None
        
        if to_ts is None:
            to_ts = current_time
        
        user = session.execute(
            text("SELECT id, name FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        ).fetchone()
        
        if not user:
            return {"error": f"User with id '{user_id}' not found"}
        
        user_name = user[1]
        
        devices_rows = session.execute(
            text("SELECT id, name FROM devices WHERE user_id = :user_id"),
            {"user_id": user_id}
        ).fetchall()
        
        device_ids = [row[0] for row in devices_rows]
        device_names = {row[0]: row[1] for row in devices_rows}
        
        period = {
            "from": from_ts if from_ts else "первое измерение",
            "to": current_time if to_ts == current_time else to_ts
        }
        
        if not device_ids:
            return {
                "user_id": user_id,
                "user_name": user_name,
                "period": period,
                "total": empty_statistics(),
                "devices": {}
            }
        
        devices_stats = {}
        all_x, all_y, all_z = [], [], []
        
        for device_id in device_ids:
            device_result = compute_device_stats(device_id, from_ts, to_ts)
            
            devices_stats[str(device_id)] = {
                "device_name": device_names[device_id],
                "measurements_count": device_result["measurements_count"],
                **device_result["statistics"]
            }
            
            rows = get_measurements(device_id, from_ts, to_ts)
            if rows:
                all_x.extend([r[0] for r in rows])
                all_y.extend([r[1] for r in rows])
                all_z.extend([r[2] for r in rows])
        
        total_stats = calculate_metrics(all_x, all_y, all_z)
        
        return {
            "user_id": user_id,
            "user_name": user_name,
            "period": period,
            "total": total_stats,
            "devices": devices_stats
        }
        
    except Exception as e:
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise
    finally:
        session.close()