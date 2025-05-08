import streamlit as st
import requests
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium

st.title("🏙️ Nearby Amenities Finder")

# User inputs
address = st.text_input("Enter your address or ZIP code", "St. Gallen, Switzerland")
amenity_config = {
    "supermarket": "shop",
    "school": "amenity",
    "hospital": "amenity",
    "pharmacy": "amenity",
    "restaurant": "amenity"
}
amenity_options = list(amenity_config.keys())
selected_amenities = st.multiselect("Select amenities", amenity_options, default=["supermarket"])
radius = st.slider("Search radius (meters)", 500, 20000, 3000)

# Initialize session state
if "search_triggered" not in st.session_state:
    st.session_state["search_triggered"] = False
if "map" not in st.session_state:
    st.session_state["map"] = None

# Button to trigger search
if st.button("Search"):
    geolocator = Nominatim(user_agent="streamlit_app")
    location = geolocator.geocode(address)
    
    if not location:
        st.error("📍 Location not found.")
        st.session_state["search_triggered"] = False
    else:
        lat, lon = location.latitude, location.longitude
        st.success(f"📍 Found: {location.address} ({lat:.5f}, {lon:.5f})")

        # Create map
        folium_map = folium.Map(location=[lat, lon], zoom_start=14)
        folium.Marker([lat, lon], tooltip="Your Location", icon=folium.Icon(color='blue')).add_to(folium_map)

        # Process each amenity
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
                data = response.json()
                results = []

                for el in data.get("elements", []):
                    el_lat = el.get("lat") or el.get("center", {}).get("lat")
                    el_lon = el.get("lon") or el.get("center", {}).get("lon")
                    if el_lat and el_lon:
                        dist = geodesic((lat, lon), (el_lat, el_lon)).meters
                        name = el.get("tags", {}).get("name", f"{amenity.title()} (Unnamed)")
                        results.append((name, dist, el_lat, el_lon))

                for name, dist, el_lat, el_lon in sorted(results, key=lambda x: x[1])[:3]:
                    folium.Marker(
                        [el_lat, el_lon],
                        tooltip=f"{name} — {dist:.0f} m",
                        icon=folium.Icon(color="green", icon="info-sign")
                    ).add_to(folium_map)

            except Exception as e:
                st.warning(f"Could not load {amenity}: {e}")

        # Store map in session_state so it persists
        st.session_state["map"] = folium_map
        st.session_state["search_triggered"] = True

# Display map from session state
if st.session_state["search_triggered"] and st.session_state["map"]:
    st.subheader("🗺️ Map of Nearby Amenities")
    st_folium(st.session_state["map"], width=700, height=500)




