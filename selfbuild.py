import streamlit as st
import requests
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium

# UI
st.title("🏙️ Find Nearby Amenities")
st.markdown("Enter your address or ZIP code to find nearby amenities.")

# 1. Address input
address = st.text_input("Enter your address or ZIP code", "St. Gallen, Switzerland")

# 2. Amenity options
# Use separate tags: 'shop' for supermarket, 'amenity' for others
amenity_config = {
    "supermarket": "shop",
    "school": "amenity",
    "hospital": "amenity",
    "pharmacy": "amenity",
    "restaurant": "amenity"
}

amenity_options = list(amenity_config.keys())
selected_amenities = st.multiselect("Select amenities", amenity_options, default=["supermarket"])

# 3. Radius slider
radius = st.slider("Search radius (meters)", 500, 20000, 3000)

if st.button("Search"):
    # Geocode input
    geolocator = Nominatim(user_agent="streamlit_app")
    location = geolocator.geocode(address)

    if location is None:
        st.error("📍 Location not found. Try a more specific address.")
    else:
        lat, lon = location.latitude, location.longitude
        st.success(f"📍 Found: {location.address}")

        # Map setup
        m = folium.Map(location=[lat, lon], zoom_start=13)
        folium.Marker([lat, lon], tooltip="Your Location", icon=folium.Icon(color='blue')).add_to(m)

        for amenity in selected_amenities:
            tag_type = amenity_config[amenity]

            # Overpass query including nodes, ways, relations
            query = f"""
            [out:json];
            (
              node["{tag_type}"="{amenity}"](around:{radius},{lat},{lon});
              way["{tag_type}"="{amenity}"](around:{radius},{lat},{lon});
              relation["{tag_type}"="{amenity}"](around:{radius},{lat},{lon});
            );
            out center;
            """

            url = "https://overpass-api.de/api/interpreter"
            response = requests.post(url, data=query)
            data = response.json()

            if "elements" in data and data["elements"]:
                results = []
                for el in data["elements"]:
                    # Use center if it's a way or relation
                    el_lat = el.get("lat") or el.get("center", {}).get("lat")
                    el_lon = el.get("lon") or el.get("center", {}).get("lon")
                    if el_lat and el_lon:
                        dist = geodesic((lat, lon), (el_lat, el_lon)).meters
                        name = el.get("tags", {}).get("name", f"{amenity.title()} (Unnamed)")
                        results.append((name, dist, el_lat, el_lon))

                # Show top 3
                top = sorted(results, key=lambda x: x[1])[:3]
                for name, dist, el_lat, el_lon in top:
                    folium.Marker(
                        [el_lat, el_lon],
                        tooltip=f"{name} — {dist:.0f} m",
                        icon=folium.Icon(color="green", icon="info-sign")
                    ).add_to(m)
            else:
                st.info(f"No {amenity}s found nearby.")

        st.subheader("🗺️ Map of Nearby Amenities")
        st_data = st_folium(m, width=700, height=500)


