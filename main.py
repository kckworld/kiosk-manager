from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from models import create_db_and_tables, settings
from routers import admin, api, redirect

app = FastAPI(title="Kiosk URL Manager")
app.state.templates = Jinja2Templates(directory="templates")
app.state.settings = settings
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()


app.include_router(admin.router)
app.include_router(api.router)
app.include_router(redirect.router)
