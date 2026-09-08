from pathlib import Path
import tempfile
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from .parser import parse_contract
from .generator import fill_canvas, safe_filename

app = FastAPI(title="WebBeds Canvas Generator")

HTML = r'''<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>WebBeds Canvas Generator</title>
<style>
:root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#17202a;background:#f3f6f8}*{box-sizing:border-box}body{margin:0}.container{min-height:100vh;display:grid;place-items:center;padding:32px 18px}.card{width:min(860px,100%);background:#fff;border-radius:24px;padding:34px;box-shadow:0 20px 60px rgba(0,0,0,.08)}.badge{display:inline-block;font-size:12px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;background:#eef2f4;padding:7px 10px;border-radius:999px}h1{margin:14px 0 8px;font-size:clamp(30px,5vw,48px)}.lead{margin:0 0 28px;color:#5c6770}.upload{display:block;padding:20px;border:2px dashed #ccd5db;border-radius:16px;margin-bottom:20px}.upload span{display:block;font-weight:700;margin-bottom:10px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}label{font-size:14px;font-weight:650}input[type=text],input[type=file]{width:100%;margin-top:7px}input[type=text]{border:1px solid #d8dfe4;border-radius:10px;padding:12px 13px;outline:none}.wide{grid-column:1/-1}button{margin-top:24px;border:0;border-radius:12px;padding:14px 20px;font-weight:800;cursor:pointer;background:#17202a;color:#fff}button:disabled{opacity:.55;cursor:wait}#status{margin-top:14px;min-height:22px;color:#53606a}@media(max-width:640px){.card{padding:24px}.grid{grid-template-columns:1fr}.wide{grid-column:auto}}
</style></head><body><main class="container"><section class="card"><div class="badge">WebBeds</div><h1>Hotel Canvas Generator</h1><p class="lead">Sejour tarzı otel kontratını yükle, WebBeds Canvas dosyasını otomatik oluştur.</p>
<form id="form" action="/api/generate" method="post" enctype="multipart/form-data"><label class="upload"><span>Kontrat Excel Dosyası</span><input type="file" name="file" accept=".xlsx" required></label><div class="grid"><label>Otel adı (opsiyonel)<input type="text" name="hotel_name_override" placeholder="Kontrattan otomatik okunur"></label><label>Şehir (opsiyonel)<input type="text" name="city_override" placeholder="Örn. Fethiye"></label><label class="wide">Adres (opsiyonel)<input type="text" name="address"></label><label class="wide">Hotel Website (opsiyonel)<input type="text" name="website"></label><label>Latitude (opsiyonel)<input type="text" name="latitude"></label><label>Longitude (opsiyonel)<input type="text" name="longitude"></label></div><button id="submit" type="submit">Canvas Oluştur</button><div id="status"></div></form></section></main>
<script>const form=document.getElementById('form'),status=document.getElementById('status'),submit=document.getElementById('submit');form.addEventListener('submit',async e=>{e.preventDefault();status.textContent='Canvas hazırlanıyor...';submit.disabled=true;try{const response=await fetch('/api/generate',{method:'POST',body:new FormData(form)});if(!response.ok){const err=await response.json().catch(()=>({error:'Bilinmeyen hata'}));throw new Error(err.error||'İşlem başarısız')}const blob=await response.blob(),d=response.headers.get('content-disposition')||'',m=d.match(/filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i),filename=decodeURIComponent((m&&(m[1]||m[2]))||'Hotel_Canva.xlsx'),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=filename;document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url);status.textContent='Canvas hazır.'}catch(err){status.textContent='Hata: '+err.message}finally{submit.disabled=false}});</script></body></html>'''

@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(HTML)

@app.get("/api/health")
def health():
    return {"ok": True, "service": "webbeds-canvas-generator", "version": "v3"}

@app.post("/generate")
@app.post("/api/generate")
async def generate(
    file: UploadFile = File(...),
    address: str = Form(""),
    website: str = Form(""),
    latitude: str = Form(""),
    longitude: str = Form(""),
    city_override: str = Form(""),
    hotel_name_override: str = Form(""),
):
    filename = file.filename or ""
    if not filename.lower().endswith(".xlsx"):
        return JSONResponse({"error": "Lütfen .xlsx kontrat dosyası yükleyin."}, status_code=400)

    workdir = Path(tempfile.mkdtemp(prefix="webbeds_", dir="/tmp"))
    input_path = workdir / Path(filename).name
    try:
        input_path.write_bytes(await file.read())
        contract = parse_contract(str(input_path))
        if hotel_name_override.strip(): contract.hotel_name = hotel_name_override.strip()
        if city_override.strip(): contract.city = city_override.strip()
        contract.address = address.strip()
        contract.website = website.strip()
        contract.latitude = latitude.strip()
        contract.longitude = longitude.strip()
        output_name = safe_filename(contract.hotel_name)
        output_path = workdir / output_name
        fill_canvas(contract, str(output_path))
        return FileResponse(path=str(output_path), filename=output_name, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as exc:
        return JSONResponse({"error": f"{type(exc).__name__}: {exc}"}, status_code=500)
