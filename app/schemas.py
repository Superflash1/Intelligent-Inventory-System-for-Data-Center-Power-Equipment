from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class LoginStatusResponse(BaseModel):
    is_first_login: bool
    password_configured: bool
    need_password_on_login: bool


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    message: str
    token: str


class PasswordSetRequest(BaseModel):
    password: str = Field(min_length=6)


class MessageResponse(BaseModel):
    message: str
    message: str


class ReminderResponse(BaseModel):
    need_set_password: bool


class LLMConfigRequest(BaseModel):
    base_url: str
    api_key: str
    model: str
    timeout_seconds: int = 60
    enabled: bool = False


class LLMConfigResponse(BaseModel):
    base_url: str | None
    model: str | None
    timeout_seconds: int
    enabled: bool
    has_api_key: bool


class RuleConfigRequest(BaseModel):
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    require_serial_number: bool = True


class LLMTestRequest(BaseModel):
    text: str = "ping"


class RuleConfigResponse(BaseModel):
    min_confidence: float
    require_serial_number: bool


class TaskCreateRequest(BaseModel):
    city: str
    site: str
    device_type: str
    person: str | None = None
    inventory_date: date


class TaskCreateResponse(BaseModel):
    task_id: int
    task_kind: Literal["new", "update", "duplicate"]
    status: str
    message: str


class TaskOut(BaseModel):
    id: int
    city: str
    site: str
    device_type: str
    person: str | None = None
    inventory_date: date
    status: str

    class Config:
        from_attributes = True


class TaskListItem(TaskOut):
    devices_count: int = 0


class RecognizeResponse(BaseModel):
    task_id: int
    inserted_count: int


class RecognizeImageResponse(BaseModel):
    image_id: int
    record_id: int
    updated: bool


class DeviceRecordUpdateRequest(BaseModel):
    brand: str | None = None
    model: str | None = None
    serial_number: str | None = None
    production_date: str | None = None
    confidence: str | None = None
    raw_text: str | None = None


class ConfirmVersionRequest(BaseModel):
    task_id: int


class HideFieldOptionRequest(BaseModel):
    category: str
    value: str


class SummaryItem(BaseModel):
    city: str
    site: str
    device_type: str
    person: str | None = None
    inventory_date: date
    status: str
    devices_count: int
    validation_fail_count: int = 0


class PendingGroup(BaseModel):
    city: str
    site: str
    device_type: str
    tasks: list[TaskOut]


class DictItemOut(BaseModel):
    id: int
    category: str
    value: str
    created_at: datetime

    class Config:
        from_attributes = True


class ImageFileOut(BaseModel):
    id: int
    task_id: int
    file_name: str
    file_path: str
    created_at: datetime

    class Config:
        from_attributes = True


class DeviceRecordOut(BaseModel):
    id: int
    task_id: int
    image_id: int | None
    brand: str | None
    model: str | None
    serial_number: str | None
    production_date: str | None
    confidence: str | None
    raw_text: str | None
    validation_status: str
    validation_message: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class TaskDetailResponse(BaseModel):
    id: int
    city: str
    site: str
    device_type: str
    person: str | None = None
    inventory_date: date
    status: str
    images: list[ImageFileOut]
    device_records: list[DeviceRecordOut]


class TaskLogItem(BaseModel):
    id: int
    task_id: int | None
    action_type: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True
