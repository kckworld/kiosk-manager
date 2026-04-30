from typing import Any, Dict

import httpx
from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/albums")
async def get_albums(request: Request) -> Dict[str, Any]:
    settings = request.app.state.settings
    if not settings.immich_api_key:
        raise HTTPException(status_code=500, detail="IMMICH_API_KEY is missing")

    url = f"{settings.immich_url}/api/albums"
    headers = {"x-api-key": settings.immich_api_key}

    try:
        async with httpx.AsyncClient(timeout=15, verify=False) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        error_msg = f"Immich API error {exc.response.status_code}"
        try:
            error_detail = exc.response.json()
            error_msg += f": {error_detail}"
        except Exception:
            error_msg += f": {exc.response.text[:200]}"
        raise HTTPException(status_code=502, detail=error_msg) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Failed to connect to Immich: {str(exc)[:200]}") from exc

    data = response.json()
    albums = []

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                albums.append(
                    {
                        "id": item.get("id"),
                        "albumName": item.get("albumName") or item.get("name") or "(Unnamed)",
                        "assetCount": item.get("assetCount", 0),
                    }
                )

    albums.sort(key=lambda album: str(album.get("albumName") or "").casefold())

    return {"albums": albums}


@router.get("/debug/albums-raw")
async def debug_albums_raw(request: Request) -> Dict[str, Any]:
    """디버깅용: Immich API 응답 원본"""
    settings = request.app.state.settings
    if not settings.immich_api_key:
        return {"error": "IMMICH_API_KEY missing", "settings": {
            "immich_url": settings.immich_url,
            "immich_api_key": "***"
        }}

    url = f"{settings.immich_url}/api/albums"
    headers = {"x-api-key": settings.immich_api_key}

    try:
        async with httpx.AsyncClient(timeout=15, verify=False) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return {
                "status": response.status_code,
                "url": url,
                "data": response.json()
            }
    except Exception as exc:
        return {
            "error": str(exc),
            "url": url,
            "settings": {
                "immich_url": settings.immich_url,
                "immich_api_key": "***"
            }
        }

