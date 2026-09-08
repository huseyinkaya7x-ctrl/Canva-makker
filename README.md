# WebBeds Canvas Generator

Hotel kontrat Excel dosyasını yükleyip WebBeds Hotel Canvas şablonunu otomatik dolduran web uygulaması.

## Uygulanan ana kurallar

- PP / P.P.P.D. odalarda `SINGLE ROOM` varsa Single ayrı oda oluşturulur.
- `DOUBLE ROOM + EXTRA BED` = 3 Adult olarak değerlendirilir.
- Canvas oda isimleri A:C birleşik kalır.
- Extra Bed (H) sütunu her zaman boş bırakılır.
- Currency A213 hücresine yazılır.
- Meal Plan / Board Type A218 hücresine yazılır.
- Child yaşları kontrattaki ondalık değer korunarak yazılır.
- Adult Only kontratlarda çocuk yaşları boş bırakılır ve Single/Double split uygulanmaz.
- Total-price family/suite odalarda yetişkin sayısına göre fiyat değişiyorsa fiyat grupları ayrı Canvas odalarına bölünür.
- Max Occupancy kontratta gerçekten görülen yetişkin + çocuk kombinasyonlarından hesaplanır.

## GitHub'a yükleme

Bu klasörün tamamını yeni bir GitHub repository'sine yükleyin.

## Lokal çalıştırma

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Mac/Linux:

```bash
source .venv/bin/activate
```

Ardından:

```bash
pip install -r requirements.txt
uvicorn webapp.main:app --reload
```

Tarayıcıdan:

`http://127.0.0.1:8000`

## Render ile yayınlama

1. GitHub repository'nizi Render hesabınıza bağlayın.
2. New > Blueprint seçin.
3. Repository'yi seçin.
4. `render.yaml` otomatik algılanır.
5. Deploy edin.

## Template

`templates/Webbeds_Hotel_Canvas.xlsx` uygulamanın sabit Canvas şablonudur.

Şablonu değiştirirseniz hücre adreslerini `app/generator.py` içinde kontrol edin.

## Not

Otel adresi, website, latitude ve longitude gibi kontratta bulunmayan genel bilgiler otomatik olarak internetten çekilmez.
Bu alanlar arayüzde opsiyonel olarak elle girilebilir.

Parser, şimdiye kadar kullanılan Sejour tarzı kontrat formatlarına göre hazırlanmıştır.
Farklı kolon veya satır düzenine sahip kontratlarda `app/parser.py` içindeki kurallar genişletilebilir.

## Vercel ile yayınlama

Bu sürüm Vercel'in zero-config FastAPI desteğine göre hazırlanmıştır. Repository root'unda `app.py` bulunur ve FastAPI uygulamasını `app` adıyla dışa aktarır.

Vercel'de özel Build Command veya Output Directory girmeyin. Root Directory, `app.py` dosyasının bulunduğu repository kökü olmalıdır.
