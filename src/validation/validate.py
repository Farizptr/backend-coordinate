import folium
import json

# Load simple buildings list: [{"id": str, "longitude": float, "latitude": float}, ...]
with open('output/buildings_simple.json', 'r') as f:
	buildings = json.load(f)

# Guard: ensure list format
if not isinstance(buildings, list) or len(buildings) == 0:
	print('No buildings found in output/buildings_simple.json')
	raise SystemExit(0)

# Compute map center (average of lat/lon)
avg_lat = sum(b["latitude"] for b in buildings) / len(buildings)
avg_lon = sum(b["longitude"] for b in buildings) / len(buildings)

m = folium.Map(location=[avg_lat, avg_lon], zoom_start=18, tiles='OpenStreetMap')

# Plot points
for b in buildings:
	b_id = str(b.get("id", ""))
	lon = float(b["longitude"])
	lat = float(b["latitude"])
	popup_html = f"ID: {b_id}<br>Lon: {lon}<br>Lat: {lat}"
	folium.CircleMarker(
		location=[lat, lon],
		radius=3,
		color='red',
		fill=True,
		fill_opacity=0.7,
		popup=folium.Popup(popup_html, max_width=300)
	).add_to(m)

# Save the map
m.save('building_validation_map.html')
print(f"Map saved to building_validation_map.html with {len(buildings)} building points")
print("- Red dots: Building centroids (points from buildings_simple.json)")