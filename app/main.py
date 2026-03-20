from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import DeviceRecord, DictionaryItem, ImageFile, Task
from app.schemas import (
    ConfirmVersionRequest,
    DeviceRecordUpdateRequest,
    DictItemOut,
    HideFieldOptionRequest,
    ImageFileOut,
    LLMConfigRequest,
    LLMConfigResponse,
    LLMTestRequest,
    LoginRequest,
    LoginResponse,
    LoginStatusResponse,
    MessageResponse,
    PasswordSetRequest,
    PendingGroup,
    RecognizeImageResponse,
    RecognizeResponse,
    ReminderResponse,
    RuleConfigRequest,
    RuleConfigResponse,
    SummaryItem,
    TaskCreateRequest,
    TaskCreateResponse,
    TaskDetailResponse,
    TaskListItem,
    TaskLogItem,
)
from app.services import (
    DuplicateTaskError,
    confirm_active_task,
    create_task,
    delete_image_file,
    delete_task,
    ensure_system_config,
    export_summary_csv_text,
    export_summary_excel_bytes,
    export_task_detail_excel_bytes,
    get_llm_config,
    get_rule_config,
    hide_field_option,
    list_field_options,
    list_logs,
    llm_test,
    log_action,
    openai_compatible_vision_recognize,
    pending_groups,
    save_recognition,
    set_llm_config,
    clear_session_token,
    set_password,
    set_rule_config,
    summary_data,
    validate_session_token,
    verify_login,
)

app = FastAPI(title="机房动力设备智能盘点系统 MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

Base.metadata.create_all(bind=engine)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


with engine.begin() as conn:
    for ddl in [
        "ALTER TABLE system_config ADD COLUMN llm_base_url VARCHAR(500)",
        "ALTER TABLE system_config ADD COLUMN llm_api_key VARCHAR(500)",
        "ALTER TABLE system_config ADD COLUMN llm_model VARCHAR(120)",
        "ALTER TABLE system_config ADD COLUMN llm_timeout_seconds INTEGER DEFAULT 60",
        "ALTER TABLE system_config ADD COLUMN llm_enabled BOOLEAN DEFAULT 0",
        "ALTER TABLE system_config ADD COLUMN rule_min_confidence VARCHAR(20)",
        "ALTER TABLE system_config ADD COLUMN rule_require_serial_number BOOLEAN DEFAULT 1",
        "ALTER TABLE device_records ADD COLUMN validation_status VARCHAR(30) DEFAULT 'pass'",
        "ALTER TABLE device_records ADD COLUMN validation_message VARCHAR(500)",
        "ALTER TABLE device_records ADD COLUMN image_id INTEGER",
        "ALTER TABLE tasks ADD COLUMN person VARCHAR(100)",
        "ALTER TABLE system_config ADD COLUMN current_session_token VARCHAR(255)",
    ]:
        try:
            conn.execute(text(ddl))
        except Exception:
            pass

    try:
        conn.execute(
            text(
                "CREATE TABLE hidden_options ("
                "id INTEGER PRIMARY KEY, "
                "category VARCHAR(50), "
                "value VARCHAR(255), "
                "created_at DATETIME"
                ")"
            )
        )
    except Exception:
        pass


@app.get("/health")
def health():
    return {"status": "ok"}


def require_auth(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if not validate_session_token(db, token):
        raise HTTPException(status_code=401, detail="未登录或登录已失效，请重新登录")


@app.get("/auth/status", response_model=LoginStatusResponse)
def auth_status(db: Session = Depends(get_db)):
    cfg = ensure_system_config(db)
    return LoginStatusResponse(
        is_first_login=not cfg.first_login_done,
        password_configured=cfg.password_configured,
        need_password_on_login=cfg.first_login_done,
    )


@app.post("/auth/set-password", response_model=MessageResponse)
def auth_set_password(body: PasswordSetRequest, db: Session = Depends(get_db)):
    set_password(db, body.password)
    return MessageResponse(message="密码配置成功")


@app.post("/auth/login", response_model=LoginResponse)
def auth_login(body: LoginRequest, db: Session = Depends(get_db)):
    token = verify_login(db, body.password)
    if not token:
        raise HTTPException(status_code=401, detail="登录失败，请检查密码或先配置密码")
    return LoginResponse(message="登录成功", token=token)


@app.post("/auth/logout", response_model=MessageResponse)
def auth_logout(db: Session = Depends(get_db)):
    clear_session_token(db)
    return MessageResponse(message="已退出登录")


@app.get("/auth/reminder", response_model=ReminderResponse)
def auth_reminder(db: Session = Depends(get_db)):
    cfg = ensure_system_config(db)
    return ReminderResponse(need_set_password=not cfg.password_configured)


@app.post("/tasks", response_model=TaskCreateResponse)
def create_task_api(body: TaskCreateRequest, _auth: None = Depends(require_auth), db: Session = Depends(get_db)):
    try:
        task, kind, message = create_task(
            db,
            city=body.city,
            site=body.site,
            device_type=body.device_type,
            inventory_date=body.inventory_date,
            person=body.person,
        )
        return TaskCreateResponse(task_id=task.id, task_kind=kind, status=task.status, message=message)
    except DuplicateTaskError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.post("/tasks/{task_id}/upload", response_model=MessageResponse)
def upload_files(
    task_id: int,
    files: list[UploadFile] = File(...),
    _auth: None = Depends(require_auth),
    db: Session = Depends(get_db),
):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    for f in files:
        ext = Path(f.filename).suffix
        file_name = f"{uuid4().hex}{ext}"
        save_path = UPLOAD_DIR / file_name
        with save_path.open("wb") as out:
            out.write(f.file.read())
        db.add(ImageFile(task_id=task_id, file_name=f.filename, file_path=str(save_path)))
    db.commit()
    log_action(db, "images_uploaded", f"上传图片数量：{len(files)}", task_id)
    return MessageResponse(message="上传成功")


@app.post("/tasks/{task_id}/recognize", response_model=RecognizeResponse)
def recognize_task(task_id: int, _auth: None = Depends(require_auth), db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    image_records = []
    for img in task.images:
        image_records.append((img.id, openai_compatible_vision_recognize(db, Path(img.file_path))))

    inserted = save_recognition(db, task, image_records)
    return RecognizeResponse(task_id=task_id, inserted_count=inserted)


@app.post("/images/{image_id}/recognize", response_model=RecognizeImageResponse)
def recognize_one_image(image_id: int, _auth: None = Depends(require_auth), db: Session = Depends(get_db)):
    img = db.get(ImageFile, image_id)
    if not img:
        raise HTTPException(status_code=404, detail="图片不存在")

    task = db.get(Task, img.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    rec = openai_compatible_vision_recognize(db, Path(img.file_path))

    existed = db.scalar(
        select(DeviceRecord).where(DeviceRecord.task_id == task.id, DeviceRecord.image_id == image_id)
    )
    if existed:
        existed.brand = rec.get("brand")
        existed.model = rec.get("model")
        existed.serial_number = rec.get("serial_number")
        existed.production_date = rec.get("production_date")
        existed.confidence = rec.get("confidence")
        existed.raw_text = rec.get("raw_text")
        db.add(existed)
        db.commit()
        db.refresh(existed)
        return RecognizeImageResponse(image_id=image_id, record_id=existed.id, updated=True)

    inserted = save_recognition(db, task, [(image_id, rec)])
    if inserted <= 0:
        raise HTTPException(status_code=500, detail="识别结果保存失败")

    latest = db.scalar(
        select(DeviceRecord)
        .where(DeviceRecord.task_id == task.id, DeviceRecord.image_id == image_id)
        .order_by(DeviceRecord.created_at.desc())
    )
    if not latest:
        raise HTTPException(status_code=500, detail="识别结果保存失败")

    return RecognizeImageResponse(image_id=image_id, record_id=latest.id, updated=False)


@app.get("/tasks/pending-updates", response_model=list[PendingGroup])
def pending_updates(_auth: None = Depends(require_auth), db: Session = Depends(get_db)):
    return pending_groups(db)


@app.post("/tasks/confirm-active", response_model=MessageResponse)
def confirm_active(body: ConfirmVersionRequest, _auth: None = Depends(require_auth), db: Session = Depends(get_db)):
    try:
        task = confirm_active_task(db, body.task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return MessageResponse(message=f"已确认任务 {task.id} 为当前有效版本")


@app.get("/summary", response_model=list[SummaryItem])
def summary(_auth: None = Depends(require_auth), db: Session = Depends(get_db)):
    return summary_data(db)


@app.get("/dict/{category}", response_model=list[DictItemOut])
def get_dict(category: str, _auth: None = Depends(require_auth), db: Session = Depends(get_db)):
    return db.scalars(select(DictionaryItem).where(DictionaryItem.category == category)).all()


@app.get("/dict/options/{category}", response_model=list[str])
def get_field_options(category: str, _auth: None = Depends(require_auth), db: Session = Depends(get_db)):
    options = list_field_options(db, category)
    if category not in {"city", "site", "device_type", "person", "brand", "model", "serial_number", "production_date"}:
        raise HTTPException(status_code=400, detail="不支持的字段")
    return options


@app.post("/dict/options/hide", response_model=MessageResponse)
def hide_option(body: HideFieldOptionRequest, _auth: None = Depends(require_auth), db: Session = Depends(get_db)):
    ok = hide_field_option(db, body.category, body.value)
    if not ok:
        raise HTTPException(status_code=400, detail="隐藏失败，请检查字段和值")
    return MessageResponse(message="已从候选列表隐藏")


@app.get("/system/llm-config", response_model=LLMConfigResponse)
def llm_config_get(_auth: None = Depends(require_auth), db: Session = Depends(get_db)):
    return get_llm_config(db)


@app.post("/system/llm-config", response_model=LLMConfigResponse)
def llm_config_set(body: LLMConfigRequest, _auth: None = Depends(require_auth), db: Session = Depends(get_db)):
    return set_llm_config(
        db,
        base_url=body.base_url,
        api_key=body.api_key,
        model=body.model,
        timeout_seconds=body.timeout_seconds,
        enabled=body.enabled,
    )


@app.get("/tasks", response_model=list[TaskListItem])
def list_tasks(_auth: None = Depends(require_auth), db: Session = Depends(get_db)):
    tasks = db.scalars(select(Task).order_by(Task.created_at.desc())).all()
    return [
        TaskListItem(
            id=t.id,
            city=t.city,
            site=t.site,
            device_type=t.device_type,
            person=t.person,
            inventory_date=t.inventory_date,
            status=t.status,
            devices_count=len(t.devices),
        )
        for t in tasks
    ]


@app.get("/tasks/{task_id}", response_model=TaskDetailResponse)
def task_detail(task_id: int, _auth: None = Depends(require_auth), db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    images = db.scalars(select(ImageFile).where(ImageFile.task_id == task_id).order_by(ImageFile.created_at.desc())).all()
    records = db.scalars(select(DeviceRecord).where(DeviceRecord.task_id == task_id).order_by(DeviceRecord.created_at.desc())).all()

    return TaskDetailResponse(
        id=task.id,
        city=task.city,
        site=task.site,
        device_type=task.device_type,
        person=task.person,
        inventory_date=task.inventory_date,
        status=task.status,
        images=images,
        device_records=records,
    )


@app.delete("/tasks/{task_id}", response_model=MessageResponse)
def remove_task(task_id: int, _auth: None = Depends(require_auth), db: Session = Depends(get_db)):
    ok = delete_task(db, task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="任务不存在")
    return MessageResponse(message="任务已删除")


@app.get("/tasks/{task_id}/images", response_model=list[ImageFileOut])
def list_task_images(task_id: int, _auth: None = Depends(require_auth), db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return db.scalars(select(ImageFile).where(ImageFile.task_id == task_id).order_by(ImageFile.created_at.desc())).all()


@app.delete("/images/{image_id}", response_model=MessageResponse)
def remove_image(image_id: int, _auth: None = Depends(require_auth), db: Session = Depends(get_db)):
    ok = delete_image_file(db, image_id)
    if not ok:
        raise HTTPException(status_code=404, detail="图片不存在")
    return MessageResponse(message="图片已删除")


@app.patch("/device-records/{record_id}", response_model=MessageResponse)
def update_device_record(
    record_id: int,
    body: DeviceRecordUpdateRequest,
    _auth: None = Depends(require_auth),
    db: Session = Depends(get_db),
):
    record = db.get(DeviceRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="识别记录不存在")

    payload = body.model_dump(exclude_unset=True)
    for field, value in payload.items():
        setattr(record, field, value)

    db.add(record)
    db.commit()
    return MessageResponse(message="识别信息已更新")


@app.get("/summary/export")
def export_summary(_auth: None = Depends(require_auth), db: Session = Depends(get_db)):
    csv_text = export_summary_csv_text(db)
    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=summary.csv"},
    )


@app.get("/summary/export-xlsx")
def export_summary_xlsx(_auth: None = Depends(require_auth), db: Session = Depends(get_db)):
    data = export_summary_excel_bytes(db)
    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=summary.xlsx"},
    )


@app.get("/tasks/{task_id}/export-xlsx")
def export_task_xlsx(task_id: int, _auth: None = Depends(require_auth), db: Session = Depends(get_db)):
    try:
        data = export_task_detail_excel_bytes(db, task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=task_{task_id}.xlsx"},
    )


@app.get("/system/rule-config", response_model=RuleConfigResponse)
def rule_config_get(_auth: None = Depends(require_auth), db: Session = Depends(get_db)):
    return get_rule_config(db)


@app.post("/system/rule-config", response_model=RuleConfigResponse)
def rule_config_set(body: RuleConfigRequest, _auth: None = Depends(require_auth), db: Session = Depends(get_db)):
    return set_rule_config(db, min_confidence=body.min_confidence, require_serial_number=body.require_serial_number)


@app.post("/system/llm-test", response_model=MessageResponse)
def llm_test_api(body: LLMTestRequest, _auth: None = Depends(require_auth), db: Session = Depends(get_db)):
    result = llm_test(db, body.text)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return MessageResponse(message=result["message"])


@app.get("/logs", response_model=list[TaskLogItem])
def get_logs(
    limit: int = Query(default=200, ge=1, le=1000),
    _auth: None = Depends(require_auth),
    db: Session = Depends(get_db),
):
    return list_logs(db, limit=limit)
