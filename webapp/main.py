from pathlib import Path
import tempfile
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from .parser import parse_contract
from .generator import fill_canvas, safe_filename

BASE = Path(__file__).resolve().parent
app = FastAPI(title="WebBeds Canvas Generator")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate")
async def generate(
    file: UploadFile = File(...),
    address: str = Form(""),
    website: str = Form(""),
    latitude: str = Form(""),
    longitude: str = Form(""),
    city_override: str = Form(""),
    hotel_name_override: str = Form(""),
):
    if not file.filename.lower().endswith(".xlsx"):
        return JSONResponse({"error": "Lütfen .xlsx kontrat dosyası yükleyin."}, status_code=400)

    workdir = Path(tempfile.mkdtemp(prefix="webbeds_"))
    input_path = workdir / file.filename
    input_path.write_bytes(await file.read())

    try:
        contract = parse_contract(str(input_path))

        if hotel_name_override.strip():
            contract.hotel_name = hotel_name_override.strip()
        if city_override.strip():
            contract.city = city_override.strip()

        contract.address = address.strip()
        contract.website = website.strip()
        contract.latitude = latitude.strip()
        contract.longitude = longitude.strip()

        output_name = safe_filename(contract.hotel_name)
        output_path = workdir / output_name

        fill_canvas(contract, str(output_path))

        return FileResponse(
            path=output_path,
            filename=output_name,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)
