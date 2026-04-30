from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Generator, List, Optional

from dotenv import load_dotenv
from sqlmodel import Field, Session, SQLModel, create_engine

load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.immich_url = os.getenv("IMMICH_URL", "https://your-immich-url.com").rstrip("/")
        self.immich_api_key = os.getenv("IMMICH_API_KEY", "")
        self.base_kiosk_url = os.getenv("BASE_KIOSK_URL", "https://your-kiosk-url.com").rstrip("/")
        self.base_short_url = os.getenv("BASE_SHORT_URL", "https://your-short-url.com").rstrip("/")
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./data/kiosk_links.db")


settings = Settings()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class KioskLink(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(index=True, unique=True, max_length=100)
    label: str = Field(max_length=255)
    album_ids: str = Field(default="[]")
    options: str = Field(default="{}")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def get_album_ids(self) -> List[str]:
        try:
            value = json.loads(self.album_ids)
            if isinstance(value, list):
                return [str(v) for v in value if str(v).strip()]
        except json.JSONDecodeError:
            pass
        return []

    def get_options(self) -> Dict[str, str]:
        try:
            value = json.loads(self.options)
            if isinstance(value, dict):
                return {str(k): str(v) for k, v in value.items() if str(k).strip() and str(v).strip()}
        except json.JSONDecodeError:
            pass
        return {}

    def set_album_ids(self, album_ids: List[str]) -> None:
        self.album_ids = json.dumps([v for v in album_ids if v], ensure_ascii=True)

    def set_options(self, options: Dict[str, str]) -> None:
        self.options = json.dumps(options, ensure_ascii=True)


def _ensure_sqlite_parent_dir(database_url: str) -> None:
    if not database_url.startswith("sqlite:///"):
        return
    path_str = database_url[len("sqlite:///"):]
    if path_str == ":memory:":
        return
    db_path = Path(path_str)
    if not db_path.is_absolute():
        db_path = (Path.cwd() / db_path).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_parent_dir(settings.database_url)

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
