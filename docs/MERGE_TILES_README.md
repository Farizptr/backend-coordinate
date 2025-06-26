# Merge Tiles Utility

## Overview
Utility untuk menggabungkan semua file JSON tiles menjadi satu file JSON dengan format sederhana: **id (increment dari 1), longitude, latitude**.

## Format Output
```json
[
  {"id": 1, "longitude": 106.82929687, "latitude": -6.13320312},
  {"id": 2, "longitude": 106.86835937, "latitude": -6.17226562},
  {"id": 3, "longitude": 107.04882812, "latitude": -6.15273437},
  ...
]
```

## Cara Penggunaan

### 1. Command Line Utility

#### Basic Usage
```bash
# Merge dari direktori tiles specific
python merge_tiles_utility.py polygon_detection_results/tiles

# Merge dengan output file custom
python merge_tiles_utility.py polygon_detection_results/tiles output.json

# Auto-detect tiles folder dengan @tiles shortcut
python merge_tiles_utility.py @tiles

# Auto-detect dengan output file custom
python merge_tiles_utility.py @tiles buildings_merged.json
```

#### @tiles Shortcut
Fitur `@tiles` akan otomatis mencari folder tiles di lokasi berikut:
- `./tiles`
- `./polygon_detection_results/tiles`
- `../polygon_detection_results/tiles`
- `./results/tiles`

### 2. Programmatic Usage

```python
from polygon_detection import merge_all_tiles_to_simple_json

# Merge tiles dari direktori
count = merge_all_tiles_to_simple_json("path/to/tiles", "output.json")
print(f"Merged {count} buildings")

# Auto-detect tiles folder dari parent directory
count = merge_all_tiles_to_simple_json("polygon_detection_results", "output.json")
```

## Fitur Utama

### ✅ ID Increment Sederhana
- ID dimulai dari 1 dan increment secara berurutan
- Tidak ada prefix tile atau format kompleks
- Format: 1, 2, 3, 4, ...

### ✅ Auto-Detection
- Otomatis detect folder `tiles/` dari parent directory
- Support multiple common directory structures
- Error handling untuk missing directories

### ✅ Data Validation
- Validasi format JSON input
- Verifikasi field longitude/latitude
- Error handling untuk file corrupt

### ✅ Progress Reporting
- Menampilkan jumlah tiles files yang ditemukan
- Progress loading dari setiap file
- Summary statistik hasil merge

## File Structure

### Input
```
polygon_detection_results/
├── tiles/
│   ├── tile_18_123456_789012_simple.json
│   ├── tile_18_123457_789012_simple.json
│   └── tile_18_123458_789012_simple.json
```

### Output
```
merged_buildings_simple.json (atau nama custom)
```

## Example Usage Flow

### 1. Setelah Detection Selesai
```bash
# Jalankan detection normal (menghasilkan tiles)
python polygon_detection.py polygon.geojson

# Merge semua tiles menjadi format sederhana
python merge_tiles_utility.py @tiles buildings_final.json
```

### 2. Working dengan Existing Tiles
```bash
# Jika sudah ada folder tiles
python merge_tiles_utility.py polygon_detection_results/tiles output.json
```

## Output Example

### Console Output
```
============================================================
TILES MERGER UTILITY
============================================================
Menggabungkan semua file JSON tiles menjadi satu file
Format output: [{"id": 1, "longitude": 106.123, "latitude": -6.456}, ...]
============================================================
📂 Input tiles directory: polygon_detection_results/tiles
📄 Output file: merged_buildings_simple.json

Merging tiles from: polygon_detection_results/tiles
Found 3 simple format tile files
  Loaded 2 buildings from tile_18_123456_789012_simple.json
  Loaded 3 buildings from tile_18_123457_789012_simple.json
  Loaded 1 buildings from tile_18_123458_789012_simple.json

✅ Successfully merged 6 buildings
📁 Output saved to: merged_buildings_simple.json
📊 Format: ID starts from 1, increments by 1

📋 Sample data (first 3 buildings):
  ID: 1, Lon: 106.82929687, Lat: -6.13320312
  ID: 2, Lon: 106.86835937, Lat: -6.17226562
  ID: 3, Lon: 107.04882812, Lat: -6.15273437

🎉 MERGE COMPLETED SUCCESSFULLY!
📊 Total buildings merged: 6
📁 Output file: merged_buildings_simple.json
📏 File size: 486 bytes (0.5 KB)
```

### JSON Output
```json
[
  {
    "id": 1,
    "longitude": 106.82929687,
    "latitude": -6.13320312
  },
  {
    "id": 2,
    "longitude": 106.86835937,
    "latitude": -6.17226562
  },
  {
    "id": 3,
    "longitude": 107.04882812,
    "latitude": -6.15273437
  }
]
```

## Error Handling

### Common Issues & Solutions

#### 1. Tiles Directory Not Found
```
❌ Error: Tiles directory not found: ./tiles

Tips:
- Pastikan path tiles directory benar
- Gunakan @tiles untuk auto-detect dari direktori umum
- Jalankan detection script terlebih dahulu untuk menghasilkan tiles
```

#### 2. No Simple Format Files
```
No simple format tile files found
```
**Solution**: Pastikan detection dijalankan dengan incremental saving enabled.

#### 3. Empty Output
```
❌ MERGE FAILED!
No buildings were found or merged.
```
**Solution**: Check file tiles simple format dan pastikan ada data buildings.

## Integration dengan Detection

### Otomatis dalam Detection Flow
Detection script otomatis akan memanggil merge function di akhir proses:

```python
# Di dalam detect_buildings_in_polygon()
buildings_incremental_simple_path = os.path.join(output_dir, "buildings_incremental_simple.json")
save_incremental_simple_format(output_dir, buildings_incremental_simple_path)
```

### Manual Merge
Untuk merge manual setelah detection:

```bash
python merge_tiles_utility.py @tiles final_buildings.json
```

## Benefits

1. **Format Sederhana**: Hanya id, longitude, latitude
2. **ID Konsisten**: Increment dari 1 tanpa prefix kompleks
3. **Easy Integration**: Compatible dengan sistem database/aplikasi lain
4. **File Size Kecil**: Format minimal tanpa metadata ekstra
5. **Fast Processing**: Merge cepat dari tiles individual 