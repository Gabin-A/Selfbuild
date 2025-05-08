import streamlit as st
import requests
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium

# App title
st.title("🏙️ Nearby Amenities Finder")

# User input: address or ZIP
address = st.text_input("Enter your address or ZIP code", "St. Gallen, Switzerland")

# Amenity options and Overpass tag type
amenity_config = {
    "supermarket": "shop",
    "school": "amenity",
    "hospital": "amenity",
    "pharmacy": "amenity",
    "restaurant": "amenity"
}
amenity_options = list(amenity_config.keys())
selected_amenities = st.multiselect("Select amenities", amenity_options, default=["supermarket"])

# Search radius
radius = st.slider("Search radius (meters)", 500, 20000, 3000)

# When search is triggered
if st.button("Search"):
    geolocator = Nominatim(user_agent="streamlit_app")
    location = geolocator.geocode(address)

    if not location:
        st.error("📍 Location not found. Try a more specific address.")
    else:
        lat, lon = location.latitude, location.longitude
        st.success(f"📍 Found location: {location.address} ({lat:.5f}, {lon:.5f})")

        # Setup map
        folium_map = folium.Map(location=[lat, lon], zoom_start=14)
        folium.Marker([lat, lon], tooltip="Your Location", icon=folium.Icon(color='blue')).add_to(folium_map)

        found_any = False

        for amenity in selected_amenities:
            tag_type = amenity_config[amenity]
            query = f"""
            [out:json];
            (
              node["{tag_type}"="{amenity}"](around:{radius},{lat},{lon});
              way["{tag_type}"="{amenity}"](around:{radius},{lat},{lon});
              relation["{tag_type}"="{amenity}"](around:{radius},{lat},{lon});
            );
            out center;
            """
            try:
                response = requests.post("https://overpass-api.de/api/interpreter", data=query, timeout=30)
                response.raise_for_status()
                data = response.json()

                results = []
                for el in data.get("elements", []):
                    el_lat = el.get("lat") or el.get("center", {}).get("lat")
                    el_lon = el.get("lon") or el.get("center", {}).get("lon")
                    if el_lat and el_lon:
                        dist = geodesic((lat, lon), (el_lat, el_lon)).meters
                        name = el.get("tags", {}).get("name", f"{amenity.title()} (Unnamed)")
                        results.append((name, dist, el_lat, el_lon))

                if results:
                    found_any = True
                    top = sorted(results, key=lambda x: x[1])[:3]
                    for name, dist, el_lat, el_lon in top:
                        folium.Marker(
                            [el_lat, el_lon],
                            tooltip=f"{name} — {dist:.0f} m",
                            icon=folium.Icon(color="green", icon="info-sign")
                        ).add_to(folium_map)
                else:
                    st.info(f"❌ No nearby '{amenity}' found.")
            except Exception as e:
                st.warning(f"⚠️ Could not fetch {amenity}: {e}")

        if found_any:
            st.subheader("🗺️ Map of Nearest Amenities")
            st_data = st_folium(folium_map, width=700, height=500)
        else:
            st.warning("No amenities were found to show on the map.")



