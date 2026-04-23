from locust import HttpUser, task, between
import random
from datetime import datetime, timedelta

class DeviceStatsUser(HttpUser):
    wait_time = between(0.5, 2)
    
    def on_start(self):
        self.user_id = None
        self.device_ids = []
        self.last_task_id = None
        
        response = self.client.post(
            "/users",
            json={"name": f"user_{random.randint(1, 10000000)}"}
        )
        if response.status_code == 200:
            self.user_id = response.json()["id"]
        
        if self.user_id:
            for i in range(5):
                response = self.client.post(
                    "/devices",
                    json={
                        "name": f"device_{self.user_id}_{i}_{random.randint(1, 10000000)}",
                        "user_id": self.user_id
                    }
                )
                if response.status_code == 200:
                    self.device_ids.append(response.json()["device_id"])
    
    @task(5)
    def add_measurement(self):
        if not self.device_ids:
            return
        device_id = random.choice(self.device_ids)
        self.client.post(
            f"/devices/{device_id}/data",
            json={
                "x": random.uniform(0, 100),
                "y": random.uniform(0, 100),
                "z": random.uniform(0, 100)
            },
            name="/devices/{id}/data"
        )
    
    @task(3)
    def get_device_analytics_all_time(self):
        if not self.device_ids:
            return
        device_id = random.choice(self.device_ids)
        response = self.client.post(
            f"/analytics/device/{device_id}",
            name="/analytics/device/{id} (all time)"
        )
        if response.status_code == 200:
            self.last_task_id = response.json().get("task_id")
    
    @task(2)
    def get_device_analytics_last_5_seconds(self):
        if not self.device_ids:
            return
        device_id = random.choice(self.device_ids)
        from_ts = (datetime.now() - timedelta(seconds=5)).isoformat()
        to_ts = datetime.now().isoformat()
        response = self.client.post(
            f"/analytics/device/{device_id}?from_ts={from_ts}&to_ts={to_ts}",
            name="/analytics/device/{id} (last 5 sec)"
        )
        if response.status_code == 200:
            self.last_task_id = response.json().get("task_id")
    
    @task(2)
    def get_user_analytics_all_time(self):
        if self.user_id is None:
            return
        response = self.client.post(
            f"/analytics/user/{self.user_id}",
            name="/analytics/user/{id} (all time)"
        )
        if response.status_code == 200:
            self.last_task_id = response.json().get("task_id")
    
    @task(1)
    def get_user_analytics_last_5_seconds(self):
        if self.user_id is None:
            return
        from_ts = (datetime.now() - timedelta(seconds=5)).isoformat()
        to_ts = datetime.now().isoformat()
        response = self.client.post(
            f"/analytics/user/{self.user_id}?from_ts={from_ts}&to_ts={to_ts}",
            name="/analytics/user/{id} (last 5 sec)"
        )
        if response.status_code == 200:
            self.last_task_id = response.json().get("task_id")
    
    @task(1)
    def get_analytics_result(self):
        if self.last_task_id is None:
            return
        self.client.get(
            f"/analytics/result/{self.last_task_id}",
            name="/analytics/result/{task_id}"
        )
