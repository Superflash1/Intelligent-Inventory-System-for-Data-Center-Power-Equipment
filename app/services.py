import base64
import csv
import json
import secrets
from collections import defaultdict
from datetime import date
from io import BytesIO, StringIO
from pathlib import Path

import httpx
from openpyxl import Workbook
from passlib.context import CryptContext
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import DeviceRecord, DictionaryItem, HiddenOption, ImageFile, SystemConfig, Task, TaskActionLog, VersionConfirmation

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class DuplicateTaskError(Exception):
    pass


def ensure_system_config(db: Session) -> SystemConfig:
    cfg = db.scalar(select(SystemConfig).limit(1))
    if not cfg:
        cfg = SystemConfig(password_configured=False, first_login_done=False)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


def set_password(db: Session, password: str) -> None:
    cfg = ensure_system_config(db)
    cfg.password_hash = pwd_context.hash(password)
    cfg.password_configured = True
    db.add(cfg)
    db.commit()


def verify_login(db: Session, password: str) -> str | None:
    cfg = ensure_system_config(db)
    if not cfg.first_login_done:
        cfg.first_login_done = True
        token = secrets.token_urlsafe(32)
        cfg.current_session_token = token
        db.add(cfg)
        db.commit()
        return token

    if not cfg.password_configured or not cfg.password_hash:
        return None

    if not pwd_context.verify(password, cfg.password_hash):
        return None

    token = secrets.token_urlsafe(32)
    cfg.current_session_token = token
    db.add(cfg)
    db.commit()
    return token


def validate_session_token(db: Session, token: str | None) -> bool:
    if not token:
        return False
    cfg = ensure_system_config(db)
    return bool(cfg.current_session_token and cfg.current_session_token == token)


def clear_session_token(db: Session) -> None:
    cfg = ensure_system_config(db)
    cfg.current_session_token = None
    db.add(cfg)
    db.commit()


def get_llm_config(db: Session) -> dict:
    cfg = ensure_system_config(db)
    return {
        "base_url": cfg.llm_base_url,
        "model": cfg.llm_model,
        "timeout_seconds": cfg.llm_timeout_seconds or 60,
        "enabled": bool(cfg.llm_enabled),
        "has_api_key": bool(cfg.llm_api_key),
    }


def set_llm_config(
    db: Session,
    base_url: str,
    api_key: str,
    model: str,
    timeout_seconds: int = 60,
    enabled: bool = False,
) -> dict:
    cfg = ensure_system_config(db)
    cfg.llm_base_url = base_url.strip()
    cfg.llm_api_key = api_key.strip()
    cfg.llm_model = model.strip()
    cfg.llm_timeout_seconds = max(10, int(timeout_seconds))
    cfg.llm_enabled = enabled
    db.add(cfg)
    db.commit()
    return get_llm_config(db)


def get_rule_config(db: Session) -> dict:
    cfg = ensure_system_config(db)
    min_conf = cfg.rule_min_confidence
    return {
        "min_confidence": float(min_conf) if min_conf not in (None, "") else 0.0,
        "require_serial_number": bool(cfg.rule_require_serial_number),
    }


def set_rule_config(db: Session, min_confidence: float, require_serial_number: bool) -> dict:
    cfg = ensure_system_config(db)
    cfg.rule_min_confidence = str(min_confidence)
    cfg.rule_require_serial_number = require_serial_number
    db.add(cfg)
    db.commit()
    return get_rule_config(db)


def log_action(db: Session, action_type: str, message: str, task_id: int | None = None) -> None:
    db.add(TaskActionLog(task_id=task_id, action_type=action_type, message=message))
    db.commit()


def add_dict_value(db: Session, category: str, value: str) -> None:
    value = value.strip()
    if not value:
        return
    existing = db.scalar(select(DictionaryItem).where(DictionaryItem.category == category, DictionaryItem.value == value))
    if existing:
        return
    db.add(DictionaryItem(category=category, value=value))
    db.commit()


def list_field_options(db: Session, category: str) -> list[str]:
    allowed = {"city", "site", "device_type", "person", "brand", "model", "serial_number", "production_date"}
    if category not in allowed:
        return []

    hidden_values = {
        v
        for v in db.scalars(select(HiddenOption.value).where(HiddenOption.category == category)).all()
        if isinstance(v, str) and v.strip()
    }

    values: set[str] = set()

    if category in {"city", "site", "device_type", "person"}:
        field = getattr(Task, category)
        rows = db.scalars(select(field).where(field.is_not(None))).all()
        for row in rows:
            text = str(row or "").strip()
            if text:
                values.add(text)

    if category in {"brand", "model", "serial_number", "production_date"}:
        field = getattr(DeviceRecord, category)
        rows = db.scalars(select(field).where(field.is_not(None))).all()
        for row in rows:
            text = str(row or "").strip()
            if text:
                values.add(text)

    if category in {"city", "site", "device_type"}:
        dict_rows = db.scalars(select(DictionaryItem.value).where(DictionaryItem.category == category)).all()
        for row in dict_rows:
            text = str(row or "").strip()
            if text:
                values.add(text)

    return sorted([v for v in values if v not in hidden_values])


def hide_field_option(db: Session, category: str, value: str) -> bool:
    allowed = {"city", "site", "device_type", "person", "brand", "model", "serial_number", "production_date"}
    if category not in allowed:
        return False

    clean_value = (value or "").strip()
    if not clean_value:
        return False

    existing = db.scalar(select(HiddenOption).where(HiddenOption.category == category, HiddenOption.value == clean_value))
    if existing:
        return True

    db.add(HiddenOption(category=category, value=clean_value))
    db.commit()
    return True


def create_task(
    db: Session,
    city: str,
    site: str,
    device_type: str,
    inventory_date: date,
    person: str | None = None,
) -> tuple[Task, str, str]:
    duplicate = db.scalar(
        select(Task).where(
            Task.city == city,
            Task.site == site,
            Task.device_type == device_type,
            Task.inventory_date == inventory_date,
        )
    )
    if duplicate:
        raise DuplicateTaskError("同一天同站点同类型任务已存在")

    existing_group = db.scalars(
        select(Task).where(Task.city == city, Task.site == site, Task.device_type == device_type)
    ).all()

    kind = "new"
    message = "创建成功"
    status = "pending_confirm"

    if existing_group:
        kind = "update"
        message = "检测到历史任务，已作为更新任务创建，待人工确认版本"

    task = Task(
        city=city,
        site=site,
        device_type=device_type,
        person=(person or "").strip() or None,
        inventory_date=inventory_date,
        status=status,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    add_dict_value(db, "city", city)
    add_dict_value(db, "site", site)
    add_dict_value(db, "device_type", device_type)
    log_action(db, "task_created", f"创建任务：{city}/{site}/{device_type}/{inventory_date}", task.id)

    return task, kind, message


def fake_vision_recognize(file_path: Path) -> dict:
    stem = file_path.stem
    parts = stem.split("-")
    brand = parts[0] if len(parts) > 0 else "UNKNOWN"
    model = parts[1] if len(parts) > 1 else "MODEL"
    serial = parts[2] if len(parts) > 2 else stem
    return {
        "brand": brand,
        "model": model,
        "serial_number": serial,
        "production_date": "2023-01",
        "confidence": "0.88",
        "raw_text": f"recognized from {file_path.name}",
    }


def _build_image_data_url(file_path: Path) -> str:
    suffix = file_path.suffix.lower().lstrip(".")
    mime = f"image/{'jpeg' if suffix == 'jpg' else suffix or 'jpeg'}"
    b64 = base64.b64encode(file_path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def openai_compatible_vision_recognize(db: Session, file_path: Path) -> dict:
    cfg = ensure_system_config(db)
    if not (cfg.llm_enabled and cfg.llm_base_url and cfg.llm_api_key and cfg.llm_model):
        return fake_vision_recognize(file_path)

    prompt = (
        "请识别图片中的机房动力设备铭牌，输出JSON对象，字段为: "
        "brand, model, serial_number, production_date, confidence, raw_text。"
        "若无法识别请尽量返回空字符串，confidence返回0到1字符串。"
    )
    data_url = _build_image_data_url(file_path)

    payload = {
        "model": cfg.llm_model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }

    base = cfg.llm_base_url.rstrip("/")
    url = f"{base}/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {cfg.llm_api_key}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=cfg.llm_timeout_seconds or 60) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            body = resp.json()

        text = body["choices"][0]["message"]["content"]
        if isinstance(text, list):
            text = "".join(x.get("text", "") for x in text if isinstance(x, dict))

        parsed = json.loads(text)
        return {
            "brand": str(parsed.get("brand", "")),
            "model": str(parsed.get("model", "")),
            "serial_number": str(parsed.get("serial_number", "")),
            "production_date": str(parsed.get("production_date", "")),
            "confidence": str(parsed.get("confidence", "")),
            "raw_text": str(parsed.get("raw_text", "")) or f"recognized from {file_path.name}",
        }
    except Exception:
        return fake_vision_recognize(file_path)


def _validate_record(record: dict, min_confidence: float, require_serial_number: bool) -> tuple[str, str | None]:
    errors = []
    conf_raw = str(record.get("confidence", "") or "").strip()
    conf_val = 0.0
    try:
        conf_val = float(conf_raw)
    except Exception:
        conf_val = 0.0

    if conf_val < min_confidence:
        errors.append(f"置信度低于阈值({min_confidence})")

    serial = str(record.get("serial_number", "") or "").strip()
    if require_serial_number and not serial:
        errors.append("序列号缺失")

    if errors:
        return "fail", "；".join(errors)
    return "pass", None


def save_recognition(db: Session, task: Task, image_records: list[tuple[int, dict]]) -> int:
    cfg = ensure_system_config(db)
    min_conf = float(cfg.rule_min_confidence) if cfg.rule_min_confidence not in (None, "") else 0.0
    require_serial = bool(cfg.rule_require_serial_number)

    count = 0
    fail_count = 0
    for image_id, rec in image_records:
        status, message = _validate_record(rec, min_conf, require_serial)
        if status == "fail":
            fail_count += 1

        db.add(
            DeviceRecord(
                task_id=task.id,
                image_id=image_id,
                brand=rec.get("brand"),
                model=rec.get("model"),
                serial_number=rec.get("serial_number"),
                production_date=rec.get("production_date"),
                confidence=rec.get("confidence"),
                raw_text=rec.get("raw_text"),
                validation_status=status,
                validation_message=message,
            )
        )
        count += 1
    db.commit()
    log_action(db, "recognized", f"识别完成：{count}条，校验失败{fail_count}条", task.id)
    return count


def pending_groups(db: Session) -> list[dict]:
    pending_tasks = db.scalars(select(Task).where(Task.status == "pending_confirm")).all()
    grouped_pending = defaultdict(list)
    for t in pending_tasks:
        grouped_pending[(t.city, t.site, t.device_type)].append(t)

    out = []
    for (city, site, device_type), pending_list in grouped_pending.items():
        total_in_group = db.scalar(
            select(func.count())
            .select_from(Task)
            .where(Task.city == city, Task.site == site, Task.device_type == device_type)
        )

        # 至少存在一个历史版本（active/inactive/pending 中任一）时，才需要人工确认更新
        if (total_in_group or 0) >= 2:
            out.append(
                {
                    "city": city,
                    "site": site,
                    "device_type": device_type,
                    "tasks": sorted(pending_list, key=lambda x: x.inventory_date, reverse=True),
                }
            )
    return out


def confirm_active_task(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if not task:
        raise ValueError("任务不存在")

    same_group = db.scalars(
        select(Task).where(Task.city == task.city, Task.site == task.site, Task.device_type == task.device_type)
    ).all()

    for t in same_group:
        t.status = "active" if t.id == task_id else "inactive"
        db.add(t)

    old = db.scalars(
        select(VersionConfirmation).where(
            VersionConfirmation.city == task.city,
            VersionConfirmation.site == task.site,
            VersionConfirmation.device_type == task.device_type,
        )
    ).all()
    for o in old:
        db.delete(o)

    db.add(
        VersionConfirmation(
            city=task.city,
            site=task.site,
            device_type=task.device_type,
            active_task_id=task_id,
        )
    )
    db.commit()
    log_action(db, "version_confirmed", f"确认任务 {task_id} 为有效版本", task_id)
    db.refresh(task)
    return task


def summary_data(db: Session) -> list[dict]:
    active_tasks = db.scalars(select(Task).where(Task.status == "active")).all()
    result = []
    for task in active_tasks:
        devices_count = len(task.devices)
        validation_fail_count = sum(1 for d in task.devices if d.validation_status == "fail")
        result.append(
            {
                "city": task.city,
                "site": task.site,
                "device_type": task.device_type,
                "person": task.person,
                "inventory_date": task.inventory_date,
                "status": task.status,
                "devices_count": devices_count,
                "validation_fail_count": validation_fail_count,
            }
        )
    return result


def export_summary_csv_text(db: Session) -> str:
    rows = summary_data(db)
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["city", "site", "device_type", "person", "inventory_date", "status", "devices_count", "validation_fail_count"])
    for r in rows:
        writer.writerow(
            [
                r["city"],
                r["site"],
                r["device_type"],
                r.get("person") or "",
                r["inventory_date"],
                r["status"],
                r["devices_count"],
                r["validation_fail_count"],
            ]
        )
    # utf-8-sig，避免Excel打开CSV中文乱码
    return "\ufeff" + buffer.getvalue()


def export_summary_excel_bytes(db: Session) -> bytes:
    rows = summary_data(db)
    wb = Workbook()
    ws = wb.active
    ws.title = "全省汇总"
    ws.append(["地市", "站点", "设备类型", "人员", "盘点日期", "状态", "设备数量", "校验失败数"])
    for r in rows:
        ws.append(
            [
                r["city"],
                r["site"],
                r["device_type"],
                r.get("person") or "",
                str(r["inventory_date"]),
                r["status"],
                r["devices_count"],
                r["validation_fail_count"],
            ]
        )
    out = BytesIO()
    wb.save(out)
    return out.getvalue()


def export_task_detail_excel_bytes(db: Session, task_id: int) -> bytes:
    task = db.get(Task, task_id)
    if not task:
        raise ValueError("任务不存在")

    records = db.scalars(select(DeviceRecord).where(DeviceRecord.task_id == task_id).order_by(DeviceRecord.created_at.desc())).all()

    wb = Workbook()
    ws = wb.active
    ws.title = f"任务{task_id}汇总"
    ws.append(["任务ID", "地市", "站点", "设备类型", "人员", "盘点日期", "状态"])
    ws.append([task.id, task.city, task.site, task.device_type, task.person or "", str(task.inventory_date), task.status])
    ws.append([])
    ws.append(["记录ID", "图片ID", "品牌", "型号", "序列号", "生产日期", "置信度", "校验", "校验信息"])
    for r in records:
        ws.append([
            r.id,
            r.image_id,
            r.brand or "",
            r.model or "",
            r.serial_number or "",
            r.production_date or "",
            r.confidence or "",
            r.validation_status,
            r.validation_message or "",
        ])

    out = BytesIO()
    wb.save(out)
    return out.getvalue()


def delete_image_file(db: Session, image_id: int) -> bool:
    img = db.get(ImageFile, image_id)
    if not img:
        return False

    file_path = Path(img.file_path)
    task_id = img.task_id

    # 删除与该图片绑定的识别记录，保证汇总同步更新
    records = db.scalars(select(DeviceRecord).where(DeviceRecord.image_id == image_id)).all()
    for r in records:
        db.delete(r)

    db.delete(img)
    db.commit()

    if file_path.exists():
        try:
            file_path.unlink()
        except Exception:
            pass

    log_action(db, "image_deleted", f"删除图片 {image_id}，同步删除识别记录 {len(records)} 条", task_id)
    return True


def list_logs(db: Session, limit: int = 200) -> list[TaskActionLog]:
    return db.scalars(select(TaskActionLog).order_by(TaskActionLog.created_at.desc()).limit(limit)).all()


def delete_task(db: Session, task_id: int) -> bool:
    task = db.get(Task, task_id)
    if not task:
        return False

    # 删除文件
    for img in task.images:
        file_path = Path(img.file_path)
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass

    # 清理版本确认记录
    confirmations = db.scalars(select(VersionConfirmation).where(VersionConfirmation.active_task_id == task_id)).all()
    for c in confirmations:
        db.delete(c)

    db.delete(task)
    db.commit()
    log_action(db, "task_deleted", f"删除任务 {task_id}", task_id)
    return True


def llm_test(db: Session, text: str = "ping") -> dict:
    cfg = ensure_system_config(db)
    if not (cfg.llm_base_url and cfg.llm_api_key and cfg.llm_model):
        return {"ok": False, "message": "请先完整配置 Base URL / API Key / Model"}

    base = cfg.llm_base_url.rstrip("/")
    url = f"{base}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg.llm_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": cfg.llm_model,
        "messages": [{"role": "user", "content": f"请回复OK：{text}"}],
        "temperature": 0,
    }

    try:
        with httpx.Client(timeout=cfg.llm_timeout_seconds or 60) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            body = resp.json()

        content = body["choices"][0]["message"]["content"]
        return {"ok": True, "message": str(content)}
    except Exception as e:
        return {"ok": False, "message": str(e)}
