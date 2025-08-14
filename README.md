## Building Detection Backend Service

Layanan backend FastAPI untuk deteksi bangunan menggunakan YOLOv8. Server menerima area poligon (GeoJSON), melakukan tiling, deteksi per tile, melakukan penggabungan (merging), dan mengembalikan daftar titik centroid bangunan sederhana dalam JSON.

Catatan penting: saat ini kode mengambil tile peta OSM standar (bukan citra satelit). Model yang dilatih pada citra satelit bisa berkinerja buruk pada peta OSM. Untuk hasil akurat, gunakan penyedia citra satelit (lihat bagian Sumber Citra & Rekomendasi).

### Ringkas (English)
FastAPI backend for building detection with YOLOv8. Accepts polygon GeoJSON and returns building centroid points. Current tiles are OSM map tiles (not satellite). For accurate results, switch to a satellite imagery provider.

### Fitur Utama
- FastAPI + OpenAPI docs
- Mode sinkron dan asinkron (job queue in-memory)
- Penggabungan deteksi lintas-tile (Union-Find, IoU, boundary-aware)
- Output sederhana: `[ { id, longitude, latitude } ]`
- Konfigurasi lewat environment variables

---

## Struktur Proyek (ringkas)
```
building-detector/
├─ run_server.py            # Entrypoint server (uvicorn)
├─ main_app.py              # FastAPI app (routers, deps, lifespan)
├─ api/                     # Layer API: routers, models, services
├─ src/                     # Pipeline deteksi (tiling, YOLO, merging)
├─ examples/                # Contoh GeoJSON
├─ output/                  # Hasil deteksi
└─ requirements.txt         # Dependensi Python (pinned)
```

---

## Persyaratan Sistem
- Python 3.12 (lihat `Dockerfile` untuk container image)
- Model YOLOv8 file `best.pt` tersedia pada `MODEL_PATH`
- Opsional: GPU (CUDA) untuk performa lebih cepat

---

## Instalasi (Lokal)
```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt


```

---

## Konfigurasi
Semua konfigurasi dikelola via `api/config.py` (Pydantic Settings) dan `.env`.

Variabel utama:
- `HOST` (default: `0.0.0.0`)
- `PORT` (default: `5050`)
- `RELOAD` (default: `true` untuk dev)
- `LOG_LEVEL` (default: `info`)
- `MODEL_PATH` (default: `best.pt`)
- `MAX_CONCURRENT_JOBS` (default: `2`)


Contoh `.env`:
```bash
HOST=0.0.0.0
PORT=5050
RELOAD=false
LOG_LEVEL=info
MODEL_PATH=best.pt
MAX_CONCURRENT_JOBS=2
```

---

## Menjalankan Server API
```bash
python run_server.py
```

Server menggunakan base path `/ai` (lihat `main_app.py`).

- Docs: `http://localhost:5050/ai/docs`
- Health: `http://localhost:5050/ai/health`

Jika ingin URL tanpa prefix, hapus `root_path="/ai"` di `main_app.py` dan sesuaikan dokumentasi ini.

---

## Referensi API

Semua path di bawah diasumsikan dengan base path `/ai`.

### Kesehatan
- `GET /health`
  - Cek status server dan apakah model termuat
  - Respon:
  ```json
  { "status": "healthy", "model_loaded": true, "timestamp": "2024-01-01T12:00:00" }
  ```

### Informasi Model
- `GET /model/info`
  - 503 jika model belum termuat
  - Respon contoh:
  ```json
  { "model_loaded": true, "model_type": "YOLOv8", "model_file": "best.pt" }
  ```

### Deteksi Sinkron
- `POST /detect/sync`
  - Body (contoh):
  ```json
  {
    "polygon": {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[106.84, -6.21], [106.85, -6.21], [106.85, -6.20], [106.84, -6.20], [106.84, -6.21]]]
      },
      "properties": {}
    },
    "zoom": 18,
    "confidence": 0.25,
    "batch_size": 5,
    "enable_merging": true,
    "merge_iou_threshold": 0.1,
    "merge_touch_enabled": true,
    "merge_min_edge_distance_deg": 0.00001
  }
  ```
  - Respon (contoh):
  ```json
  {
    "success": true,
    "message": "Building detection completed successfully",
    "buildings": [ { "id": "1", "longitude": 106.8456, "latitude": -6.2088 } ],
    "total_buildings": 1,
    "execution_time": 12.3
  }
  ```

Curl contoh:
```bash
curl -X POST http://localhost:5050/ai/detect/sync \
  -H "Content-Type: application/json" \
  -d @examples/sample_polygon.geojson
```

### Deteksi Asinkron (Job)
- `POST /detect/async` → submit job
  - Body sama seperti sinkron, opsional `job_id`
  - Respon:
  ```json
  { "job_id": "<id>", "status": "queued", "message": "Detection job submitted successfully.", "submitted_at": "..." }
  ```
- `GET /job/{job_id}` → status job
- `GET /job/{job_id}/result` → hasil akhir (202 jika belum selesai)
- `DELETE /job/{job_id}` → batalkan job
- `GET /jobs` → daftar semua job (debug)

### Validasi Input
- `job_id`: 3–50 karakter, alfanumerik, `-`/`_`, tidak boleh diawali/diakhiri simbol
- GeoJSON: harus `Polygon`/`MultiPolygon` yang valid

---

## Menjalankan CLI (opsional/legacy)

### Tanpa Docker (Lokal)
1) Pastikan dependensi terpasang dan file model tersedia (default `best.pt` di root, atau set `--model`).
2) Jalankan perintah berikut:
```bash
python main.py examples/sample_polygon.geojson \
  --output output/ \
  --zoom 18 \
  --conf 0.25 \
  --batch-size 5
```
3) Hasil utama tersedia di `output/buildings_simple.json`.
4) (Opsional) Validasi pada peta: `python src/validation/validate.py` → menghasilkan `building_validation_map.html`.

Catatan: Anda dapat mengganti `--model best.pt` dengan path lain jika model tidak berada di root.

### Dengan Docker
Pastikan image sudah dibangun:
```bash
docker build -t building-detector:latest .
```

- Menggunakan contoh GeoJSON yang sudah ada di image:
```bash
docker run --rm \
  -v $(pwd)/best.pt:/app/best.pt \
  -v $(pwd)/output:/app/output \
  building-detector:latest \
  python main.py examples/sample_polygon.geojson \
    --output output \
    --zoom 18 \
    --conf 0.25 \
    --batch-size 5
```

- Menggunakan GeoJSON dari host:
```bash
docker run --rm \
  -v $(pwd)/best.pt:/app/best.pt \
  -v $(pwd)/my_area.geojson:/app/examples/my_area.geojson \
  -v $(pwd)/output:/app/output \
  building-detector:latest \
  python main.py examples/my_area.geojson \
    --output output \
    --zoom 18 \
    --conf 0.25 \
    --batch-size 5
```

Keterangan:
- `-v $(pwd)/best.pt:/app/best.pt`: memasang file model ke dalam container.
- `-v $(pwd)/output:/app/output`: hasil deteksi akan tersedia di folder host `./output`.
- Untuk file GeoJSON kustom, mount ke path di dalam container lalu rujuk path tersebut saat menjalankan `main.py`.

---

## Cara Kerja Pipeline (Ringkas)
1) Load poligon → hitung tile yang beririsan (mercantile)
2) Unduh gambar tile → inferensi YOLO per tile
3) Simpan hasil per tile (detail & simple) → gabung (merging) lintas tile
4) Filter bangunan (centroid) yang benar-benar berada di dalam poligon input → tulis `buildings_simple.json`

Penggabungan memakai Union-Find multi-fase (IoU, proximity/touching dekat boundary, axis alignment) untuk mengurangi duplikasi lintas tile.

---

## Sumber Citra & Rekomendasi
Saat ini fungsi `get_tile_image` di `src/core/tile_utils.py` memakai:
```text
https://tile.openstreetmap.org/{z}/{x}/{y}.png
```
Ini adalah peta OSM standar (bukan citra satelit). Jika model Anda dilatih pada citra satelit/udara, gunakan penyedia citra satelit (mis. Mapbox Satellite, WMTS/WMS lain) dan sesuaikan `get_tile_image` untuk memanggil provider tersebut (biasanya butuh API key dan kepatuhan T&C). Pertimbangkan caching lokal dan rate limiting.

---

## Tuning Performa
- `zoom` (default 18): lebih tinggi = lebih banyak tile, lebih detail, lebih lambat
- `batch_size` (default 5): jumlah tile per batch; I/O dan memori terpengaruh
- `MAX_CONCURRENT_JOBS`: batasi beban asinkron
- GPU inference: percepat inferensi YOLO
- Hindari menyimpan image tile dalam memori jika tidak diperlukan (opsional optimisasi lanjutan)

---

## Keamanan & Operasional
- CORS diaktifkan luas (origins `*` dan credentials `true`) → sesuaikan untuk produksi
- Rate limiting & auth belum tersedia → rekomendasi pakai reverse proxy (Nginx/Traefik)
- Logging masih `print` → rekomendasi gunakan `logging` dengan format terstruktur
- Job persistence in-memory → tambahkan pembersihan berkala sesuai `job_cleanup_interval_hours`

---

## Validasi Hasil pada Peta (Folium)
Setelah deteksi sinkron, jalankan:
```bash
python src/validation/validate.py
```
Menghasilkan `building_validation_map.html` yang menampilkan titik centroid dari `output/buildings_simple.json`.

---

## Deployment dengan Docker
```bash
docker build -t building-detector:latest .
docker run --rm -p 5050:5050 \
  -e HOST=0.0.0.0 -e PORT=5050 -e RELOAD=false -e LOG_LEVEL=info \
  -v $(pwd)/best.pt:/app/best.pt \
  building-detector:latest
```
Lalu akses `http://localhost:5050/ai/docs`.

---

## Troubleshooting
- 503 Model Not Loaded: pastikan `MODEL_PATH` menunjuk file `.pt` yang ada
- 404 pada `/docs`/`/health`: ingat base path `/ai` (gunakan `/ai/docs`, `/ai/health`)
- 429 Server at Capacity: kurangi concurrent jobs atau naikkan `MAX_CONCURRENT_JOBS`
- 400 Invalid GeoJSON: perbaiki struktur poligon
- Hasil kosong: ingat OSM tiles bukan citra satelit; ganti sumber citra

---

## Kontribusi & Lisensi
- Pull request dan isu dipersilakan.
- Lisensi: MIT (jika tidak ada, tambahkan file LICENSE sesuai kebutuhan).

---

## Dokumentasi Lebih Lanjut
- Ikhtisar: `docs/overview.md`
- Arsitektur: `docs/architecture.md`
- Referensi API: `docs/api_reference.md`
- Konfigurasi: `docs/configuration.md`
- Pipeline Deteksi: `docs/pipeline.md`
- Deployment: `docs/deployment.md`
- Troubleshooting: `docs/troubleshooting.md`
- Sumber Citra: `docs/imagery.md`

