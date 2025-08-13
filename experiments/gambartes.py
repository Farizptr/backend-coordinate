import requests
import json
import os
from PIL import Image # Membutuhkan library Pillow: pip install Pillow

# --- Konfigurasi ---
API_KEY = "AIzaSyC7o5JGJ-n2nWmJeBuoqFK1OKbQG0E6X6Y"  # Ganti dengan API key Google Anda
INPUT_JSON = "output/buildings_simple.json"
OUTPUT_JSON = "streetview_metadata_results.json"
IMAGE_FOLDER = "buildings"  # Folder tempat gambar akan disimpan

# Ukuran gambar yang diinginkan (sesuai kebutuhan model Anda)
TARGET_WIDTH = 600
TARGET_HEIGHT = 400

# --- Persiapan Direktori ---
def setup_directories():
    """Memastikan folder output dan gambar ada."""
    if not os.path.exists("output"):
        os.makedirs("output")
        print("Folder 'output' dibuat.")
    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)
        print(f"Folder '{IMAGE_FOLDER}' dibuat.")

# --- Dummy Data untuk Pengujian ---
def create_dummy_data(input_file_path):
    """Membuat dummy data JSON untuk pengujian awal."""
    dummy_data = [
      {"id": "building_001", "latitude": -6.917464, "longitude": 107.619122}, # Bandung, dekat ITB
      {"id": "building_002", "latitude": -6.890632, "longitude": 107.610500}, # Bandung, dekat PVJ
      {"id": "building_003", "latitude": -6.903494, "longitude": 107.643328}, # Bandung, dekat Gedung Sate
      {"id": "building_004", "latitude": 40.712776, "longitude": -74.005974}, # New York City (seharusnya ada Street View)
      {"id": "building_005", "latitude": 0.000000, "longitude": 0.000000}    # Samudra (kemungkinan besar tidak ada Street View)
    ]
    with open(input_file_path, "w") as f:
        json.dump(dummy_data, f, indent=2)
    print(f"Dummy data disimpan ke '{input_file_path}' untuk pengujian.")

# --- Fungsi Pengecekan Metadata ---
def check_streetview_metadata(lat, lng):
    """
    Memeriksa ketersediaan metadata Street View untuk koordinat tertentu.
    Pemanggilan API ini tidak dikenakan biaya.
    """
    url = f"https://maps.googleapis.com/maps/api/streetview/metadata?location={lat},{lng}&key={API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data.get("status", "ERROR")

# --- Fungsi Pengunduhan dan Pengubahan Ukuran Gambar ---
def download_and_resize_streetview_image(lat, lng, image_id, folder=IMAGE_FOLDER, target_width=TARGET_WIDTH, target_height=TARGET_HEIGHT):
    """
    Mengunduh gambar Street View dan mengubah ukurannya sesuai target.
    Akan dikenakan biaya per unduhan gambar.
    """
    # Ukuran awal yang lebih besar untuk menjaga kualitas saat di-resize
    initial_size = "640x640" 
    # Sesuaikan fov, heading, pitch untuk sudut pandang yang berbeda jika diperlukan
    url = f"https://maps.googleapis.com/maps/api/streetview?size={initial_size}&location={lat},{lng}&fov=90&heading=235&pitch=10&key={API_KEY}"
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status() # Akan memunculkan HTTPError untuk status kode 4xx/5xx

        # Simpan sementara gambar asli yang diunduh
        initial_filename = os.path.join(folder, f"temp_{image_id}.jpg")
        with open(initial_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        # print(f"   ✔ Gambar awal diunduh: {initial_filename} ({initial_size})")

        # Buka, ubah ukuran, konversi ke RGB, dan simpan gambar akhir
        final_filename = os.path.join(folder, f"streetview_{image_id}.jpg")
        img = Image.open(initial_filename)
        img = img.resize((target_width, target_height))
        
        # Pastikan gambar dalam mode RGB (3 channel)
        if img.mode != "RGB":
            img = img.convert("RGB")
            
        img.save(final_filename)
        os.remove(initial_filename) # Hapus file sementara
        print(f"   🎨 Gambar diubah ukuran dan disimpan: {final_filename} ({target_width}x{target_height}, {img.mode})")
        return final_filename
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Gagal mengunduh gambar untuk ID {image_id}: {e}")
        return None
    except Exception as e:
        # Menangkap error lain seperti masalah Pillow jika file bukan gambar valid atau disk penuh
        print(f"   ❌ Gagal memproses gambar untuk ID {image_id}: {e}")
        return None

# --- Main Program ---
def main():
    setup_directories()
    create_dummy_data(INPUT_JSON) # Hapus atau komen baris ini jika Anda ingin menggunakan file JSON asli

    # Baca koordinat dari JSON
    try:
        with open(INPUT_JSON, "r") as f:
            coords = json.load(f)
    except FileNotFoundError:
        print(f"Error: File input JSON '{INPUT_JSON}' tidak ditemukan. Pastikan sudah ada atau gunakan dummy data.")
        return
    except json.JSONDecodeError:
        print(f"Error: Gagal membaca file JSON '{INPUT_JSON}'. Pastikan formatnya benar.")
        return

    # Proses & simpan hasil ke JSON
    results = [] 

    for item in coords:
        lat = item.get("latitude")
        lng = item.get("longitude")
        coord_id = item.get("id")

        if lat is None or lng is None or coord_id is None:
            print(f"⚠️ Melewatkan item dengan data tidak lengkap: {item}")
            continue
        
        image_filename = None # Akan diisi dengan nama file jika gambar diunduh

        print(f"\n🔍 Mengecek ID {coord_id}: ({lat}, {lng})")
        status = check_streetview_metadata(lat, lng)
        print(f"   ➜ Status Metadata: {status}")

        if status == "OK":
            print(f"   ⬇️ Mengunduh dan mengubah ukuran gambar untuk ID {coord_id} menjadi {TARGET_WIDTH}x{TARGET_HEIGHT}...")
            image_filename = download_and_resize_streetview_image(lat, lng, coord_id)
        else:
            print(f"   ⚠️ Gambar Street View tidak tersedia untuk ID {coord_id}.")

        # Tambahkan semua informasi ke list results
        results.append({
            "id": coord_id,
            "latitude": lat,
            "longitude": lng,
            "status": status,
            "image_file": image_filename # Akan berisi nama file atau None
        })

    # Tulis semua hasil ke file JSON akhir
    with open(OUTPUT_JSON, mode="w", encoding="utf-8") as f:
        json.dump(results, f, indent=4) # Gunakan indent=4 untuk format yang rapi

    print(f"\n✅ Proses selesai. Hasil metadata disimpan di '{OUTPUT_JSON}' dan gambar (ukuran {TARGET_WIDTH}x{TARGET_HEIGHT}) di folder '{IMAGE_FOLDER}'.")

if __name__ == "__main__":
    main()