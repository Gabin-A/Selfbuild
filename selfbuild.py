import streamlit as st
import requests #will enable http request for the map api
#since we use a overpass turbo api, we can use https://geopy.readthedocs.io/en/stable/
from geopy.geocoders import Nominatim #Nominatim since we are using openstreetmap api
from geopy.distance import geodesic #we need geodesic to calculate the distance on the map we will deploy using the basic radius method
import folium #enable the creation of a map in separate html file
import streamlit.components.v1 as components #to be able to create a custom compenent, here our display map https://docs.streamlit.io/develop/concepts/custom-components/intro

#set page title using https://docs.streamlit.io/ examples
st.set_page_config(page_title='Local Amenities Finder', layout='centered')
st.title('Local Amenities :red[Finder]')

#storing follow up infos in the map
if "map_html" not in st.session_state:
    st.session_state.map_html = None

#adress input section using https://docs.streamlit.io/ examples
st.header('Enter Your Address')
col1, col2 = st.columns([2, 1])
street = col1.text_input('Street')
house_number = col2.text_input('House Number')
zip_code = st.text_input('ZIP Code')
city = st.text_input('City')

#Input section : Potential precise location customer want to measure distance to, again https://docs.streamlit.io/
st.header('Add a Target Location to Assess Distance')
compare_street = st.text_input('Target Street')
compare_house_number = st.text_input('Target House Number')
compare_zip_code = st.text_input('Target ZIP Code')
compare_city = st.text_input('Target City')

#Buttons to select critical amenities the customers want around his flat
st.header('Select Amenities')
#create a dictionnary and assign user friendly amenities
amenity_config = {
    "Supermarket": "shop",
    "School": "amenity",
    "Hospital": "amenity",
    "Pharmacy": "amenity",
    "Restaurant": "amenity"
}
selected_amenities = [] #create an empty list for user amenities

#selection section for customer to choose
cols = st.columns(len(amenity_config))
for i, label in enumerate(amenity_config.keys()):
    if cols[i].checkbox(label, key=f"btn_{label}"):
        selected_amenities.append(label.lower())

#set slider using streamlit features https://docs.streamlit.io/develop/api-reference/widgets/st.slider
radius = st.slider('Search Radius in meters', 0, 5000, 300)

#Search button using https://docs.streamlit.io/develop/api-reference/widgets/st.slider and assigning function
if st.button('Search Nearby'):
    geolocator = Nominatim(user_agent='streamlit_app') #creating geocoder from geopy https://geopy.readthedocs.io/en/stable/index.html?highlight=user_agent
    full_address = f"{street} {house_number}, {zip_code} {city}" #Combines the address components the user entered into one full string
    location = geolocator.geocode(full_address)

    if not location:
        st.error('Location not found')
        st.session_state.map_html = None #if adress not found, no map and error message
    else:
        lat, lon = location.latitude, location.longitude
        st.success(f'Found: {location.address} ({lat:.5f}, {lon:.5f})') #if found assign geoloc values and windows pop

        folium_map = folium.Map(location=[lat, lon], zoom_start=14)
        folium.Marker(
            [lat, lon],
            tooltip='Your Location',
            icon=folium.Icon(color='blue')
        ).add_to(folium_map) #add features found to the map

        #attempt to add amenities using try/except block to handle errors
        try:
            for amenity in selected_amenities: #for funtion iterates dictionnary established before
                tag_type = amenity_config[amenity.capitalize()] #we assigned categories in the dictionnary before to certain tags, it assigns to proper openstreemap cat.
                query = f""" #building the overpass query
                [out:json];
                (
                  node["{tag_type}"="{amenity}"](around:{radius},{lat},{lon});
                  way["{tag_type}"="{amenity}"](around:{radius},{lat},{lon});
                  relation["{tag_type}"="{amenity}"](around:{radius},{lat},{lon}); #building the query for overpass in json to then be used in openstreetmap
                );
                out center;
                """
                response = requests.post("https://overpass-api.de/api/interpreter", data=query, timeout=30) #sends the query to overpas api, max 30 sec waiting time
                data = response.json() #response in a dictionnary
                elements = data.get('elements', []) #exctracts nodes ways and relations returned by overpass
#processing data return by overpass
                results = [] #processing data return by overpass
                for el in elements:
                    el_lat = el.get('lat') or el.get('center', {}).get('lat')
                    el_lon = el.get('lon') or el.get('center', {}).get('lon') #nods have long and lat directly, ways or relations have center dictionary, hence or function
                    if el_lat and el_lon:
                        dist = geodesic((lat, lon), (el_lat, el_lon)).meters #calculating distance in straight line
                        name = el.get('tags', {}).get('name', f'{amenity.title()} (Unnamed)') #extracting name
                        results.append((name, dist, el_lat, el_lon)) #creating complete list

                for name, dist, el_lat, el_lon in sorted(results, key=lambda x: x[1])[:3]:
                    folium.Marker(
                        [el_lat, el_lon],
                        tooltip=f'{name} — {dist:.0f} m',
                        icon=folium.Icon(color='green')
                    ).add_to(folium_map)
        except Exception as e:
            st.error(f'Error during Overpass request: {e}')

        #comparaison point
        if compare_street and compare_zip_code and compare_city:
            compare_address = f'{compare_street} {compare_house_number}, {compare_zip_code} {compare_city}'
            compare_location = geolocator.geocode(compare_address)
            if compare_location:
                compare_lat = compare_location.latitude
                compare_lon = compare_location.longitude
                dist_to_compare = geodesic((lat, lon), (compare_lat, compare_lon)).meters

                #Add marker for comparison
                folium.Marker(
                    [compare_lat, compare_lon],
                    tooltip=f'Comparison Location — {dist_to_compare:.0f} m',
                    icon=folium.Icon(color='red', icon='info-sign')
                ).add_to(folium_map)

                #Add line between home and comparison
                folium.PolyLine(
                    locations=[(lat, lon), (compare_lat, compare_lon)],
                    color='red', weight=2.5, opacity=0.8,
                    tooltip=f'{dist_to_compare:.0f} m'
                ).add_to(folium_map)

                st.info(f'Distance to comparison location: **{dist_to_compare:.0f} meters**')

        #Render map
        st.session_state.map_html = folium_map._repr_html_()

#Display map
if st.session_state.map_html:
    st.subheader('Map of Nearest Amenities')
    components.html(st.session_state.map_html, height=500)











