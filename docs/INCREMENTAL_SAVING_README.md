# Incremental Saving Feature

## Overview
Fitur incremental saving memungkinkan program untuk menyimpan hasil deteksi koordinat bangunan per tile secara real-time, sehingga menghindari kehilangan data jika program mengalami error di tengah proses.

## Fitur Utama

### 1. Real-time Tile Saving
- Setiap tile yang selesai diproses langsung disimpan ke file JSON terpisah
- File disimpan di folder `output_dir/tiles/` dengan format `tile_z_x_y.json`
- Tidak perlu menunggu seluruh proses selesai

### 2. Resume Functionality
- Program dapat melanjutkan dari tile yang sudah diproses sebelumnya
- Otomatis mendeteksi tile yang sudah disimpan dan skip tile tersebut
- Parameter `resume_from_saved=True` (default) mengaktifkan fitur ini

### 3. Automatic Cleanup
- File-file tile individual otomatis dibersihkan setelah proses berhasil
- Hasil akhir tetap disimpan di file utama (`buildings.json`, dll.)

## Penggunaan

### Basic Usage
```python
from polygon_detection import detect_buildings_in_polygon
from detection import load_model

model = load_model("path/to/model.pt")
results = detect_buildings_in_polygon(
    model, 
    "polygon.geojson", 
    output_dir="results",
    resume_from_saved=True  # Enable resume functionality
)
```

### Manual Control
```python
# Disable resume (always start fresh)
results = detect_buildings_in_polygon(
    model, 
    "polygon.geojson", 
    resume_from_saved=False
)
```

## File Structure

```
output_dir/
├── tiles/                                    # Temporary tile files
│   ├── tile_18_123456_789012.json           # Individual tile results (detailed)
│   ├── tile_18_123456_789012_simple.json    # Individual tile results (simple format)
│   ├── tile_18_123457_789012.json
│   ├── tile_18_123457_789012_simple.json
│   └── ...
├── detection_results.json                   # Final merged results
├── buildings.json                           # Building data in GeoJSON format
├── buildings_simple.json                    # Simplified building coordinates (polygon filtered)
├── buildings_incremental_simple.json        # Simple format from incremental tiles
└── polygon_visualization.png                # Visualization
```

## Error Recovery

Jika program crash atau di-interrupt:

1. **Restart program** dengan parameter yang sama
2. Program akan otomatis:
   - Memuat tile yang sudah diproses
   - Skip tile yang sudah ada
   - Melanjutkan hanya tile yang belum selesai

## Benefits

1. **Data Safety**: Tidak kehilangan data jika program crash
2. **Time Efficiency**: Bisa resume tanpa mengulang dari awal
3. **Progress Monitoring**: Bisa melihat progress real-time dari file tile
4. **Memory Management**: File tile lebih kecil dan tidak menyimpan image data
5. **Detailed Merging Logs**: Progress tracking untuk setiap tahap merging dengan persentase

## Technical Details

### Tile File Formats

#### Detailed Format (for recovery)
```json
{
  "tile": "18/123456/789012",
  "bounds": [lon_min, lat_min, lon_max, lat_max],
  "detections": 3,
  "boxes": [[x1, y1, x2, y2], ...],
  "confidences": [0.85, 0.92, 0.78],
  "class_ids": [0, 0, 0],
  "processed_at": 1699123456.789
}
```

#### Simple Format (for output)
```json
[
  {
    "id": "18_123456_789012_0",
    "longitude": 106.82929687,
    "latitude": -6.13320312
  },
  {
    "id": "18_123456_789012_1", 
    "longitude": 106.86835937,
    "latitude": -6.17226562
  }
]
```

### Functions Added
- `save_tile_results()`: Save individual tile results (both detailed & simple formats)
- `convert_tile_to_simple_format()`: Convert tile detection to simple id,lon,lat format
- `load_saved_tile_results()`: Load previously saved tiles (detailed format for recovery)
- `load_all_simple_tile_results()`: Load all simple format tiles combined
- `save_incremental_simple_format()`: Save combined simple format results
- `cleanup_tile_files()`: Clean up temporary files

### Enhanced Features
- **Merging Progress Logging**: Detailed progress tracking untuk 4 tahap merging:
  - Step 1: Pre-computing polygon axes (dengan persentase)
  - Step 2: Finding potential connections (analisis comparison progress)
  - Step 3: Processing connections and merging (track merged count)
  - Step 4: Creating final merged buildings (building creation progress)

## Testing

Run the test script to validate functionality:
```bash
python test_incremental_saving.py
```

## Backward Compatibility

Fitur ini fully backward compatible:
- Existing code tetap berfungsi tanpa perubahan
- Default parameter `resume_from_saved=True` bisa diubah ke `False`
- Output files tetap sama seperti sebelumnya 