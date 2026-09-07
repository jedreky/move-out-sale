import secrets
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request, UploadFile, File, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.db_utils import get_connection

USERNAME = "USERNAME"
PASSWORD = "PASSWORD"

RAW_FOLDER = Path("data/raw")
PROCESSED_FOLDER = Path("data/processed")

RAW_FOLDER.mkdir(parents=True, exist_ok=True)
PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)


app = FastAPI()
app.mount("/processed", StaticFiles(directory=PROCESSED_FOLDER), name="processed")
templates = Jinja2Templates(directory="templates")
security = HTTPBasic()


executor = ProcessPoolExecutor(max_workers=1)


def convert_to_jpg(src: str, dst_folder: str):
    print(f"[convert] starting: {src}")
    try:
        from PIL import Image
        from pillow_heif import register_heif_opener
        register_heif_opener()
        src_path = Path(src)
        dst = Path(dst_folder) / (src_path.stem + ".jpg")
        with Image.open(src_path) as img:
            max_dim = max(img.width, img.height)
            if max_dim > 1024:
                scale = 1024 / max_dim
                new_size = (int(img.width * scale), int(img.height * scale))
                img = img.resize(new_size, Image.LANCZOS)
            img.convert("RGB").save(dst, "JPEG")
        print(f"[convert] done: {dst}")
    except Exception as e:
        print(f"[convert] error: {e}")


def require_auth(creds: HTTPBasicCredentials = Depends(security)):
    valid_username = secrets.compare_digest(creds.username, USERNAME)
    valid_password = secrets.compare_digest(creds.password, PASSWORD)
    if not (valid_username and valid_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, headers={"WWW-Authenticate": "Basic"})


def build_content(min_priority: int | None = None, max_priority: int | None = None):
    with get_connection() as conn:
        if min_priority is not None:
            items = conn.execute("SELECT id, desc, price, available_on FROM items WHERE status = 'available' AND priority >= ? ORDER BY priority DESC, id DESC", (min_priority,)).fetchall()
        elif max_priority is not None:
            items = conn.execute("SELECT id, desc, price, available_on FROM items WHERE status = 'available' AND priority <= ? ORDER BY priority DESC, id DESC", (max_priority,)).fetchall()
        else:
            items = conn.execute("SELECT id, desc, price, available_on FROM items WHERE status = 'available' ORDER BY priority DESC, id DESC").fetchall()
    headers = ["Photos", "Details"]
    header = "<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>"
    rows = []
    for item_id, desc, price, available_on in items:
        with get_connection() as conn:
            pics = conn.execute("SELECT path FROM pictures WHERE item_id = ?", (item_id,)).fetchall()
        imgs = "".join(f'<img src="/processed/{p[0]}">' for p in pics)
        today = datetime.now().date().isoformat()
        pickup = "ready to pick-up" if available_on <= today else f"pick-up: {available_on}"
        price_str = f"{price} AED<br><br>" if price else ""
        details = f"{desc}<br><br>{price_str}{pickup}"
        rows.append(f'<tr><td style="padding:0;">{imgs}</td><td>{details}</td></tr>')
    return f'<table style="width:100%;table-layout:fixed;"><colgroup><col style="width:40%;"><col></colgroup><thead>{header}</thead><tbody>{"".join(rows)}</tbody></table>'


@app.get("/", response_class=HTMLResponse)
def main(request: Request):
    return templates.TemplateResponse(request, "main.html", {"content": build_content(max_priority=5), "phone_wa": "971123456789", "phone_display": "+971 123 456 789"})





_INPUT = "background:#2a2a2a;color:#e0e0e0;border:1px solid #555;padding:0.5rem;border-radius:4px;font-size:0.9rem;width:100%;"
_LABEL = "display:block;color:#bbb;font-size:0.8rem;margin-bottom:0.25rem;"
_BTN   = "background:#444;color:#e0e0e0;border:1px solid #555;padding:0.5rem 1.5rem;border-radius:4px;cursor:pointer;font-size:0.9rem;"


def build_edit_content():
    add_form = (
        '<h2 style="color:#e0e0e0;">Add new item</h2>'
        '<form method="post" enctype="multipart/form-data"'
        ' style="display:flex;flex-direction:column;gap:1rem;max-width:480px;">'

        f'<div><label style="{_LABEL}">Pictures</label>'
        '<label style="background:#333;color:#ccc;border:1px solid #555;padding:0.5rem 1rem;'
        'border-radius:4px;cursor:pointer;font-size:0.9rem;display:inline-block;">'
        'Choose files'
        '<input type="file" name="files" multiple accept="image/*" style="display:none;">'
        "</label></div>"

        f'<div><label style="{_LABEL}">Description</label>'
        f'<textarea name="desc" rows="3" required style="{_INPUT}resize:vertical;"></textarea></div>'

        f'<div><label style="{_LABEL}">Price (AED)</label>'
        f'<input type="number" name="price" min="0" required style="{_INPUT}"></div>'

        f'<div><label style="{_LABEL}">Available from</label>'
        f'<input type="date" name="available_on" required style="{_INPUT}"></div>'

        f'<div><label style="{_LABEL}">Priority</label>'
        f'<select name="priority" style="{_INPUT}">'
        + "".join(f'<option value="{i}">{i}</option>' for i in range(8))
        + '</select></div>'

        f'<div><button type="submit" style="{_BTN}">Add item</button></div>'
        "</form>"
    )

    with get_connection() as conn:
        items = conn.execute("SELECT id, desc, status FROM items ORDER BY id DESC").fetchall()

    rows = []
    for item_id, desc, item_status in items:
        toggle = "sold" if item_status == "available" else "available"
        badge_color = "#2e7d32" if item_status == "available" else "#7f0000"
        badge = f'<span style="background:{badge_color};color:#e0e0e0;padding:0.2rem 0.6rem;border-radius:4px;font-size:0.8rem;">{item_status}</span>'
        btn = (
            f'<form method="post" action="/edit_d4g21e/item/{item_id}/status" style="display:inline;">'
            f'<input type="hidden" name="new_status" value="{toggle}">'
            f'<button type="submit" style="{_BTN}font-size:0.8rem;padding:0.3rem 0.8rem;">Mark as {toggle}</button>'
            '</form>'
        )
        rows.append(
            f'<tr><td style="color:#e0e0e0;padding:0.5rem;">{desc}</td>'
            f'<td style="padding:0.5rem;">{badge}</td>'
            f'<td style="padding:0.5rem;">{btn}</td></tr>'
        )

    table = (
        '<h2 style="color:#e0e0e0;margin-top:2rem;">Existing items</h2>'
        '<table style="width:100%;max-width:720px;border-collapse:collapse;">'
        '<thead><tr>'
        '<th style="color:#bbb;text-align:left;padding:0.5rem;border-bottom:1px solid #444;">Description</th>'
        '<th style="color:#bbb;text-align:left;padding:0.5rem;border-bottom:1px solid #444;">Status</th>'
        '<th style="color:#bbb;text-align:left;padding:0.5rem;border-bottom:1px solid #444;"></th>'
        '</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody>'
        '</table>'
    )

    return add_form + table


@app.get("/edit_d4g21e", response_class=HTMLResponse)
def edit_get(request: Request, _: None = Depends(require_auth)):
    return templates.TemplateResponse(request, "main.html", {"content": build_edit_content(), "phone_wa": "971123456789", "phone_display": "+971 123 456 789"})


@app.post("/edit_d4g21e", response_class=HTMLResponse)
async def edit_post(
    request: Request,
    files: list[UploadFile] = File(...),
    desc: str = Form(...),
    price: int = Form(...),
    available_on: str = Form(...),
    priority: int = Form(0),
    _: None = Depends(require_auth),
):
    saved = []

    for file in files:
        ext = Path(file.filename).suffix.lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hex_suffix = secrets.token_hex(3)
        dst = RAW_FOLDER / f"{timestamp}_{hex_suffix}{ext}"
        dst.write_bytes(await file.read())
        print(f"[upload] saved to raw: {dst}")
        saved.append(dst)

    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO items (desc, price, available_on, priority) VALUES (?, ?, ?, ?)",
            (desc, price, available_on, priority),
        )
        item_id = cursor.lastrowid
        for dst in saved:
            jpg_name = dst.stem + ".jpg"
            conn.execute("INSERT INTO pictures (path, item_id) VALUES (?, ?)", (jpg_name, item_id))

    for dst in saved:
        executor.submit(convert_to_jpg, str(dst), str(PROCESSED_FOLDER))

    return RedirectResponse("/edit_d4g21e", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/edit_d4g21e/item/{item_id}/status")
async def edit_item_status(
    item_id: int,
    new_status: str = Form(...),
    _: None = Depends(require_auth),
):
    if new_status not in ("available", "sold"):
        raise HTTPException(status_code=400, detail="Invalid status")
    with get_connection() as conn:
        conn.execute("UPDATE items SET status = ? WHERE id = ?", (new_status, item_id))
    return RedirectResponse("/edit_d4g21e", status_code=status.HTTP_303_SEE_OTHER)
