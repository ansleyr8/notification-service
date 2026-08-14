from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4



from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="Notification Service",
    description="This is a simple notification service built with FastAPI as the backend framework. It provides endpoints for sending notifications and checking the health of the service.",
    version="1.0.0",
)

class NotificationCreate(BaseModel):
    recipient: str = Field(..., min_length=1)
    type: Literal["email", "sms", "push"]
    subject: str | None = None
    message: str = Field(..., min_length=1)

class Notification(NotificationCreate):
    id: str
    status:Literal["pending", "sent", "failed"]
    created_at: datetime

notifications: dict[str, Notification] = {}


@app.get("/")
def root():
    return {
        "message": "Hello, Notification service is up and running!"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }

@app.post("/notifications", response_model=Notification, status_code=201)
def create_notification(notification: NotificationCreate):

    notification_id = str(uuid4())

    new_notification = Notification(
        id=notification_id,
        recipient=notification.recipient,
        type=notification.type,
        subject=notification.subject,
        message=notification.message,
        status="pending",
        created_at=datetime.now(timezone.utc)
    )

    notifications[notification_id] = new_notification

    return new_notification

@app.get("/notifications", response_model=list[Notification])
def get_notifications():
    return list(notifications.values())

@app.get("/notifications/{notification_id}", response_model=Notification)
def get_notification(notification_id: str):
    notification = notifications.get(notification_id)

    if notification is None:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )
    return notification