from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SystemConfig(Base):
    __tablename__ = "system_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_configured: Mapped[bool] = mapped_column(Boolean, default=False)
    first_login_done: Mapped[bool] = mapped_column(Boolean, default=False)
    current_session_token: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    llm_base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    llm_api_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    llm_timeout_seconds: Mapped[int] = mapped_column(Integer, default=60)
    llm_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    rule_min_confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rule_require_serial_number: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DictionaryItem(Base):
    __tablename__ = "dictionary_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category: Mapped[str] = mapped_column(String(50), index=True)  # city/site/device_type
    value: Mapped[str] = mapped_column(String(255), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("category", "value", name="uq_category_value"),)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    city: Mapped[str] = mapped_column(String(100), index=True)
    site: Mapped[str] = mapped_column(String(150), index=True)
    device_type: Mapped[str] = mapped_column(String(100), index=True)
    person: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    inventory_date: Mapped[Date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(30), default="pending_confirm", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    images: Mapped[list["ImageFile"]] = relationship("ImageFile", back_populates="task", cascade="all, delete-orphan")
    devices: Mapped[list["DeviceRecord"]] = relationship("DeviceRecord", back_populates="task", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("city", "site", "device_type", "inventory_date", name="uq_task_unique_day"),
    )


class ImageFile(Base):
    __tablename__ = "image_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    task: Mapped[Task] = relationship("Task", back_populates="images")


class DeviceRecord(Base):
    __tablename__ = "device_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True)
    image_id: Mapped[int | None] = mapped_column(ForeignKey("image_files.id"), nullable=True, index=True)
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model: Mapped[str | None] = mapped_column(String(150), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(150), nullable=True)
    production_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(50), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    validation_status: Mapped[str] = mapped_column(String(30), default="pass", index=True)
    validation_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    task: Mapped[Task] = relationship("Task", back_populates="devices")


class VersionConfirmation(Base):
    __tablename__ = "version_confirmations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    city: Mapped[str] = mapped_column(String(100), index=True)
    site: Mapped[str] = mapped_column(String(150), index=True)
    device_type: Mapped[str] = mapped_column(String(100), index=True)
    active_task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TaskActionLog(Base):
    __tablename__ = "task_action_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id"), nullable=True, index=True)
    action_type: Mapped[str] = mapped_column(String(50), index=True)
    message: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class HiddenOption(Base):
    __tablename__ = "hidden_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    value: Mapped[str] = mapped_column(String(255), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("category", "value", name="uq_hidden_option"),)
