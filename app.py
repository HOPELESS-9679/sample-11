import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from geopy.distance import geodesic
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import requests

# Set page config
st.set_page_config(
    page_title="Nursery Locator - Khariar",
    page_icon="🌿",
    layout="wide"
)

# Load data from GitHub
@st.cache_data
def load_data():
    try:
        # Replace with your raw Excel file URL on GitHub
        excel_url = "https://github.com/your-username/nursery-locator/raw/main/NURSARY.xlsx"
        data = pd.read_excel(excel_url)
        
        # Ensure required columns exist
        required_columns = ['Name', 'Longitude', 'Latitude', 'Capacity', 'PlantsAvailable', 'Contact']
        for col in required_columns:
            if col not in data.columns:
                data[col] = 'N/A'
        return data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

@st.cache_data
def load_khariar_boundary():
    try:
        # Replace with your raw GeoJSON URL on GitHub
        geo_json_url = "https://github.com/your-username/nursery-locator/raw/main/khariar_boundary.geojson"
        response = requests.get(geo_json_url)
        return response.json()
    except:
        st.warning("Could not load Khariar boundary")
        return {"type": "FeatureCollection", "features": []}

def create_map(data, boundary_data, user_location=None):
    m = folium.Map(location=[20.1, 82.5], zoom_start=11)
    
    # Add boundary
    if boundary_data['features']:
        folium.GeoJson(
            boundary_data,
            name='Khariar Boundary',
            style_function=lambda x: {
                'color': 'yellow',
                'weight': 3,
                'fillOpacity': 0.1
            }
        ).add_to(m)
    
    # Add nurseries
    marker_cluster = MarkerCluster().add_to(m)
    for _, row in data.iterrows():
        folium.Marker(
            [row['Latitude'], row['Longitude']],
            popup=f"""
            <b>{row['Name']}</b><br>
            Plants: {row['PlantsAvailable']}<br>
            Contact: {row['Contact']}
            """,
            icon=folium.Icon(icon='leaf', prefix='fa', color='green')
        ).add_to(marker_cluster)
    
    # Add user location if provided
    if user_location:
        folium.Marker(
            user_location,
            icon=folium.Icon(color='blue', icon='user', prefix='fa'),
            tooltip="Your Location"
        ).add_to(m)
        
        # Find nearest nursery
        nearest = min(
            [(row['Latitude'], row['Longitude']) for _, row in data.iterrows()],
            key=lambda loc: geodesic(user_location, loc).km
        )
        folium.PolyLine(
            [user_location, nearest],
            color='red',
            weight=2
        ).add_to(m)
        m.fit_bounds([user_location, nearest])
    
    return m

def main():
    st.title("🌿 Khariar Nursery Locator")
    
    data = load_data()
    boundary = load_khariar_boundary()
    
    if data is not None:
        st.sidebar.header("Options")
        
        # Location input
        address = st.sidebar.text_input("Enter your location in Khariar:")
        user_loc = None
        if address:
            try:
                geolocator = Nominatim(user_agent="khariar_app")
                location = geolocator.geocode(f"{address}, Khariar, India")
                if location:
                    user_loc = (location.latitude, location.longitude)
            except:
                st.sidebar.error("Geocoding service unavailable")
        
        # Create and show map
        m = create_map(data, boundary, user_loc)
        st_folium(m, width=1200, height=700)
        
        # Show data
        if st.sidebar.checkbox("Show raw data"):
            st.dataframe(data)

if __name__ == "__main__":
    main()