# Import Necessary Libraries
import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import requests
from gtts import gTTS
from io import BytesIO
import base64
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage

# Google Text-to-Speech if you want more sophisticated TTS
# from google.cloud import texttospeech

# App Layout
st.title("Dynamic Route Generation App")

# User Input for Start and End Locations
start_location = st.text_input("Enter Start Location:")
end_location = st.text_input("Enter End Location:")

# Geocoding Function
def geocode_locations(start_location, end_location):
    geolocator = Nominatim(user_agent="streamlit-app")
    try:
        start = geolocator.geocode(start_location)
        end = geolocator.geocode(end_location)
        return (start.latitude, start.longitude), (end.latitude, end.longitude)
    except Exception as e:
        st.error(f"Error with geocoding: {e}")
        return None, None

# Generate Route Function
def get_route(start_coords, end_coords):
    try:
        api_key = st.secrets.get("openroutservice_key")
        url = f"https://api.openrouteservice.org/v2/directions/driving-car"
        headers = {
            'Authorization': api_key,
        }
        params = {
            'start': f"{start_coords[1]},{start_coords[0]}",
            'end': f"{end_coords[1]},{end_coords[0]}"
        }
        response = requests.get(url, headers=headers, params=params)
        route = response.json()
        return route['routes'][0]['geometry']['coordinates']
    except Exception as e:
        st.error(f"Error with route generation: {e}")
        return None

# Render Map Function
def render_map(route, start_coords, end_coords):
    # Create the map centered between the start and end coordinates
    route_map = folium.Map(location=[(start_coords[0] + end_coords[0]) / 2, (start_coords[1] + end_coords[1]) / 2], zoom_start=13)

    # Add start and end markers
    folium.Marker(start_coords, tooltip='Start Location', icon=folium.Icon(color='green')).add_to(route_map)
    folium.Marker(end_coords, tooltip='End Location', icon=folium.Icon(color='red')).add_to(route_map)

    # Add the route polyline
    route_coordinates = [(point[1], point[0]) for point in route]
    folium.PolyLine(route_coordinates, color="blue", weight=2.5, opacity=1).add_to(route_map)

    # Display the map using Streamlit
    st_folium(route_map, width=725)

# Get POIs Along Route Using LLM
def get_pois_along_route(route_coordinates):
    chat_model = ChatGoogleGenerativeAI(model='gemini-1.5-flash-8b', google_api_key=st.secrets.get("gemini_key"), temperature=0.8)
    try:
        # Create a prompt to generate POIs
        prompt = "Generate 5 interesting points of interest along a route that follows these coordinates: {}. Include landmarks, parks, and restaurants.".format(route_coordinates)

        human_message = HumanMessage(content=prompt)
        response = chat_model([human_message])
        if response:
            pois = response.choices[0].text.strip().split('\n')
            return pois
        
        return None
    except Exception as e:
        st.error(f"Error fetching recommendations: {e}")
        return None

# Text-to-Speech Function
def generate_tts(description):
    try:
        tts = gTTS(description)
        audio_data = BytesIO()
        tts.write_to_fp(audio_data)
        audio_data.seek(0)
        audio_base64 = base64.b64encode(audio_data.read()).decode('utf-8')
        return f"data:audio/mp3;base64,{audio_base64}"
    except Exception as e:
        st.error(f"Error with TTS: {e}")
        return None

# Add POIs to Map
def add_pois_to_map(route_map, pois):
    for poi in pois:
        folium.Marker(poi['location'], tooltip=poi['name'], icon=folium.Icon(color='blue')).add_to(route_map)
        # Add TTS link to play description
        audio_link = generate_tts(poi['description'])
        if audio_link:
            st.audio(audio_link, format="audio/mp3")

# Simulate Navigation Along Route
def simulate_navigation(route_coordinates):
    # Slider to simulate movement
    point_index = st.slider("Move along the route", 0, len(route_coordinates)-1, 0)
    current_location = route_coordinates[point_index]

    # Highlight current position
    current_map = folium.Map(location=[current_location[1], current_location[0]], zoom_start=13)
    folium.Marker([current_location[1], current_location[0]], tooltip="Current Position", icon=folium.Icon(color='orange')).add_to(current_map)
    
    # Re-render the map
    st_folium(current_map, width=725)

# Main App Logic
if st.button("Generate Route"):
    if start_location and end_location:
        # Call the function to geocode the locations and generate route
        start_coords, end_coords = geocode_locations(start_location, end_location)
        if start_coords and end_coords:
            route = get_route(start_coords, end_coords)
            if route:
                route_map = render_map(route, start_coords, end_coords)
                pois = get_pois_along_route(route)
                add_pois_to_map(route_map, pois)
                simulate_navigation(route)
else:
    st.warning("Please enter both start and end locations to generate a route.")
