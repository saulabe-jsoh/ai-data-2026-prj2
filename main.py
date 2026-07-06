from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "message": "Hello, FastAPI + Jinja2!"})


@app.get("/hello/{name}", response_class=HTMLResponse)
async def hello(request: Request, name: str):
    return templates.TemplateResponse("index.html", {"request": request, "message": f"안녕하세요, {name}님!"})
