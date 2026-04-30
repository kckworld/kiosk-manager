import re
from datetime import datetime, timezone
from typing import Dict, List

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select

from models import KioskLink, get_session

router = APIRouter(prefix="/admin", tags=["admin"])
SLUG_PATTERN = re.compile(r"^[a-z0-9-]+$")


def _parse_options(keys: List[str], values: List[str]) -> Dict[str, str]:
    options: Dict[str, str] = {}
    for key, value in zip(keys, values):
        clean_key = key.strip()
        clean_value = value.strip()
        if clean_key and clean_value:
            options[clean_key] = clean_value
    return options


def _validate_slug(slug: str) -> str:
    value = slug.strip().lower()
    if not value:
        raise HTTPException(status_code=422, detail="Slug is required")
    if not SLUG_PATTERN.fullmatch(value):
        raise HTTPException(status_code=422, detail="Slug must contain only lowercase letters, numbers, and hyphens")
    return value


@router.get("", response_class=HTMLResponse)
def admin_index(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    templates = request.app.state.templates
    settings = request.app.state.settings
    links = session.exec(select(KioskLink).order_by(KioskLink.id.desc())).all()

    return templates.TemplateResponse(
        "admin/index.html",
        {
            "request": request,
            "links": links,
            "base_kiosk_url": settings.base_kiosk_url,
            "short_base_url": settings.base_short_url,
        },
    )


@router.get("/new", response_class=HTMLResponse)
def admin_new(request: Request) -> HTMLResponse:
    templates = request.app.state.templates
    settings = request.app.state.settings
    return templates.TemplateResponse(
        "admin/form.html",
        {
            "request": request,
            "title": "새 링크 생성",
            "action_url": "/admin/links",
            "method": "POST",
            "link": None,
            "selected_album_ids": [],
            "options": {},
            "base_kiosk_url": settings.base_kiosk_url,
            "is_edit": False,
        },
    )


@router.post("/links")
def create_link(
    slug: str = Form(...),
    label: str = Form(...),
    album_ids: List[str] = Form(default=[]),
    option_keys: List[str] = Form(default=[]),
    option_values: List[str] = Form(default=[]),
    session: Session = Depends(get_session),
) -> RedirectResponse:
    clean_slug = _validate_slug(slug)
    if session.exec(select(KioskLink).where(KioskLink.slug == clean_slug)).first():
        raise HTTPException(status_code=409, detail="Slug already exists")

    link = KioskLink(slug=clean_slug, label=label.strip())
    link.set_album_ids(album_ids)
    link.set_options(_parse_options(option_keys, option_values))

    session.add(link)
    session.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/links/{id}/edit", response_class=HTMLResponse)
def admin_edit(id: int, request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    templates = request.app.state.templates
    settings = request.app.state.settings

    link = session.get(KioskLink, id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    return templates.TemplateResponse(
        "admin/form.html",
        {
            "request": request,
            "title": "링크 수정",
            "action_url": f"/admin/links/{id}",
            "method": "PUT",
            "link": link,
            "selected_album_ids": link.get_album_ids(),
            "options": link.get_options(),
            "base_kiosk_url": settings.base_kiosk_url,
            "is_edit": True,
        },
    )


@router.put("/links/{id}")
def update_link(
    id: int,
    slug: str = Form(...),
    label: str = Form(...),
    album_ids: List[str] = Form(default=[]),
    option_keys: List[str] = Form(default=[]),
    option_values: List[str] = Form(default=[]),
    session: Session = Depends(get_session),
) -> RedirectResponse:
    link = session.get(KioskLink, id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    clean_slug = _validate_slug(slug)
    duplicate = session.exec(select(KioskLink).where(KioskLink.slug == clean_slug, KioskLink.id != id)).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="Slug already exists")

    link.slug = clean_slug
    link.label = label.strip()
    link.set_album_ids(album_ids)
    link.set_options(_parse_options(option_keys, option_values))
    link.updated_at = datetime.now(timezone.utc)

    session.add(link)
    session.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)


@router.delete("/links/{id}")
def delete_link(id: int, session: Session = Depends(get_session)) -> Dict[str, bool]:
    link = session.get(KioskLink, id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    session.delete(link)
    session.commit()
    return {"ok": True}
