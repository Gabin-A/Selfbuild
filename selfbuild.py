import streamlit as st
import requests
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium
import streamlit.components.v1 as components

st.set_page_config(page_title="Nearby Amenities Finder", layout="centered")
st.title("🏙️ Nearby Amenities Finder")

# ---- Session state init ----
if "map_html" not in st.session_state:
    st.session_state.map_html = None

# ---- User inputs ----
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

# ---- Run search on button click ----
if st.button("Search"):
    geolocator = Nominatim(user_agent="streamlit_app")
    location = geolocator.geocode(address)

    if not location:
        st.error("📍 Location not found.")
        st.session_state.map_html = None
    else:
        lat, lon = location.latitude, location.longitude
        st.success(f"📍 Found: {location.address} ({lat:.5f}, {lon:.5f})")

        folium_map = folium.Map(location=[lat, lon], zoom_start=14)
        folium.Marker([lat, lon], tooltip="Your Location", icon=folium.Icon(color='blue')).add_to(folium_map)

        try:
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
                response = requests.post("https://overpass-api.de/api/interpreter", data=query, timeout=30)
                data = response.json()
                elements = data.get("elements", [])

                results = []
                for el in elements:
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
                        icon=folium.Icon(color="green")
                    ).add_to(folium_map)

            # Save map as HTML string
            st.session_state.map_html = folium_map._repr_html_()

        except Exception as e:
            st.error(f"❌ Error during Overpass request: {e}")
            st.session_state.map_html = None

# ---- Display map safely with no reruns ----
if st.session_state.map_html:
    st.subheader("🗺️ Map of Nearest Amenities")
    components.html(st.session_state.map_html, height=500)











