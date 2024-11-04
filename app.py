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
import json, re

# Google Text-to-Speech if you want more sophisticated TTS
# from google.cloud import texttospeech

# App Layout
st.title("Dynamic Route Generation App")

# User Input for Start and End Locations
start_location = st.text_input("Enter Start Location:")
end_location = st.text_input("Enter End Location:")

if 'route_map' not in st.session_state:
    st.session_state['route_map'] = None
if 'route_coordinates' not in st.session_state:
    st.session_state['route_coordinates'] = None
if 'pois' not in st.session_state:
    st.session_state['pois'] = None
if 'start_coords' not in st.session_state:
    st.session_state['start_coords'] = None
if 'end_coords' not in st.session_state:
    st.session_state['end_coords'] = None

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
        with open('route.txt', 'w') as file:
            str = json.dumps(response.json(), indent=4)
            file.write(str)
        
        route = response.json()
        return route['features'][0]['geometry']['coordinates']
    except Exception as e:
        st.error(f"Error with route generation: {e}")
        return None

# Render Map Function
def render_map(start_coords, end_coords, route=None, current_location=None):
    # Create the map centered between the start and end coordinates
    if start_coords is None or end_coords is None:
        st.error("Start or end coordinates are not defined.")
        return None
    
    route_map = folium.Map(location=[(start_coords[0] + end_coords[0]) / 2, (start_coords[1] + end_coords[1]) / 2], zoom_start=13)

    # Add start and end markers
    folium.Marker(start_coords, tooltip='Start Location', icon=folium.Icon(color='green')).add_to(route_map)
    folium.Marker(end_coords, tooltip='End Location', icon=folium.Icon(color='red')).add_to(route_map)

    # Add the route polyline
    # Add the route polyline if available
    if route:
        route_coordinates = [(point[1], point[0]) for point in route]
        folium.PolyLine(route_coordinates, color="blue", weight=2.5, opacity=1).add_to(route_map)

    if current_location:
        folium.Marker([current_location[1], current_location[0]], tooltip="Current Position", icon=folium.Icon(color='orange')).add_to(route_map)

    return route_map


# Extract POIs from Text
def extract_pois_from_text(pois_text):
    poi_list = []
    pattern = r'\d+\.\s*(\*\*)?\[\s*([\d\.\-]+),\s*([\d\.\-]+)\s*\](\*\*)?\s*(.*?)(?=\n\d+\.|\Z)'

    # Find all matches in the text
    matches = re.findall(pattern, pois_text, re.DOTALL)
    for i, match in matches:
        latitude = match[1]
        longitude = match[2]
        description = match[4].strip()
        poi_list.append({
            'latitude': latitude,
            'longitude': longitude,
            'description': description
        })
    return poi_list

# Get POIs Along Route Using LLM
def get_pois_along_route(route_coordinates):
    chat_model = ChatGoogleGenerativeAI(model='gemini-1.5-pro', google_api_key=st.secrets.get("gemini_key"), temperature=0.8)
    try:
        # Create a prompt to generate POIs
        prompt = f"""
        You are an AI tour guide, that takes as input a route: {route_coordinates}
        From the route, you will then create an interesting, charming, and funny narrative tour guide that:
        * Highlights significant historical, cultural, sporting, and political points of interest along the route using your knowledge of the area and includes recent news or developments relevant to each area.
        * Divides the guide into no more than 5 sections with the suggested content, as well as GPS coordinates where the section is relevant. When the user crosses these GPS coordinates, we will play the audio for the section.
        * Each section should be concise, fitting within the expected travel time, and incorporate local perspectives, anecdotes, and ongoing issues to enrich the listener's experience.
        * Each numbered section should conform to the following format:
            1. [GPS Coordinates] [Relevant Content] (e.g. [47.55378762303337, -122.29579514494682] Beacon Hill is known for its diversity, with a large Asian-American population, particularly Filipino, Vietnamese, and Chinese communities. One significant figure from the area is Bob Santos, known as “Uncle Bob,” who was a prominent Filipino-American civil rights leader. )
        """

        human_message = HumanMessage(content=prompt)
        response = chat_model([human_message])
        if response:
            with open('pois.txt', 'w') as file:
                file.write(response.content)
            
            pois = extract_pois_from_text(response.content)
            print(pois)
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
                # Save coordinates and route in session state
                st.session_state['start_coords'] = start_coords
                st.session_state['end_coords'] = end_coords
                st.session_state['route_coordinates'] = route

                # Render and save the map to session state
                st.session_state['route_map'] = render_map(start_coords, end_coords, route)

                # Generate POIs and add them to the map
                pois = get_pois_along_route(route)
                if pois:
                    st.session_state['pois'] = pois
                    add_pois_to_map(st.session_state['route_map'], pois)

# Update Map with Current Position if Slider is Used
if st.session_state['route_coordinates'] is not None:
    route_coordinates = st.session_state['route_coordinates']
    point_index = st.slider("Move along the route", 0, len(route_coordinates)-1, 0)
    current_location = route_coordinates[point_index]

    # Render and update the map with the current position marker
    st.session_state['route_map'] = render_map(st.session_state['start_coords'], st.session_state['end_coords'], route=route_coordinates, current_location=current_location)

# Display the updated map
if st.session_state['route_map'] is not None:
    st_folium(st.session_state['route_map'], width=725)

