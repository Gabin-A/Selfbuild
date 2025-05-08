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

# ---- Improved Address Input ----
st.header("📍 Enter Your Address")
col1, col2 = st.columns([2, 1])
street = col1.text_input("Street", "Rosenbergstrasse")
house_number = col2.text_input("House Number", "51")
zip_code = st.text_input("ZIP Code", "9000")
city = st.text_input("City", "St. Gallen")

#selection of a precise location

st.header("📌 Add a Location to Compare Distance")
compare_street = st.text_input("Compare Street", "")
compare_house_number = st.text_input("Compare House Number", "")
compare_zip_code = st.text_input("Compare ZIP Code", "")
compare_city = st.text_input("Compare City", "")


# ---- Amenity Selection with Buttons ----
st.header("🏪 Select Amenities")
amenity_config = {
    "Supermarket": "shop",
    "School": "amenity",
    "Hospital": "amenity",
    "Pharmacy": "amenity",
    "Restaurant": "amenity"
}
selected_amenities = []

cols = st.columns(len(amenity_config))
for i, label in enumerate(amenity_config.keys()):
    if cols[i].checkbox(label, key=f"btn_{label}"):
        selected_amenities.append(label.lower())

# ---- Radius Selection ----
radius = st.slider("Search radius (meters)", 500, 20000, 3000)

# ---- Run search on button click ----
if st.button("🔍 Search Nearby"):
    full_address = f"{street} {house_number}, {zip_code} {city}"
    geolocator = Nominatim(user_agent="streamlit_app")
    location = geolocator.geocode(full_address)
    

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
                tag_type = amenity_config[amenity.capitalize()]
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

            st.session_state.map_html = folium_map._repr_html_()
        except Exception as e:
            st.error(f"❌ Error during Overpass request: {e}")
            st.session_state.map_html = None

            # Try to geocode comparison point
compare_lat, compare_lon = None, None
if compare_street and compare_zip_code and compare_city:
    compare_address = f"{compare_street} {compare_house_number}, {compare_zip_code} {compare_city}"
    compare_location = geolocator.geocode(compare_address)
    if compare_location:
        compare_lat = compare_location.latitude
        compare_lon = compare_location.longitude

# ---- Display map safely with no reruns ----
if st.session_state.map_html:
    st.subheader("🗺️ Map of Nearest Amenities")
    components.html(st.session_state.map_html, height=500)











