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

@app.route('/location_info')
def map_view():
    # 기준 지점 A (위도, 경도, 고도)
    point_a = {"name": "A 지점", "lat": 37.5665, "lon": 126.9780, "altitude": 50.0}
    
    # 대상 지점 B (위도, 경도, 고도)
    # 아래 좌표와 고도는 A 지점으로부터 약 100m 거리에 위치한 가상의 B 지점입니다.
    point_b = {"name": "B 지점", "lat": 37.566589, "lon": 126.979116, "altitude": 65.0}

    # Haversine 공식을 사용한 A, B 지점 간 평면 거리 계산 (미터 단위)
    # haversine 패키지는 km단위를 기본으로 반환하므로 1000을 곱해 미터(m)로 변환
    distance_2d = haversine((point_a['lat'], point_a['lon']), (point_b['lat'], point_b['lon'])) * 1000

    # 3D 실제 거리를 구하기 위해 피타고라스 정리 적용 ($c = \sqrt{a^2 + b^2}$)
    # $a = 2D 수평 거리$, $b = 고도 차이$
    alt_diff = abs(point_a['altitude'] - point_b['altitude'])
    distance_3d = (distance_2d**2 + alt_diff**2)**0.5

    return render_template('location_info.html', 
                           a=point_a, 
                           b=point_b, 
                           distance_2d=distance_2d,
                           distance_3d=distance_3d,
                           alt_diff=alt_diff)
