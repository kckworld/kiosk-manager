from typing import Any, Dict, List, Tuple
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from models import KioskLink, get_session

router = APIRouter(tags=["redirect"])


@router.get("/{slug}")
def redirect_slug(request: Request, slug: str, session: Session = Depends(get_session)) -> RedirectResponse:
    link = session.exec(select(KioskLink).where(KioskLink.slug == slug)).first()
    if not link:
        raise HTTPException(status_code=404, detail="Slug not found")

    album_ids = link.get_album_ids()
    options = link.get_options()

    params: List[Tuple[str, str]] = []
    params.extend(("album", album_id) for album_id in album_ids)
    params.extend((key, value) for key, value in options.items())

    base_url = request.app.state.settings.base_kiosk_url + "/"
    query = urlencode(params, doseq=True)
    destination = f"{base_url}?{query}" if query else base_url
    return RedirectResponse(url=destination, status_code=302)


@router.get("/debug/{slug}")
def debug_redirect(request: Request, slug: str, session: Session = Depends(get_session)) -> Dict[str, Any]:
    """디버깅용: 슬러그 리디렉션 정보 확인"""
    link = session.exec(select(KioskLink).where(KioskLink.slug == slug)).first()
    if not link:
        return {"error": f"Slug '{slug}' not found"}

    album_ids = link.get_album_ids()
    options = link.get_options()
    
    params: List[Tuple[str, str]] = []
    params.extend(("album", album_id) for album_id in album_ids)
    params.extend((key, value) for key, value in options.items())

    base_url = request.app.state.settings.base_kiosk_url + "/"
    query = urlencode(params, doseq=True)
    destination = f"{base_url}?{query}" if query else base_url

    return {
        "slug": slug,
        "label": link.label,
        "album_ids_raw": link.album_ids,
        "album_ids_parsed": album_ids,
        "options_raw": link.options,
        "options_parsed": options,
        "params": params,
        "query_string": query,
        "destination": destination
    }
