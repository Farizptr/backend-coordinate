import requests
import time
import json

# --- Konfigurasi untuk Service A ---
# Ini adalah URL tempat Service B (API deteksi Anda) berjalan.
# Saat menjalankan secara lokal, ini adalah alamat yang benar.
# Jika Service B berjalan di tempat lain, ganti URL ini.
SERVICE_B_BASE_URL = "http://localhost:5050"

# --- Data yang akan dikirim oleh Service A ---
# Service A harus membuat ID unik untuk setiap pekerjaan agar bisa dilacak.
# Ini bisa berupa UUID, ID dari database Service A, dll.
JOB_ID = f"job-from-service-a-{int(time.time())}"

# Contoh polygon GeoJSON (misalnya, area di sekitar Monas, Jakarta)
POLYGON_GEOJSON = {
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [106.826, -6.174],
        [106.828, -6.174],
        [106.828, -6.176],
        [106.826, -6.176],
        [106.826, -6.174]
      ]
    ]
  },
  "properties": {}
}

def submit_detection_job():
    """
    Langkah 1: Mengirimkan pekerjaan deteksi ke Service B.
    """
    submit_url = f"{SERVICE_B_BASE_URL}/detect/async"
    payload = {
        "job_id": JOB_ID,
        "polygon": POLYGON_GEOJSON,
        "zoom": 18 # Kita bisa override parameter default
    }
    
    print(f"--- [LANGKAH 1] ---")
    print(f"Mengirimkan permintaan ke: {submit_url}")
    print(f"Payload: {json.dumps(payload, indent=2)}\n")
    
    try:
        response = requests.post(submit_url, json=payload, timeout=15)
        response.raise_for_status() # Akan error jika status code 4xx atau 5xx
        
        response_data = response.json()
        print("✅ Berhasil mengirimkan pekerjaan!")
        print(f"   Job ID: {response_data.get('job_id')}")
        print(f"   Status: {response_data.get('status')}")
        print("-" * 20 + "\n")
        return response_data.get('job_id')
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error dari Service B: {e.response.status_code}")
        print(f"   Detail: {e.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Tidak dapat terhubung ke Service B. Pastikan Service B sudah berjalan.")
        print(f"   Error: {e}")
        
    return None

def poll_job_status(job_id):
    """
    Langkah 2: Memeriksa status pekerjaan secara berkala sampai selesai.
    """
    status_url = f"{SERVICE_B_BASE_URL}/job/{job_id}"
    
    print(f"--- [LANGKAH 2] ---")
    print(f"Memeriksa status pekerjaan di: {status_url}\n")
    
    while True:
        try:
            response = requests.get(status_url, timeout=10)
            response.raise_for_status()
            
            status_data = response.json()
            status = status_data.get('status')
            progress = status_data.get('progress', 0)
            stage = status_data.get('stage', 'N/A')
            
            print(f"Status saat ini: {status} | Progress: {progress}% | Tahap: {stage}")
            
            if status == "completed":
                print("\n✅ Pekerjaan selesai!")
                print("-" * 20 + "\n")
                return True
            elif status == "failed":
                print(f"\n❌ Pekerjaan gagal: {status_data.get('error_message')}")
                return False
            
            # Tunggu beberapa detik sebelum memeriksa lagi
            time.sleep(5)
            
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error saat memeriksa status: {e.response.status_code}")
            print(f"   Detail: {e.response.text}")
            return False
        except requests.exceptions.RequestException:
            print(f"❌ Koneksi ke Service B terputus saat memeriksa status.")
            return False

def get_job_result(job_id):
    """
    Langkah 3: Mengambil hasil akhir dari pekerjaan yang sudah selesai.
    """
    result_url = f"{SERVICE_B_BASE_URL}/job/{job_id}/result"
    
    print(f"--- [LANGKAH 3] ---")
    print(f"Mengambil hasil akhir dari: {result_url}\n")
    
    try:
        response = requests.get(result_url, timeout=10)
        response.raise_for_status()
        
        result_data = response.json()
        
        print("✅ Berhasil mendapatkan hasil akhir!")
        print(f"   Job ID: {result_data.get('job_id')}")
        print(f"   Total bangunan terdeteksi: {result_data.get('total_buildings')}")
        print(f"   Waktu eksekusi: {result_data.get('execution_time')} detik")
        
        # Tampilkan beberapa data bangunan pertama
        buildings = result_data.get('buildings', [])
        print("\nContoh data bangunan:")
        for building in buildings[:5]: # Tampilkan 5 bangunan pertama
            print(f"  - ID: {building['id']}, Longitude: {building['longitude']}, Latitude: {building['latitude']}")
            
        if len(buildings) > 5:
            print("  ...")

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error saat mengambil hasil: {e.response.status_code}")
        print(f"   Detail: {e.response.text}")
    except requests.exceptions.RequestException:
        print(f"❌ Koneksi ke Service B terputus saat mengambil hasil.")


if __name__ == "__main__":
    # --- Jalankan Alur Kerja Penuh ---
    
    # Pertama, jalankan Service B (API Anda) di terminal lain:
    # python main_app.py
    
    # Kemudian, jalankan skrip ini.
    
    submitted_job_id = submit_detection_job()
    
    if submitted_job_id:
        is_completed = poll_job_status(submitted_job_id)
        
        if is_completed:
            get_job_result(submitted_job_id) 