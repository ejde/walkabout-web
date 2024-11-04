# Walkabout - An AI Route Guide

## Overview
Walkabout is a dynamic route generation app designed to provide users with an enriched travel experience. It takes user-provided start and end locations and generates an optimal driving route. Along the way, Walkabout uses AI to highlight interesting points of interest (POIs) with engaging narratives, including historical, cultural, and other significant highlights. Users can even listen to audio descriptions of these POIs using Text-to-Speech (TTS) capabilities.

## Features
- **User Inputs**: Enter start and end GPS coordinates to generate the route.
- **Route Generation**: Uses the OpenRouteService API to generate driving routes between user-defined locations.
- **Points of Interest (POIs)**: Uses a generative AI model (Google Gemini) to provide insightful and entertaining descriptions of POIs along the route.
- **Interactive Map**: Visualize the entire route, start and end points, POIs, and current location in real-time on an interactive map using Folium.
- **Audio Guide**: Listen to POI descriptions via Google Text-to-Speech, which helps create an immersive tour experience.
- **Navigation Simulation**: Simulate navigation along the route using a slider, allowing users to explore the route interactively and hear relevant audio as they approach POIs.

## How to Run the App

### Prerequisites
To run Walkabout, you will need the following:
1. **Python 3.7+**
2. **Libraries**: Install the required Python packages by running:
    ```sh
    pip install streamlit folium geopy requests gtts langchain_google_genai
    ```
3. **API Keys**:
   - **OpenRouteService API Key**: Required to generate driving routes.
   - **Google API Key for Gemini**: Required to generate POIs along the route using the generative AI model.
   - Store the API keys in your Streamlit secrets for easy access:
     ```
     [secrets]
     openroutservice_key = "YOUR_OPENROUTESERVICE_API_KEY"
     gemini_key = "YOUR_GOOGLE_GEMINI_API_KEY"
     ```

### Running the App
1. Clone this repository.
2. Navigate to the project directory and run the following command:
    ```sh
    streamlit run walkabout_app.py
    ```
3. Open the provided URL in your browser to interact with Walkabout.

## How to Use the App
1. **Input Start and End Coordinates**: Enter latitude and longitude for the starting and ending points.
2. **Generate Route**: Click on "Generate Route" to calculate the route and discover POIs along the way.
3. **Visualize and Simulate Navigation**:
    - The generated map will display the route, start, end, and POIs.
    - Use the slider to simulate moving along the route. As you move closer to POIs, the corresponding audio will automatically play.

## Technology Stack
- **Frontend**: Built using Streamlit for quick prototyping and interactivity.
- **Mapping**: Uses Folium for map visualization and integrating geographic data.
- **Route Planning**: OpenRouteService API for generating the optimal route.
- **Generative AI**: Google Gemini API for generating detailed and insightful POI descriptions.
- **Text-to-Speech**: Google Text-to-Speech (gTTS) for creating audio guides of POI descriptions.

## Key Files
- **walkabout_app.py**: Main application file that contains all logic for route generation, POI identification, and map rendering.
- **route.txt**: Output of the route JSON data for debugging purposes.
- **pois.txt**: Output of the POIs text for debugging purposes.

## Known Issues
- **Accuracy of POIs**: The generated POIs are based on AI-generated content and may not always be factually accurate or up-to-date.
- **Limited Geocoding**: The app uses Nominatim for geocoding, which may have request limits or fail for certain locations.
- **Distance Threshold for Audio**: POI audio is played if the simulated current location is within a fixed distance. This threshold may need adjustments based on route length and density of POIs.

## Future Improvements
- **Enhanced POI Data**: Integrate additional data sources for more reliable and up-to-date POI information.
- **Multiple Transport Modes**: Allow users to select other transport options, such as cycling or walking routes.
- **Real-time Updates**: Add real-time movement and GPS tracking functionality.
- **Voice Navigation**: Enable continuous voice navigation to guide users through their journey in real-time.

## Contributing
Contributions are welcome! If you'd like to improve Walkabout, please submit a pull request or create an issue for discussion.

## License
This project is licensed under the MIT License.

## Acknowledgments
- **OpenRouteService** for providing routing capabilities.
- **Google Gemini** for enriching the experience with generative AI content.
- **gTTS** for providing an easy-to-use text-to-speech functionality.
- **Streamlit** for the fast and interactive user interface.
- **Folium** for integrating maps into the application seamlessly.

