import datetime
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    domain: str
    title: str
    message: str
    notification_type: str
    severity: str
    is_read: bool
    read_at: Optional[datetime.datetime] = None
    link: Optional[str] = None
    metadata_json: Dict[str, Any] = {}
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationUnreadCount(BaseModel):
    unread_count: int
    by_domain: Dict[str, int] = {}


class NotificationListResponse(BaseModel):
    items: List[NotificationRead]
    total: int
    unread_count: int
