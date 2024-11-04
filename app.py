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

st.title("Walkabout - An AI Route Guide")

# User Input for Start and End Locations as GPS coordinates
start_location = st.text_input("Enter Start Location (Lat, Long):")
end_location = st.text_input("Enter End Location (Lat, Long):")

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

def geocode_locations(start_location, end_location):
    geolocator = Nominatim(user_agent="streamlit-app")
    try:
        start = geolocator.geocode(start_location)
        end = geolocator.geocode(end_location)
        return (start.latitude, start.longitude), (end.latitude, end.longitude)
    except Exception as e:
        st.error(f"Error with geocoding: {e}")
        return None, None

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

def render_map(start_coords, end_coords, route=None, pois=None, current_location=None):
    if start_coords is None or end_coords is None:
        st.error("Start or end coordinates are not defined.")
        return None
    
    route_map = folium.Map(location=[(start_coords[0] + end_coords[0]) / 2, (start_coords[1] + end_coords[1]) / 2], zoom_start=13)

    folium.Marker(start_coords, tooltip='Start Location', icon=folium.Icon(color='green')).add_to(route_map)
    folium.Marker(end_coords, tooltip='End Location', icon=folium.Icon(color='red')).add_to(route_map)

    # Add the route polyline if available
    if route:
        route_coordinates = [(point[1], point[0]) for point in route]
        folium.PolyLine(route_coordinates, color="blue", weight=2.5, opacity=1).add_to(route_map)

    # Add POIs to the map if available
    if pois:
        for poi in pois:
            if poi['latitude'] is not None and poi['longitude'] is not None:
                folium.Marker([poi['latitude'], poi['longitude']], tooltip=poi['description'], icon=folium.Icon(color='blue')).add_to(route_map)
                # Add TTS link to play description
                audio_link = generate_tts(poi['description'])
                if audio_link:
                    poi['audio_link'] = audio_link

    if current_location:
        folium.Marker([current_location[1], current_location[0]], tooltip="Current Position", icon=folium.Icon(color='orange')).add_to(route_map)

    return route_map


def extract_pois_from_text(pois_text):
    poi_list = []
    pattern = r'\d+\.\s*\[\s*([\d\.\-]+),\s*([\d\.\-]+)\s*\]\s*(.*?)(?=\n\d+\.|\Z)'
    cleaned_text = pois_text.replace('**', '')

    matches = re.findall(pattern, cleaned_text, re.DOTALL)
    for match in matches:
        latitude = match[0]
        longitude = match[1]
        description = match[2].strip()
        poi_list.append({
            'latitude': latitude,
            'longitude': longitude,
            'description': description
        })
    return poi_list

def get_pois_along_route(route_coordinates):
    chat_model = ChatGoogleGenerativeAI(model='gemini-1.5-pro', google_api_key=st.secrets.get("gemini_key"), temperature=0.8)
    try:
        prompt = f"""
        You are an AI tour guide, that takes as input a route: {route_coordinates}
        From the route, you will then create an interesting, charming, and funny narrative tour guide that:
        * Highlights significant historical, cultural, sporting, and political points of interest along the route using your knowledge of the area and includes recent news or developments relevant to each area.
        * Avoids generic, touristy commentary.
        * Divides the guide into no more than 5 sections with the suggested content, as well as GPS coordinates where the section is relevant. When the user crosses these GPS coordinates, we will play the audio for the section.
        * Each section should be concise, fitting within the expected travel time, and incorporate local perspectives, anecdotes, and ongoing issues to enrich the listener's experience.
        * Each section should be spread throughout the route
        * Each numbered section should conform to the following format:
            1. [GPS Coordinates] [Relevant Content] (e.g. [47.55378762303337, -122.29579514494682] Beacon Hill is known for its diversity, with a large Asian-American population, particularly Filipino, Vietnamese, and Chinese communities. One significant figure from the area is Bob Santos, known as “Uncle Bob,” who was a prominent Filipino-American civil rights leader. )
        """

        human_message = HumanMessage(content=prompt)
        response = chat_model([human_message])
        if response:
            with open('pois.txt', 'w') as file:
                file.write(response.content)
            
            pois = extract_pois_from_text(response.content)
            return pois
        
        return None
    except Exception as e:
        st.error(f"Error fetching recommendations: {e}")
        return None

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

def simulate_navigation(route_coordinates, pois):
    point_index = st.slider("Move along the route and relevant audio and text will be displayed", 0, len(route_coordinates)-1, 0)
    current_location = route_coordinates[point_index]

    st.session_state['route_map'] = render_map(st.session_state['start_coords'], st.session_state['end_coords'], route=route_coordinates, pois=st.session_state['pois'], current_location=current_location)

    if pois:
        for poi in pois:
            poi_location = (float(poi['latitude']), float(poi['longitude']))
            distance = ((current_location[1] - poi_location[0])**2 + (current_location[0] - poi_location[1])**2)**0.5
            if distance < 0.01:  # Play audio if within a threshold distance
                st.sidebar.write(poi['description'])
                if 'audio_link' in poi:
                    st.audio(poi['audio_link'], format="audio/mp3")
    

# Main App Logic
if st.button("Generate Route"):
    if start_location and end_location:
        start_coords, end_coords = geocode_locations(start_location, end_location)
        if start_coords and end_coords:
            route = get_route(start_coords, end_coords)
            if route:
                st.session_state['start_coords'] = start_coords
                st.session_state['end_coords'] = end_coords
                st.session_state['route_coordinates'] = route

                pois = get_pois_along_route(route)
                if pois:
                    st.session_state['pois'] = pois
                
                st.session_state['route_map'] = render_map(start_coords, end_coords, route, pois=st.session_state['pois'])

if st.session_state['route_coordinates'] is not None:
    route_coordinates = st.session_state['route_coordinates']
    simulate_navigation(route_coordinates, st.session_state['pois'])

if st.session_state['route_map'] is not None:
    st_folium(st.session_state['route_map'], width=725)

