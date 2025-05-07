import streamlit as st
import requests
from geopy.distance import geodesic

# --- 1. User selects input ---
st.title("🏙️ Find Nearby Amenities")

amenity = st.selectbox("Select amenity", ["supermarket", "school", "hospital"])
lat = st.number_input("Latitude", value=47.4239)
lon = st.number_input("Longitude", value=9.3748)
radius = st.slider("Search radius (meters)", 500, 20000, 3000)

if st.button("Search"):
    # --- 2. Build Overpass API query ---
    query = f"""
    [out:json];
    node["amenity"="{amenity}"](around:{radius},{lat},{lon});
    out body;
    """

    url = "https://overpass-api.de/api/interpreter"
    response = requests.post(url, data=query)
    data = response.json()

    if "elements" in data:
        results = []
        for node in data["elements"]:
            node_lat = node["lat"]
            node_lon = node["lon"]
            dist = geodesic((lat, lon), (node_lat, node_lon)).meters
            name = node.get("tags", {}).get("name", "Unnamed")
            results.append((name, dist, node_lat, node_lon))

        # Sort and display top 3
        results = sorted(results, key=lambda x: x[1])[:3]
        st.subheader("Top 3 Nearby Results")
        for name, dist, nlat, nlon in results:
            st.write(f"📍 {name} — {dist:.1f} meters away")
    else:
        st.warning("No amenities found.")
