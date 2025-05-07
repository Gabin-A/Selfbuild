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

# 2. Select one or more amenities
amenity_options = ["supermarket", "school", "hospital", "pharmacy", "restaurant"]
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
            query = f"""
            [out:json];
            node["amenity"="{amenity}"](around:{radius},{lat},{lon});
            out body;
            """
            url = "https://overpass-api.de/api/interpreter"
            response = requests.post(url, data=query)
            data = response.json()

            if "elements" in data and data["elements"]:
                results = []
                for node in data["elements"]:
                    nlat, nlon = node["lat"], node["lon"]
                    dist = geodesic((lat, lon), (nlat, nlon)).meters
                    name = node.get("tags", {}).get("name", f"{amenity.title()} (Unnamed)")
                    results.append((name, dist, nlat, nlon))

                # Show top 3
                top = sorted(results, key=lambda x: x[1])[:3]
                for name, dist, nlat, nlon in top:
                    folium.Marker(
                        [nlat, nlon],
                        tooltip=f"{name} — {dist:.0f} m",
                        icon=folium.Icon(color="green", icon="info-sign")
                    ).add_to(m)
            else:
                st.info(f"No {amenity}s found nearby.")

        st.subheader("🗺️ Map of Nearby Amenities")
        st_folium(m, width=700, height=500)

