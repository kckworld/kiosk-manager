import asyncio
from typing import Any, Dict

import asyncpg
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


@router.get("/geocoding/status")
async def get_geocoding_status(request: Request) -> Dict[str, int]:
    settings = request.app.state.settings
    query = """
SELECT
  COUNT(*) FILTER (WHERE country = '대한민국') AS converted,
  COUNT(*) FILTER (WHERE country IS NULL OR country = 'South Korea' OR country = 'Korea') AS pending,
  COUNT(*) AS total
FROM asset_exif
WHERE latitude IS NOT NULL;
"""

    conn = None
    try:
        conn = await asyncpg.connect(
            host=settings.db_host,
            port=settings.db_port,
            database=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
            timeout=10,
        )
        row = await conn.fetchrow(query)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Failed to query geocoding status") from exc
    finally:
        if conn is not None:
            await conn.close()

    if row is None:
        return {"converted": 0, "pending": 0, "total": 0}

    return {
        "converted": int(row.get("converted") or 0),
        "pending": int(row.get("pending") or 0),
        "total": int(row.get("total") or 0),
    }


@router.post("/geocoding/run")
async def run_geocoding() -> Dict[str, Any]:
    command = (
        "docker compose -f /volume1/docker/immich/docker-compose.yml "
        "exec -T immich-naver-reverse-geocoding node updater.js"
    )

    try:
        await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to start geocoding job") from exc

    return {"ok": True, "message": "역지오코딩 시작됨"}


@router.post("/library/scan")
async def run_library_scan(request: Request) -> Dict[str, Any]:
    settings = request.app.state.settings
    if not settings.immich_api_key:
        raise HTTPException(status_code=500, detail="IMMICH_API_KEY is missing")

    headers = {"x-api-key": settings.immich_api_key}
    libraries_url = f"{settings.immich_url}/api/libraries"

    try:
        async with httpx.AsyncClient(timeout=20, verify=False) as client:
            libraries_response = await client.get(libraries_url, headers=headers)
            libraries_response.raise_for_status()

            libraries_data = libraries_response.json()
            if not isinstance(libraries_data, list) or not libraries_data:
                raise HTTPException(status_code=404, detail="No libraries found")

            first_library = libraries_data[0]
            if not isinstance(first_library, dict) or not first_library.get("id"):
                raise HTTPException(status_code=502, detail="Invalid library response from Immich")

            library_id = str(first_library["id"])
            scan_url = f"{settings.immich_url}/api/libraries/{library_id}/scan"
            scan_response = await client.post(scan_url, headers=headers, json={})
            scan_response.raise_for_status()
    except HTTPException:
        raise
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

    return {"ok": True, "message": "외부 라이브러리 재탐색 시작됨"}

