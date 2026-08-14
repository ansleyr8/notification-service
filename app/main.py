import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Literal
from uuid import uuid4

from dotenv import load_dotenv


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field

load_dotenv()
app = FastAPI(
    title="Notification Service",
    description="This is a simple notification service built with FastAPI as the backend framework. It provides endpoints for sending notifications and checking the health of the service.",
    version="1.0.0",
)


class NotificationCreate(BaseModel):
    recipient: EmailStr
    type: Literal["email"]
    subject: str | None = None
    message: str = Field(..., min_length=1)


class Notification(NotificationCreate):
    id: str
    status: Literal["pending", "sent", "failed"]
    created_at: datetime


notifications: dict[str, Notification] = {}


def send_email(recipient: str, subject: str | None, message: str):
    sender = os.getenv("EMAIL_USERNAME")
    password = os.getenv("EMAIL_PASSWORD")

    if not sender or not password:
        raise RuntimeError("Email credentials are not configured")

    email = EmailMessage()
    email["From"] = sender
    email["To"] = recipient
    email["Subject"] = subject or "Notification"

    email.set_content(message)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender, password)
        smtp.send_message(email)


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

    status: Literal["pending", "sent", "failed"] = "pending"

    try:
        send_email(
            recipient=str(notification.recipient),
            subject=notification.subject,
            message=notification.message,
        )

        status = "sent"

    except Exception as e:
        print(f"Failed to send notification: {e}")
        status = "failed"

    new_notification = Notification(
        id=notification_id,
        recipient=notification.recipient,
        type=notification.type,
        subject=notification.subject,
        message=notification.message,
        status=status,
        created_at=datetime.now(timezone.utc),
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